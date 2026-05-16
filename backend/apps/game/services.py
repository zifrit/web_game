from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Character,
    CharacterClass,
    DungeonLocation,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunClaimItem,
    DungeonRunStatus,
    GameConfig,
    ItemTemplate,
    RarityConfig,
    RepairTransaction,
    UserItem,
)

STAT_KEYS = ("health", "attack", "defense", "critical_chance", "evasion")
EQUIPMENT_SLOTS = ("weapon", "helmet", "armor", "boots", "ring")
WEAPON_CLASS_BY_TYPE = {
    "sword": "warrior",
    "dagger": "assassin",
    "staff": "mage",
    "bow": "archer",
}


DEFAULT_CONFIGS: dict[str, dict[str, Any]] = {
    "power_formula_config": {
        "health": 0.25,
        "attack": 2.0,
        "defense": 1.7,
        "critical_chance": 1.0,
        "evasion": 1.0,
    },
    "success_chance_config": {"base": 75, "power_delta_multiplier": 1.5, "min": 35, "max": 100},
    "repair_cost_config": {"copper_per_durability": 10},
    "experience_curve_config": {"base": 100, "exponent": 1.5, "max_level": 20},
    "stat_caps": {"critical_chance": 60, "evasion": 50},
    "durability_loss_config": {"success": 1, "failure": 5},
}

DEFAULT_RARITIES = {
    "common": {"name": "Обычный", "stat_multiplier": 1.0, "min_item_level": 1, "max_item_level": 3, "min_stats_count": 1, "max_stats_count": 1},
    "uncommon": {"name": "Необычный", "stat_multiplier": 1.25, "min_item_level": 2, "max_item_level": 5, "min_stats_count": 1, "max_stats_count": 2},
    "rare": {"name": "Редкий", "stat_multiplier": 1.6, "min_item_level": 4, "max_item_level": 8, "min_stats_count": 2, "max_stats_count": 3},
    "epic": {"name": "Эпический", "stat_multiplier": 2.2, "min_item_level": 7, "max_item_level": 10, "min_stats_count": 3, "max_stats_count": 3},
}


class GameConfigService:
    @staticmethod
    def get_config(key: str) -> dict[str, Any]:
        value = DEFAULT_CONFIGS.get(key, {}).copy()
        db_config = GameConfig.objects.filter(key=key, is_active=True).first()
        if db_config and isinstance(db_config.value, dict):
            value.update(db_config.value)
        return value


class GameBalanceService:
    @staticmethod
    def create_character(user, name: str, character_class: CharacterClass) -> Character:
        character = Character.objects.create(
            user=user,
            name=name,
            character_class=character_class,
            base_health=character_class.start_health,
            base_attack=character_class.start_attack,
            base_defense=character_class.start_defense,
            base_critical_chance=character_class.start_critical_chance,
            base_evasion=character_class.start_evasion,
        )
        character.power_cached = GameFormulaService.character_stats(character)["power"]
        character.power_updated_at = timezone.now()
        character.save(update_fields=["power_cached", "power_updated_at", "updated_at"])
        return character

    @staticmethod
    def rarity_config(rarity: str) -> dict[str, Any]:
        db_config = RarityConfig.objects.filter(key=rarity, is_active=True).first()
        if db_config:
            return {
                "name": db_config.name,
                "stat_multiplier": db_config.stat_multiplier,
                "min_item_level": db_config.min_item_level,
                "max_item_level": db_config.max_item_level,
                "min_stats_count": db_config.min_stats_count,
                "max_stats_count": db_config.max_stats_count,
            }
        if rarity not in DEFAULT_RARITIES:
            raise serializers.ValidationError(f"Unknown rarity: {rarity}")
        return DEFAULT_RARITIES[rarity]


class GameFormulaService:
    @staticmethod
    def experience_required(level: int) -> int:
        config = GameConfigService.get_config("experience_curve_config")
        return math.ceil(float(config["base"]) * (level ** float(config["exponent"])))

    @staticmethod
    def level_growth_stats(character: Character) -> dict[str, float]:
        profile = character.character_class.growth_profile or {}
        levels_gained = max(character.level - 1, 0)
        stats = {
            "health": float(profile.get("health_per_level", 5)) * levels_gained,
            "attack": float(profile.get("attack_per_level", 1)) * levels_gained,
            "defense": float(profile.get("defense_per_level", 1)) * levels_gained,
            "critical_chance": 0.0,
            "evasion": 0.0,
        }
        every = int(profile.get("special_bonus_every", 5) or 0)
        if every > 0:
            special_count = character.level // every
            for key, value in (profile.get("special_growth") or {}).items():
                if key in stats:
                    stats[key] += float(value) * special_count
        return stats

    @classmethod
    def character_stats(cls, character: Character, include_equipment: bool = True) -> dict[str, float]:
        stats = {
            "health": float(character.base_health),
            "attack": float(character.base_attack),
            "defense": float(character.base_defense),
            "critical_chance": float(character.base_critical_chance),
            "evasion": float(character.base_evasion),
        }
        for key, value in cls.level_growth_stats(character).items():
            stats[key] += value
        if include_equipment:
            for item in character.equipped_items.all():
                if item.is_broken:
                    continue
                for key, value in (item.stats or {}).items():
                    if key in stats:
                        stats[key] += float(value)
        caps = GameConfigService.get_config("stat_caps")
        stats["critical_chance"] = min(stats["critical_chance"], float(caps.get("critical_chance", 60)))
        stats["evasion"] = min(stats["evasion"], float(caps.get("evasion", 50)))
        stats["power"] = cls.power_from_stats(stats)
        return {key: round(value, 2) for key, value in stats.items()}

    @staticmethod
    def power_from_stats(stats: dict[str, float]) -> float:
        config = GameConfigService.get_config("power_formula_config")
        return round(sum(float(stats.get(key, 0)) * float(config.get(key, 0)) for key in STAT_KEYS), 2)

    @staticmethod
    def success_chance(character_power: float, required_power: float) -> float:
        config = GameConfigService.get_config("success_chance_config")
        raw = float(config["base"]) + (character_power - required_power) * float(config["power_delta_multiplier"])
        return round(max(float(config["min"]), min(float(config["max"]), raw)), 2)

    @staticmethod
    def repair_cost(item: UserItem) -> int:
        missing = max(item.durability_max - item.durability_current, 0)
        config = GameConfigService.get_config("repair_cost_config")
        return int(missing * int(config.get("copper_per_durability", 10)))

    @staticmethod
    def durability_loss(is_success: bool) -> int:
        config = GameConfigService.get_config("durability_loss_config")
        return int(config["success" if is_success else "failure"])


class LootGenerationService:
    @staticmethod
    def _weighted_choice(chances: dict[str, float]) -> str:
        total = sum(float(value) for value in chances.values())
        roll = random.uniform(0, total)
        upto = 0.0
        for key, value in chances.items():
            upto += float(value)
            if roll <= upto:
                return key
        return next(reversed(chances))

    @classmethod
    def generate_item_reward(cls, character: Character, location: DungeonLocation) -> dict[str, Any] | None:
        if random.uniform(0, 100) > location.item_drop_chance:
            return None

        rarity = cls._weighted_choice(location.rarity_chances)
        rarity_config = GameBalanceService.rarity_config(rarity)
        templates = ItemTemplate.objects.filter(
            is_active=True,
            template_locations__location=location,
        )
        templates = [template for template in templates if item_allowed_for_character(template, character)]
        if not templates:
            return None

        template = random.choice(templates)
        item_level = random.randint(rarity_config["min_item_level"], rarity_config["max_item_level"])
        possible_stats = template.possible_stats or {}
        count = min(
            random.randint(rarity_config["min_stats_count"], rarity_config["max_stats_count"]),
            len(possible_stats),
        )
        selected_stats = random.sample(list(possible_stats.keys()), count) if count else []
        stats: dict[str, int] = {}
        for stat_key in selected_stats:
            stat_range = possible_stats[stat_key]
            base_value = random.uniform(float(stat_range["min"]), float(stat_range["max"]))
            value = base_value * rarity_config["stat_multiplier"] * (1 + item_level * 0.08)
            stats[stat_key] = max(1, int(round(value)))

        durability_max = random.randint(template.min_durability, template.max_durability)
        return {
            "template_id": template.id,
            "name": f"{rarity_config['name']} {template.name}",
            "slot": template.slot,
            "item_type": template.item_type,
            "rarity": rarity,
            "item_level": item_level,
            "stats": stats,
            "durability_current": durability_max,
            "durability_max": durability_max,
        }


def item_allowed_for_character(item: ItemTemplate | UserItem, character: Character) -> bool:
    item_type = item.item_type
    required_class = WEAPON_CLASS_BY_TYPE.get(item_type)
    if required_class and required_class != character.character_class_id:
        return False
    allowed_classes = getattr(item, "allowed_classes", None)
    if allowed_classes is None and hasattr(item, "template"):
        allowed_classes = item.template.allowed_classes
    return not allowed_classes or character.character_class_id in allowed_classes


@dataclass
class ClaimResult:
    run: DungeonRun
    claim: DungeonRunClaim
    items: list[UserItem]
    old_level: int
    new_level: int


class DungeonRunService:
    @staticmethod
    def _get_character(user) -> Character:
        try:
            return user.character
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError("User has no character.") from exc

    @classmethod
    @transaction.atomic
    def start_run(cls, user, location_id: int) -> DungeonRun:
        character = cls._get_character(user)
        character = Character.objects.select_for_update().select_related("character_class").get(pk=character.pk)
        if DungeonRun.objects.filter(character=character, status=DungeonRunStatus.IN_PROGRESS).exists():
            raise serializers.ValidationError("Character already has an active dungeon run.")
        if character.equipped_items.filter(durability_current=0).exists():
            raise serializers.ValidationError("Broken equipped items block starting a new dungeon run.")
        try:
            location = DungeonLocation.objects.get(pk=location_id, is_active=True)
        except DungeonLocation.DoesNotExist as exc:
            raise serializers.ValidationError("Dungeon location not found.") from exc

        power = GameFormulaService.character_stats(character)["power"]
        success_chance = GameFormulaService.success_chance(power, location.required_power)
        now = timezone.now()
        return DungeonRun.objects.create(
            character=character,
            location=location,
            status=DungeonRunStatus.IN_PROGRESS,
            started_at=now,
            ends_at=now + timezone.timedelta(seconds=location.duration_seconds),
            success_chance=success_chance,
        )

    @classmethod
    def finalize_due_run(cls, run: DungeonRun, now=None) -> DungeonRun:
        now = now or timezone.now()
        if run.status != DungeonRunStatus.IN_PROGRESS or run.ends_at > now:
            return run

        is_success = random.uniform(0, 100) <= run.success_chance
        location = run.location
        run.is_success = is_success
        run.completed_at = now
        run.status = DungeonRunStatus.SUCCESS_WAITING_CLAIM if is_success else DungeonRunStatus.FAILED_WAITING_CLAIM
        run.experience_reward = random.randint(location.experience_min, location.experience_max) if is_success else 0
        run.money_reward_copper = random.randint(location.money_min_copper, location.money_max_copper) if is_success else 0
        item_reward = LootGenerationService.generate_item_reward(run.character, location) if is_success else None
        run.items_reward = [item_reward] if item_reward else []
        run.durability_loss = GameFormulaService.durability_loss(is_success)
        run.save(
            update_fields=[
                "is_success",
                "completed_at",
                "status",
                "experience_reward",
                "money_reward_copper",
                "items_reward",
                "durability_loss",
                "updated_at",
            ]
        )
        return run

    @classmethod
    @transaction.atomic
    def claim_run(cls, user, run_id: int) -> ClaimResult:
        run = (
            DungeonRun.objects.select_for_update()
            .select_related("character", "character__user", "character__character_class", "location")
            .get(pk=run_id)
        )
        if run.character.user_id != user.id:
            raise serializers.ValidationError("Dungeon run does not belong to this user.")
        cls.finalize_due_run(run)

        existing_claim = getattr(run, "claim", None)
        if existing_claim:
            return ClaimResult(
                run=run,
                claim=existing_claim,
                items=[claim_item.user_item for claim_item in existing_claim.claim_items.select_related("user_item")],
                old_level=run.character.level,
                new_level=run.character.level,
            )

        if run.status not in (DungeonRunStatus.SUCCESS_WAITING_CLAIM, DungeonRunStatus.FAILED_WAITING_CLAIM):
            raise serializers.ValidationError("Dungeon run is not ready to claim.")

        user = type(user).objects.select_for_update().get(pk=user.pk)
        character = Character.objects.select_for_update().select_related("character_class").get(pk=run.character_id)
        old_level = character.level
        experience = run.experience_reward or 0
        character.experience += experience
        cls._apply_level_ups(character)
        user.money_copper += run.money_reward_copper or 0
        user.save(update_fields=["money_copper", "updated_at"])
        character.save(update_fields=["level", "experience", "updated_at"])

        claim = DungeonRunClaim.objects.create(
            dungeon_run=run,
            user=user,
            character=character,
            experience_claimed=experience,
            money_claimed_copper=run.money_reward_copper or 0,
        )

        created_items: list[UserItem] = []
        for draft in run.items_reward or []:
            item = UserItem.objects.create(
                owner_user=user,
                source_character=character,
                template_id=draft["template_id"],
                name=draft["name"],
                slot=draft["slot"],
                item_type=draft["item_type"],
                rarity=draft["rarity"],
                item_level=draft["item_level"],
                stats=draft.get("stats", {}),
                durability_current=draft["durability_current"],
                durability_max=draft["durability_max"],
            )
            DungeonRunClaimItem.objects.create(claim=claim, user_item=item)
            created_items.append(item)

        cls._apply_durability_loss(character, run.durability_loss or 0)
        run.status = DungeonRunStatus.CLAIMED
        run.save(update_fields=["status", "updated_at"])
        return ClaimResult(run=run, claim=claim, items=created_items, old_level=old_level, new_level=character.level)

    @staticmethod
    def _apply_level_ups(character: Character) -> None:
        config = GameConfigService.get_config("experience_curve_config")
        max_level = int(config.get("max_level", 20))
        while character.level < max_level:
            required = GameFormulaService.experience_required(character.level)
            if character.experience < required:
                break
            character.experience -= required
            character.level += 1

    @staticmethod
    def _apply_durability_loss(character: Character, loss: int) -> None:
        if loss <= 0:
            return
        for item in character.equipped_items.select_for_update():
            item.durability_current = max(0, item.durability_current - loss)
            item.save(update_fields=["durability_current", "updated_at"])

    @classmethod
    def complete_due_runs(cls, limit: int = 100) -> int:
        due_ids = list(
            DungeonRun.objects.filter(status=DungeonRunStatus.IN_PROGRESS, ends_at__lte=timezone.now())
            .order_by("ends_at")
            .values_list("id", flat=True)[:limit]
        )
        completed = 0
        for run_id in due_ids:
            with transaction.atomic():
                run = DungeonRun.objects.select_for_update().select_related("location", "character", "character__character_class").get(pk=run_id)
                before = run.status
                cls.finalize_due_run(run)
                if before != run.status:
                    completed += 1
        return completed


class InventoryService:
    @staticmethod
    def equipment_summary(character: Character) -> dict[str, float]:
        stats = {key: 0.0 for key in STAT_KEYS}
        for item in character.equipped_items.all():
            if item.is_broken:
                continue
            for key, value in (item.stats or {}).items():
                if key in stats:
                    stats[key] += float(value)
        stats["power"] = GameFormulaService.power_from_stats(stats)
        return {key: round(value, 2) for key, value in stats.items()}

    @staticmethod
    def repair_preview(user, item: UserItem) -> dict[str, Any]:
        cost = GameFormulaService.repair_cost(item)
        missing = max(item.durability_max - item.durability_current, 0)
        return {
            "item_id": item.id,
            "durability": {"current": item.durability_current, "max": item.durability_max, "missing": missing},
            "repair_cost_copper": cost,
            "user_money_copper": user.money_copper,
            "can_repair": missing > 0 and user.money_copper >= cost,
        }

    @staticmethod
    @transaction.atomic
    def repair(user, item_id: int) -> tuple[UserItem, int, int]:
        item = UserItem.objects.select_for_update().get(pk=item_id, owner_user=user)
        user = type(user).objects.select_for_update().get(pk=user.pk)
        cost = GameFormulaService.repair_cost(item)
        if item.durability_current >= item.durability_max:
            raise serializers.ValidationError("Item is already fully repaired.")
        if user.money_copper < cost:
            raise serializers.ValidationError("Not enough money to repair this item.")
        before = item.durability_current
        user.money_copper -= cost
        item.durability_current = item.durability_max
        user.save(update_fields=["money_copper", "updated_at"])
        item.save(update_fields=["durability_current", "updated_at"])
        RepairTransaction.objects.create(
            user=user,
            item=item,
            cost_copper=cost,
            durability_before=before,
            durability_after=item.durability_current,
        )
        return item, cost, user.money_copper

    @staticmethod
    @transaction.atomic
    def equip(user, item_id: int) -> tuple[UserItem, float]:
        character = DungeonRunService._get_character(user)
        character = Character.objects.select_for_update().select_related("character_class").get(pk=character.pk)
        item = UserItem.objects.select_for_update().select_related("template").get(pk=item_id, owner_user=user)
        if item.is_broken:
            raise serializers.ValidationError("Broken items cannot be equipped.")
        if not item_allowed_for_character(item, character):
            raise serializers.ValidationError("This item is not allowed for the character class.")

        UserItem.objects.filter(equipped_character=character, slot=item.slot).exclude(pk=item.pk).update(equipped_character=None)
        item.equipped_character = character
        try:
            item.save(update_fields=["equipped_character", "updated_at"])
        except IntegrityError as exc:
            raise serializers.ValidationError("Could not equip item in this slot.") from exc
        return item, GameFormulaService.character_stats(character)["power"]

    @staticmethod
    @transaction.atomic
    def unequip(user, item_id: int) -> float:
        character = DungeonRunService._get_character(user)
        item = UserItem.objects.select_for_update().get(pk=item_id, owner_user=user)
        if item.equipped_character_id == character.id:
            item.equipped_character = None
            item.save(update_fields=["equipped_character", "updated_at"])
        character = Character.objects.select_related("character_class").get(pk=character.pk)
        return GameFormulaService.character_stats(character)["power"]
