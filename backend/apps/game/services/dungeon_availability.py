from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Count
from django.utils import timezone

from apps.game.models import (
    AutoDungeonRun,
    AutoDungeonRunStatus,
    Character,
    DungeonLocation,
    DungeonRun,
    DungeonRunStatus,
    LocationType,
)

from .dungeon_runs import DungeonRunService
from .formulas import GameFormulaService


@dataclass(frozen=True)
class DungeonAvailabilityContext:
    """Предрасчитанное состояние героя для рендера запуска локаций."""

    character: Character | None
    active_run: DungeonRun | None
    unclaimed_run: DungeonRun | None
    auto_run: AutoDungeonRun | None
    daily_used_map: dict[int, int]
    category_limit_state_map: dict[int, dict]
    has_broken_equipment: bool = False
    hp_too_low: bool = False


class DungeonAvailabilityService:
    """Собирает состояние доступности запуска для API локаций."""

    @classmethod
    def context_for_locations(
        cls,
        character: Character | None,
        locations: list[DungeonLocation],
    ) -> DungeonAvailabilityContext:
        """Возвращает переиспользуемый контекст доступности для набора локаций."""

        if character is None:
            return DungeonAvailabilityContext(
                character=None,
                active_run=None,
                unclaimed_run=None,
                auto_run=None,
                daily_used_map={},
                category_limit_state_map=cls._category_limit_state_map(None, locations),
            )

        from .auto_runs import AutoDungeonRunService

        active_run = cls._current_run(character, [DungeonRunStatus.IN_PROGRESS])
        unclaimed_run = cls._current_run(
            character,
            [
                DungeonRunStatus.SUCCESS_WAITING_CLAIM,
                DungeonRunStatus.FAILED_WAITING_CLAIM,
            ],
        )
        auto_run = (
            AutoDungeonRunService.active_for_character(character)
            or AutoDungeonRunService.unread_summary_for_character(character)
        )
        stats = GameFormulaService.character_stats(character)
        equipped_items = list(character.equipped_items.all())
        return DungeonAvailabilityContext(
            character=character,
            active_run=active_run,
            unclaimed_run=unclaimed_run,
            auto_run=auto_run,
            daily_used_map=cls._location_daily_used_map(character),
            category_limit_state_map=cls._category_limit_state_map(character, locations),
            has_broken_equipment=any(item.durability_current == 0 for item in equipped_items),
            hp_too_low=GameFormulaService.is_hp_too_low_to_start(character.current_hp, int(stats["max_hp"])),
        )

    @staticmethod
    def _current_run(character: Character, statuses: list[str]) -> DungeonRun | None:
        return (
            DungeonRun.objects.select_related("location", "character", "character__character_class")
            .filter(character=character, status__in=statuses)
            .order_by("-started_at")
            .first()
        )

    @staticmethod
    def _location_daily_used_map(character: Character | None, location_id=None) -> dict[int, int]:
        if character is None:
            return {}
        rows = DungeonRun.objects.filter(
            character=character,
            started_at__date=timezone.localdate(),
        )
        if location_id is not None:
            rows = rows.filter(location_id=location_id)
        rows = rows.values("location_id").annotate(n=Count("id"))
        return {row["location_id"]: row["n"] for row in rows}

    @staticmethod
    def _category_limit_state_map(
        character: Character | None,
        locations: list[DungeonLocation],
    ) -> dict[int, dict]:
        categories = {
            location.limit_category_id: location.limit_category
            for location in locations
            if location.limit_category_id is not None
        }
        return {
            category_id: DungeonRunService.category_limit_state(character, category)
            for category_id, category in categories.items()
        }

    @staticmethod
    def daily_remaining(location: DungeonLocation, context: DungeonAvailabilityContext) -> int | None:
        if location.daily_limit == 0:
            return None
        used = context.daily_used_map.get(location.id, 0)
        return max(0, location.daily_limit - used)

    @classmethod
    def action_state(
        cls,
        location: DungeonLocation,
        context: DungeonAvailabilityContext,
        *,
        daily_remaining: int | None,
        limit_category: dict,
    ) -> dict:
        blocker_code = cls._blocker_code(
            location,
            context,
            daily_remaining=daily_remaining,
            limit_category=limit_category,
        )
        return {
            "can_start": blocker_code is None,
            "blocker_code": blocker_code,
            "is_active_location": cls._is_active_location(location, context),
            "daily_remaining": daily_remaining,
            "limit_category": limit_category,
        }

    @classmethod
    def _blocker_code(
        cls,
        location: DungeonLocation,
        context: DungeonAvailabilityContext,
        *,
        daily_remaining: int | None,
        limit_category: dict,
    ) -> str | None:
        if context.character is None:
            return "no_character"
        if context.auto_run is not None:
            if context.auto_run.status in (AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING):
                return "auto_run_active"
            if context.auto_run.status == AutoDungeonRunStatus.STOPPED and context.auto_run.summary_unread:
                return "auto_run_summary_unread"
        if context.active_run is not None:
            return "active_run_exists"
        if context.unclaimed_run is not None:
            return "unclaimed_run_exists"
        if limit_category["is_exhausted"]:
            return "category_limit_reached"
        if daily_remaining == 0:
            return "daily_limit_reached"
        if location.location_type != LocationType.RESOURCE and context.has_broken_equipment:
            return "broken_items_block_run"
        if location.location_type != LocationType.RESOURCE and context.hp_too_low:
            return "hp_too_low"
        return None

    @staticmethod
    def _is_active_location(
        location: DungeonLocation,
        context: DungeonAvailabilityContext,
    ) -> bool:
        if context.active_run is not None:
            return context.active_run.location_id == location.id
        if context.auto_run is not None:
            return context.auto_run.location_id == location.id
        return False
