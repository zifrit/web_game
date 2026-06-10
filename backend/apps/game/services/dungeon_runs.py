from __future__ import annotations

import random

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from pydantic import BaseModel, ConfigDict

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    DungeonMiniGameAttemptStatus,
    DungeonLocation,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunClaimItem,
    DungeonRunStatus,
    LocationType,
    MoneyTransaction,
    UserItem,
)

from .config import GameConfigService
from .formulas import GameFormulaService
from .ingredients import IngredientDropService
from .loot import LootGenerationService
from .mini_game_store import MiniGameStore
from .money import MoneyService
from .storages import INGREDIENT_STORAGE


class ClaimResult(BaseModel):
    """Результат получения наград за забег, включая уровни до и после."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run: DungeonRun
    claim: DungeonRunClaim
    items: list[UserItem]
    old_level: int
    new_level: int
    durability_total: int = 0
    durability_changes: list = []
    hp_loss: int = 0
    current_hp: int = 0
    max_hp: int = 0
    ingredients: list = []


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
        if DungeonRun.objects.filter(
            character=character,
            status__in=(
                DungeonRunStatus.SUCCESS_WAITING_CLAIM,
                DungeonRunStatus.FAILED_WAITING_CLAIM,
            ),
        ).exists():
            raise serializers.ValidationError(message("unclaimed_run_exists", locale))
        try:
            location = DungeonLocation.objects.get(pk=location_id, is_active=True)
        except DungeonLocation.DoesNotExist as exc:
            raise serializers.ValidationError(message("dungeon_not_found", locale)) from exc

        if location.location_type == LocationType.RESOURCE:
            # Ресурсная локация: гарантированный успех, доступна при любом HP,
            # не требует силы и не проверяет сломанную экипировку. Действует только
            # общий гвард «одна активность за раз» (выше) и дневной лимит.
            if location.daily_limit > 0:
                used_today = DungeonRun.objects.filter(
                    character=character,
                    location=location,
                    started_at__date=timezone.localdate(),
                ).count()
                if used_today >= location.daily_limit:
                    raise serializers.ValidationError(message("daily_limit_reached", locale))
            success_chance = 100
        else:
            if character.equipped_items.filter(durability_current=0).exists():
                raise serializers.ValidationError(message("broken_items_block_run", locale))
            stats = GameFormulaService.character_stats(character)
            total_max_hp = int(stats["max_hp"])
            if GameFormulaService.is_hp_too_low_to_start(character.current_hp, total_max_hp):
                raise serializers.ValidationError(message("hp_too_low", locale))
            hp_penalty = GameFormulaService.hp_success_penalty(character.current_hp, total_max_hp)
            success_chance = GameFormulaService.success_chance(stats["power"], location.required_power, hp_penalty=hp_penalty)
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
    def finalize_due_run(cls, run_id: int, now=None) -> DungeonRun:
        """Самоблокирующийся расчёт забега: берёт его под select_for_update в
        своей транзакции, перечитывает статус под локом и фиксирует исход.

        Идемпотентен и безопасен при гонке: одновременные вызовы (Celery beat,
        GET текущего забега) сериализуются на блокировке, и второй видит забег
        уже в *_WAITING_CLAIM и ничего не пересчитывает. Возвращает забег.
        """

        with transaction.atomic():
            run = (
                DungeonRun.objects.select_for_update()
                .select_related("location", "character", "character__character_class")
                .get(pk=run_id)
            )
            cls._finalize_locked(run, now=now)
        return run

    @classmethod
    def _finalize_locked(cls, run: DungeonRun, now=None) -> bool:
        """Фиксирует исход забега, если таймер истёк. Требует, чтобы строка
        забега уже была заблокирована вызывающим (select_for_update).

        Возвращает True, если забег реально переведён в *_WAITING_CLAIM, иначе
        False (таймер не истёк или забег уже не IN_PROGRESS)."""

        now = now or timezone.now()
        if run.status != DungeonRunStatus.IN_PROGRESS or run.ends_at > now:
            return False

        location = run.location
        if location.location_type == LocationType.RESOURCE:
            # Ресурсная локация: гарантированный успех, только ингредиенты.
            run.is_success = True
            run.completed_at = now
            run.status = DungeonRunStatus.SUCCESS_WAITING_CLAIM
            run.experience_reward = 0
            run.money_reward_copper = 0
            run.items_reward = []
            run.ingredients_reward = IngredientDropService.roll_drops(location)
            run.durability_loss = 0
            run.hp_loss = 0
        else:
            is_success = random.uniform(0, 100) <= run.success_chance
            run.is_success = is_success
            run.completed_at = now
            run.status = DungeonRunStatus.SUCCESS_WAITING_CLAIM if is_success else DungeonRunStatus.FAILED_WAITING_CLAIM
            run.experience_reward = random.randint(location.experience_min, location.experience_max) if is_success else 0
            run.money_reward_copper = random.randint(location.money_min_copper, location.money_max_copper) if is_success else 0
            item_reward = LootGenerationService.generate_item_reward(run.character, location) if is_success else None
            run.items_reward = [item_reward] if item_reward else []
            run.ingredients_reward = IngredientDropService.roll_drops(location) if is_success else []
            run.durability_loss = GameFormulaService.durability_loss(is_success)
            total_max_hp = int(GameFormulaService.character_stats(run.character)["max_hp"])
            hp_loss_percent = location.hp_loss_success_percent if is_success else location.hp_loss_fail_percent
            run.hp_loss = GameFormulaService.hp_loss(total_max_hp, hp_loss_percent)
        had_active_mini_game = run.mini_game_attempts.filter(
            status=DungeonMiniGameAttemptStatus.IN_PROGRESS
        ).update(
            status=DungeonMiniGameAttemptStatus.FAILED,
            completed_at=now,
            updated_at=now,
        )
        if had_active_mini_game:
            MiniGameStore.clear(run.id)
        run.save(
            update_fields=[
                "is_success",
                "completed_at",
                "status",
                "experience_reward",
                "money_reward_copper",
                "items_reward",
                "ingredients_reward",
                "durability_loss",
                "hp_loss",
                "updated_at",
            ]
        )
        return True

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
        cls._finalize_locked(run)

        existing_claim = getattr(run, "claim", None)
        if existing_claim:
            return ClaimResult(
                run=run,
                claim=existing_claim,
                items=[claim_item.user_item for claim_item in existing_claim.claim_items.select_related("user_item")],
                old_level=run.character.level,
                new_level=run.character.level,
                hp_loss=0,
                current_hp=run.character.current_hp,
                max_hp=int(GameFormulaService.character_stats(run.character)["max_hp"]),
                ingredients=run.ingredients_reward or [],
            )

        if run.status not in (DungeonRunStatus.SUCCESS_WAITING_CLAIM, DungeonRunStatus.FAILED_WAITING_CLAIM):
            raise serializers.ValidationError(message("run_not_ready", locale))

        character = Character.objects.select_for_update().select_related("character_class").get(pk=run.character_id)
        old_level = character.level
        experience = run.experience_reward or 0
        character.experience += experience
        cls._apply_level_ups(character)
        GameFormulaService.apply_level_stats(character)
        hp_loss = run.hp_loss or 0
        character.current_hp = max(0, character.current_hp - hp_loss)
        money_reward = run.money_reward_copper or 0
        if money_reward > 0:
            MoneyService.grant(
                user=user,
                amount=money_reward,
                reason=MoneyTransaction.Reason.DUNGEON_REWARD,
                metadata={"dungeon_run_id": run.id},
            )
        character.save(
            update_fields=[
                "level",
                "experience",
                "max_hp",
                "current_hp",
                "intellect",
                "attack",
                "defense",
                "critical_chance",
                "evasion",
                "updated_at",
            ]
        )

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

        for drop in run.ingredients_reward or []:
            INGREDIENT_STORAGE.deposit(character, drop["ingredient_id"], drop["quantity"])

        durability_total, durability_changes = cls._apply_durability_loss(character, run.durability_loss or 0)
        GameFormulaService.refresh_power_cache(character)
        total_max_hp = int(GameFormulaService.character_stats(character)["max_hp"])
        run.status = DungeonRunStatus.CLAIMED
        run.save(update_fields=["status", "updated_at"])
        return ClaimResult(
            run=run,
            claim=claim,
            items=created_items,
            old_level=old_level,
            new_level=character.level,
            durability_total=durability_total,
            durability_changes=durability_changes,
            hp_loss=hp_loss,
            current_hp=character.current_hp,
            max_hp=total_max_hp,
            ingredients=run.ingredients_reward or [],
        )

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
    def _apply_durability_loss(character: Character, loss: int) -> tuple[int, list[dict]]:
        """Списывает прочность с экипировки и возвращает суммарную потерю и разбивку."""

        if loss <= 0:
            return 0, []
        items = list(character.equipped_items.filter(durability_current__gt=0))
        if not items:
            return 0, []
        now = timezone.now()
        total_removed = 0
        changes: list[dict] = []
        for item in items:
            removed = min(item.durability_current, loss)
            item.durability_current -= removed
            item.updated_at = now
            total_removed += removed
            changes.append({"item": item, "removed": removed})
        UserItem.objects.bulk_update(items, ["durability_current", "updated_at"])
        return total_removed, changes

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
                run = (
                    DungeonRun.objects.select_for_update()
                    .select_related("location", "character", "character__character_class")
                    .get(pk=run_id)
                )
                if cls._finalize_locked(run):
                    completed += 1
        return completed
