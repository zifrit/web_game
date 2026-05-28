from __future__ import annotations

import math
import random
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import F, Value, QuerySet
from django.db.models.functions import Greatest
from django.utils import timezone
from rest_framework import serializers

from .i18n import DEFAULT_LOCALE, message
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
    "common": {
        "name": "Обычный",
        "stat_multiplier": 1.0,
        "economy_multiplier": Decimal("2.0"),
        "min_item_level": 1,
        "max_item_level": 3,
        "min_stats_count": 1,
        "max_stats_count": 1,
    },
    "uncommon": {
        "name": "Необычный",
        "stat_multiplier": 1.25,
        "economy_multiplier": Decimal("2.5"),
        "min_item_level": 2,
        "max_item_level": 5,
        "min_stats_count": 1,
        "max_stats_count": 2,
    },
    "rare": {
        "name": "Редкий",
        "stat_multiplier": 1.6,
        "economy_multiplier": Decimal("3.0"),
        "min_item_level": 4,
        "max_item_level": 8,
        "min_stats_count": 2,
        "max_stats_count": 3,
    },
    "epic": {
        "name": "Эпический",
        "stat_multiplier": 2.2,
        "economy_multiplier": Decimal("3.5"),
        "min_item_level": 7,
        "max_item_level": 10,
        "min_stats_count": 3,
        "max_stats_count": 3,
    },
}


class GameConfigService:
    """Сервис чтения игровых настроек с дефолтами и переопределениями из БД."""

    @staticmethod
    def get_config(key: str) -> dict[str, Any]:
        """Возвращает активную настройку по ключу, объединяя БД с DEFAULT_CONFIGS."""

        value = DEFAULT_CONFIGS.get(key, {}).copy()
        db_config = GameConfig.objects.filter(key=key, is_active=True).first()
        if db_config and isinstance(db_config.value, dict):
            value.update(db_config.value)
        return value


class GameBalanceService:
    """Сервис базового баланса: создание героя и параметры редкостей."""

    @staticmethod
    def create_character(user, name: str, character_class: CharacterClass) -> Character:
        """Создаёт героя с начальными статами класса и кэширует его силу."""

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
        """Возвращает параметры редкости из БД или встроенного набора по умолчанию."""

        db_config = RarityConfig.objects.filter(key=rarity, is_active=True).first()
        if db_config:
            return {
                "name": db_config.name,
                "stat_multiplier": db_config.stat_multiplier,
                "economy_multiplier": db_config.economy_multiplier,
                "min_item_level": db_config.min_item_level,
                "max_item_level": db_config.max_item_level,
                "min_stats_count": db_config.min_stats_count,
                "max_stats_count": db_config.max_stats_count,
            }
        if rarity not in DEFAULT_RARITIES:
            raise serializers.ValidationError(f"Unknown rarity: {rarity}")
        return DEFAULT_RARITIES[rarity]


class GameFormulaService:
    """Сервис серверных игровых формул для опыта, силы, шансов и прочности."""

    @staticmethod
    def experience_required(level: int) -> int:
        """Считает требуемый опыт для перехода с указанного уровня на следующий."""

        config = GameConfigService.get_config("experience_curve_config")
        return math.ceil(float(config["base"]) * (level ** float(config["exponent"])))

    @staticmethod
    def level_growth_stats(character: Character) -> dict[str, float]:
        """Считает прирост характеристик героя от уровней и профиля роста класса."""

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
        """Собирает итоговые характеристики героя с уровнем, экипировкой и капами."""

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
        """Считает показатель силы по набору характеристик и весам формулы."""

        config = GameConfigService.get_config("power_formula_config")
        return round(sum(float(stats.get(key, 0)) * float(config.get(key, 0)) for key in STAT_KEYS), 2)

    @staticmethod
    def success_chance(character_power: float, required_power: float) -> float:
        """Считает шанс успеха забега по силе героя и требуемой силе локации."""

        config = GameConfigService.get_config("success_chance_config")
        raw = float(config["base"]) + (character_power - required_power) * float(config["power_delta_multiplier"])
        return round(max(float(config["min"]), min(float(config["max"]), raw)), 2)

    @staticmethod
    def repair_cost(item: UserItem) -> int:
        """Считает стоимость ремонта недостающей прочности предмета."""

        missing = max(item.durability_max - item.durability_current, 0)
        multiplier = Decimal(str(GameBalanceService.rarity_config(item.rarity)["economy_multiplier"]))
        return int((multiplier * Decimal(missing) * Decimal("2.5")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    @staticmethod
    def destroy_refund(item: UserItem) -> int:
        """Считает возврат денег за уничтожение предмета."""

        multiplier = Decimal(str(GameBalanceService.rarity_config(item.rarity)["economy_multiplier"]))
        return int((multiplier * Decimal(item.durability_current) * Decimal("2")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    @staticmethod
    def durability_loss(is_success: bool) -> int:
        """Возвращает потерю прочности экипировки для успешного или провального забега."""

        config = GameConfigService.get_config("durability_loss_config")
        return int(config["success" if is_success else "failure"])


class LootGenerationService:
    """Сервис генерации предметных наград за успешные подземелья."""

    @staticmethod
    def _weighted_choice(chances: dict[str, float]) -> str:
        """Выбирает ключ из словаря весов случайным взвешенным броском."""

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
        """Генерирует черновик выпавшего предмета или None, если дропа нет."""

        if random.uniform(0, 100) > location.item_drop_chance:
            return None

        rarity = cls._weighted_choice(location.rarity_chances)
        rarity_config = GameBalanceService.rarity_config(rarity)
        templates = ItemTemplate.objects.filter(
            is_active=True,
            template_locations__location=location,
        ).distinct()
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
            base_value = random.randint(int(stat_range["min"]), int(stat_range["max"]))
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
    """Проверяет, подходит ли предмет классу героя по типу оружия и ограничениям."""

    item_type = item.item_type
    required_class = WEAPON_CLASS_BY_TYPE.get(item_type)
    if required_class and required_class != character.character_class.key:
        return False
    allowed_classes = getattr(item, "allowed_classes", None)
    if allowed_classes is None and hasattr(item, "template"):
        allowed_classes = item.template.allowed_classes
    return not allowed_classes or character.character_class_id in allowed_classes


@dataclass
class ClaimResult:
    """Результат получения наград за забег, включая уровни до и после."""

    run: DungeonRun
    claim: DungeonRunClaim
    items: list[UserItem]
    old_level: int
    new_level: int


class DungeonRunService:
    """Сервис жизненного цикла забегов: старт, завершение, claim и durability."""

    @staticmethod
    def _get_character(user, locale=DEFAULT_LOCALE) -> Character:
        """Возвращает героя пользователя или выбрасывает локализованную ошибку."""

        try:
            return user.character
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

    @classmethod
    @transaction.atomic
    def start_run(cls, user, location_id: int, locale=DEFAULT_LOCALE) -> DungeonRun:
        """Транзакционно запускает новый забег героя в выбранную локацию."""

        character = cls._get_character(user, locale)
        character = Character.objects.select_for_update().select_related("character_class").prefetch_related("equipped_items").get(pk=character.pk)
        if DungeonRun.objects.filter(character=character, status=DungeonRunStatus.IN_PROGRESS).exists():
            raise serializers.ValidationError(message("active_run_exists", locale))
        if character.equipped_items.filter(durability_current=0).exists():
            raise serializers.ValidationError(message("broken_items_block_run", locale))
        try:
            location = DungeonLocation.objects.get(pk=location_id, is_active=True)
        except DungeonLocation.DoesNotExist as exc:
            raise serializers.ValidationError(message("dungeon_not_found", locale)) from exc

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
        """Завершает забег, если его таймер истёк, и фиксирует результат."""

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
    def claim_run(cls, user, run_id: int, locale=DEFAULT_LOCALE) -> ClaimResult:
        """Идемпотентно начисляет награды за готовый забег и помечает его claimed."""

        run = (
            DungeonRun.objects.select_for_update()
            .select_related("character", "character__user", "character__character_class", "location")
            .get(pk=run_id)
        )
        if run.character.user_id != user.id:
            raise serializers.ValidationError(message("run_not_owned", locale))
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
            raise serializers.ValidationError(message("run_not_ready", locale))

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
        """Повышает уровень героя, пока хватает опыта и не достигнут максимум."""

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
        """Списывает прочность со всей экипировки героя после завершения забега."""

        if loss <= 0:
            return
        character.equipped_items.filter(durability_current__gt=0).update(
            durability_current=Greatest(F("durability_current") - loss, Value(0)),
            updated_at=timezone.now(),
        )

    @classmethod
    def complete_due_runs(cls, limit: int = 100) -> int:
        """Находит просроченные активные забеги и завершает их пачкой."""

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
    """Сервис правил инвентаря, экипировки и ремонта предметов."""

    @staticmethod
    def can_equip(item: UserItem, character: Character) -> bool:
        """Проверяет владение, прочность, слот и классовые ограничения предмета."""

        if item.owner_user_id != character.user_id:
            return False
        if item.is_broken:
            return False
        if item.slot not in EQUIPMENT_SLOTS:
            return False
        return item_allowed_for_character(item, character)

    @staticmethod
    def equipment_summary(character: Character) -> dict[str, float]:
        """Суммирует вклад несломанной экипировки в характеристики героя."""

        stats = {key: 0.0 for key in STAT_KEYS}
        for item in character.equipped_items.all():
            if item.is_broken:
                continue
            for key, value in (item.stats or {}).items():
                if key in stats:
                    stats[key] += float(value)
        stats["power"] = GameFormulaService.power_from_stats(stats)
        return {key: round(value, 2) for key, value in stats.items()}

    @classmethod
    def _owned_items(cls, user, item_ids: list[int] | tuple[int, ...], for_update: bool = False) -> QuerySet[UserItem]:
        """Возвращает queryset выбранных предметов текущего пользователя."""

        qs = UserItem.objects.filter(owner_user=user, pk__in=item_ids).select_related("template")
        if for_update:
            qs = qs.select_for_update()
        return qs

    @staticmethod
    def _repair_preview_payload(user, items: list[UserItem]) -> dict[str, Any]:
        repairable = [item for item in items if item.durability_current < item.durability_max]
        total_missing = sum(max(item.durability_max - item.durability_current, 0) for item in repairable)
        total_cost = sum(GameFormulaService.repair_cost(item) for item in repairable)
        return {
            "item_ids": [item.id for item in repairable],
            "items_count": len(repairable),
            "durability_missing": total_missing,
            "repair_cost_copper": total_cost,
            "user_money_copper": user.money_copper,
            "can_repair": len(repairable) > 0 and user.money_copper >= total_cost,
        }

    @staticmethod
    def _destroy_preview_payload(user, items: list[UserItem]) -> dict[str, Any]:
        refund = sum(GameFormulaService.destroy_refund(item) for item in items)
        return {
            "item_ids": [item.id for item in items],
            "items_count": len(items),
            "refund_copper": refund,
            "user_money_copper": user.money_copper,
            "can_destroy": len(items) > 0,
        }

    @classmethod
    def repair_preview(cls, user, item_ids: list[int] | tuple[int, ...]) -> dict[str, Any]:
        """Возвращает массовый расчёт ремонта без изменения баланса и прочности."""

        qs = cls._owned_items(user, item_ids)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", DEFAULT_LOCALE))
        return cls._repair_preview_payload(user, items)

    @classmethod
    def destroy_preview(cls, user, item_ids: list[int] | tuple[int, ...]) -> dict[str, Any]:
        """Возвращает массовый расчёт возврата за уничтожение предметов."""

        qs = cls._owned_items(user, item_ids)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", DEFAULT_LOCALE))
        return cls._destroy_preview_payload(user, items)

    @classmethod
    @transaction.atomic
    def repair_items(cls, user, item_ids: list[int] | tuple[int, ...], locale=DEFAULT_LOCALE) -> dict[str, Any]:
        """Транзакционно ремонтирует выбранные предметы и списывает общую стоимость."""

        user = type(user).objects.select_for_update().get(pk=user.pk)
        qs = cls._owned_items(user, item_ids, for_update=True)
        items = list(qs)
        repairable = [item for item in items if item.durability_current < item.durability_max]
        if not repairable:
            raise serializers.ValidationError(message("no_repair_needed", locale))
        cost = sum(GameFormulaService.repair_cost(item) for item in repairable)
        if user.money_copper < cost:
            raise serializers.ValidationError(message("not_enough_money_repair", locale))

        user.money_copper -= cost
        user.save(update_fields=["money_copper", "updated_at"])
        repair_transactions = []
        for item in repairable:
            before = item.durability_current
            item_cost = GameFormulaService.repair_cost(item)
            item.durability_current = item.durability_max
            item.save(update_fields=["durability_current", "updated_at"])
            repair_transactions.append(
                RepairTransaction(
                    user=user,
                    item=item,
                    cost_copper=item_cost,
                    durability_before=before,
                    durability_after=item.durability_current,
                )
            )
        RepairTransaction.objects.bulk_create(repair_transactions)
        return {
            "success": True,
            "item_ids": [item.id for item in repairable],
            "items_count": len(repairable),
            "repair_cost_copper": cost,
            "remaining_money_copper": user.money_copper,
        }

    @classmethod
    def repair(cls, user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, int, int]:
        """Совместимая одиночная обёртка поверх массового ремонта."""

        result = cls.repair_items(user, [item_id], locale=locale)
        item = UserItem.objects.get(pk=item_id, owner_user=user)
        return item, result["repair_cost_copper"], result["remaining_money_copper"]

    @classmethod
    @transaction.atomic
    def destroy_items(cls, user, item_ids: list[int] | tuple[int, ...], locale=DEFAULT_LOCALE) -> dict[str, Any]:
        """Транзакционно удаляет выбранные предметы и начисляет возврат."""

        user = type(user).objects.select_for_update().get(pk=user.pk)
        qs = cls._owned_items(user, item_ids, for_update=True)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", locale))
        refund = sum(GameFormulaService.destroy_refund(item) for item in items)
        destroyed_ids = [item.id for item in items]
        user.money_copper += refund
        user.save(update_fields=["money_copper", "updated_at"])
        UserItem.objects.filter(pk__in=destroyed_ids, owner_user=user).delete()
        return {
            "success": True,
            "item_ids": destroyed_ids,
            "items_count": len(destroyed_ids),
            "refund_copper": refund,
            "remaining_money_copper": user.money_copper,
        }

    @staticmethod
    @transaction.atomic
    def equip(user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, UserItem | None, Character]:
        """Транзакционно экипирует предмет и возвращает снятый предмет слота."""

        character = DungeonRunService._get_character(user, locale)
        character = Character.objects.select_for_update().select_related("character_class").get(pk=character.pk)
        item = UserItem.objects.select_for_update().select_related("template").get(pk=item_id, owner_user=user)
        if item.is_broken:
            raise serializers.ValidationError(message("broken_item_equip", locale))
        if not item_allowed_for_character(item, character):
            raise serializers.ValidationError(message("class_not_allowed", locale))

        replaced_item = (
            UserItem.objects.select_for_update()
            .select_related("template")
            .filter(equipped_character=character, slot=item.slot)
            .exclude(pk=item.pk)
            .first()
        )
        if replaced_item:
            replaced_item.equipped_character = None
            replaced_item.save(update_fields=["equipped_character", "updated_at"])

        item.equipped_character = character
        try:
            item.save(update_fields=["equipped_character", "updated_at"])
        except IntegrityError as exc:
            raise serializers.ValidationError(message("equip_failed", locale)) from exc
        return item, replaced_item, character

    @staticmethod
    @transaction.atomic
    def unequip(user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, Character]:
        """Транзакционно снимает предмет с героя и возвращает предмет с героем."""

        character = DungeonRunService._get_character(user, locale)
        item = UserItem.objects.select_for_update().select_related("template").get(pk=item_id, owner_user=user)
        if item.equipped_character_id == character.id:
            item.equipped_character = None
            item.save(update_fields=["equipped_character", "updated_at"])
        character = Character.objects.select_related("character_class").get(pk=character.pk)
        return item, character
