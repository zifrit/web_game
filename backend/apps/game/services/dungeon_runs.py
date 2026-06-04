from __future__ import annotations

import random

from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Greatest
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
    UserItem,
)

from .config import GameConfigService
from .formulas import GameFormulaService
from .loot import LootGenerationService
from .mini_game_store import MiniGameStore


class ClaimResult(BaseModel):
    """Результат получения наград за забег, включая уровни до и после."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
                run = (
                    DungeonRun.objects.select_for_update()
                    .select_related("location", "character", "character__character_class")
                    .get(pk=run_id)
                )
                before = run.status
                cls.finalize_due_run(run)
                if before != run.status:
                    completed += 1
        return completed
