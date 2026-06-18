from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    AutoDungeonRun,
    AutoDungeonRunClaim,
    AutoDungeonRunStatus,
    Character,
    DungeonRun,
    DungeonRunStatus,
    IngredientTemplate,
)

from .dungeon_runs import ClaimResult, DungeonRunService

logger = logging.getLogger(__name__)


class AutoDungeonRunService:
    """Управляет запуском, остановкой и worker-циклом автозапуска."""

    @staticmethod
    def _get_character(user, locale=DEFAULT_LOCALE) -> Character:
        from .dungeon_runs import DungeonRunService

        return DungeonRunService._get_character(user, locale)

    @staticmethod
    def active_for_character(character: Character) -> AutoDungeonRun | None:
        return (
            AutoDungeonRun.objects.select_related("location", "current_run")
            .filter(
                character=character,
                status__in=(AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING),
            )
            .order_by("-started_at")
            .first()
        )

    @staticmethod
    def unread_summary_for_character(character: Character) -> AutoDungeonRun | None:
        return (
            AutoDungeonRun.objects.select_related("location", "current_run")
            .filter(
                character=character,
                status=AutoDungeonRunStatus.STOPPED,
                summary_unread=True,
            )
            .order_by("-stopped_at", "-updated_at")
            .first()
        )

    @classmethod
    def ensure_can_start_manual_run(cls, character: Character, locale=DEFAULT_LOCALE) -> None:
        if cls.active_for_character(character):
            raise serializers.ValidationError(message("auto_run_active", locale))
        if cls.unread_summary_for_character(character):
            raise serializers.ValidationError(message("auto_run_summary_unread", locale))

    @classmethod
    def start_auto_run(cls, user, location_id: int, locale=DEFAULT_LOCALE):
        from .dungeon_runs import DungeonRunService

        try:
            with transaction.atomic():
                character = cls._get_character(user, locale)
                Character.objects.select_for_update().get(pk=character.pk)
                cls.ensure_can_start_manual_run(character, locale)
                run = DungeonRunService.start_run(
                    user,
                    location_id,
                    locale=locale,
                    bypass_auto_guards=True,
                )
                from .formulas import GameFormulaService

                max_hp = int(GameFormulaService.character_stats(run.character)["max_hp"])
                auto_run = AutoDungeonRun.objects.create(
                    user=user,
                    character=run.character,
                    location=run.location,
                    current_run=run,
                    status=AutoDungeonRunStatus.ACTIVE,
                    started_at=run.started_at,
                    current_hp=run.character.current_hp,
                    max_hp=max_hp,
                )
                return run, auto_run
        except IntegrityError as exc:
            raise serializers.ValidationError(message("auto_run_active", locale)) from exc

    @classmethod
    def request_stop(cls, user, locale=DEFAULT_LOCALE) -> AutoDungeonRun:
        with transaction.atomic():
            character = cls._get_character(user, locale)
            auto_run = (
                AutoDungeonRun.objects.select_for_update()
                .filter(
                    character=character,
                    status__in=(AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING),
                )
                .order_by("-started_at")
                .first()
            )
            if auto_run is None:
                raise serializers.ValidationError(message("auto_run_not_found", locale))
            if auto_run.status == AutoDungeonRunStatus.ACTIVE:
                auto_run.status = AutoDungeonRunStatus.STOPPING
                auto_run.save(update_fields=["status", "updated_at"])
            return auto_run

    @classmethod
    def mark_summary_read(cls, user, locale=DEFAULT_LOCALE) -> AutoDungeonRun | None:
        with transaction.atomic():
            character = cls._get_character(user, locale)
            auto_run = (
                AutoDungeonRun.objects.select_for_update()
                .filter(
                    character=character,
                    status=AutoDungeonRunStatus.STOPPED,
                    summary_unread=True,
                )
                .order_by("-stopped_at", "-updated_at")
                .first()
            )
            if auto_run is None:
                return None
            auto_run.summary_unread = False
            auto_run.save(update_fields=["summary_unread", "updated_at"])
            return auto_run

    @staticmethod
    def is_auto_owned_run(run_id: int) -> bool:
        return (
            AutoDungeonRun.objects.filter(current_run_id=run_id).exists()
            or AutoDungeonRunClaim.objects.filter(dungeon_run_id=run_id).exists()
        )

    @staticmethod
    def _item_preview(item) -> dict:
        """Возвращает компактное описание предмета для сводки автозапуска."""

        return {
            "id": item.id,
            "name": item.name,
            "slot": item.slot,
            "item_type": item.item_type,
            "rarity": item.rarity,
            "item_level": item.item_level,
        }

    @staticmethod
    def _ingredient_previews(ingredients: list) -> list[dict]:
        """Группирует ингредиенты claim'а в публичные превью с количеством."""

        totals: dict[int, int] = {}
        for ingredient in ingredients or []:
            ingredient_id = ingredient.get("ingredient_id")
            quantity = int(ingredient.get("quantity") or 0)
            if ingredient_id and quantity > 0:
                totals[ingredient_id] = totals.get(ingredient_id, 0) + quantity
        if not totals:
            return []
        templates = IngredientTemplate.objects.in_bulk(totals.keys())
        previews = []
        for ingredient_id, quantity in sorted(totals.items()):
            template = templates.get(ingredient_id)
            previews.append(
                {
                    "ingredient_id": ingredient_id,
                    "code": template.code if template else "",
                    "name": template.name if template else "",
                    "quantity": quantity,
                }
            )
        return previews

    @staticmethod
    def _durability_previews(changes: list) -> list[dict]:
        """Преобразует изменения прочности в превью для auto-run summary."""

        previews = []
        for change in changes or []:
            item = change.get("item")
            if item is None:
                continue
            previews.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "slot": item.slot,
                    "removed": int(change.get("removed") or 0),
                    "durability": {
                        "current": item.durability_current,
                        "max": item.durability_max,
                    },
                }
            )
        return previews

    @classmethod
    def _claim_defaults(cls, result: ClaimResult) -> dict:
        """Возвращает поля `AutoDungeonRunClaim` из результата claim'а."""

        ingredients_preview = cls._ingredient_previews(result.ingredients)
        ingredient_total = sum(item["quantity"] for item in ingredients_preview)
        return {
            "claim": result.claim,
            "is_success": bool(result.run.is_success),
            "experience": result.claim.experience_claimed,
            "money_copper": result.claim.money_claimed_copper,
            "items_count": len(result.items),
            "ingredients_count": ingredient_total,
            "current_hp": result.current_hp,
            "max_hp": result.max_hp,
            "hp_loss": result.hp_loss,
            "durability_loss": result.durability_total,
            "items_preview": [cls._item_preview(item) for item in result.items],
            "ingredients_preview": ingredients_preview,
            "durability_changes": cls._durability_previews(result.durability_changes),
        }

    @staticmethod
    def _rebuild_summary(auto_run: AutoDungeonRun) -> None:
        """Пересобирает агрегаты автозапуска из уже учтенных claim'ов."""

        claims = list(auto_run.auto_claims.order_by("counted_at", "id"))
        item_previews = []
        ingredient_totals: dict[int, dict] = {}
        durability_totals: dict[int, dict] = {}

        for claim in claims:
            item_previews.extend(claim.items_preview or [])
            for ingredient in claim.ingredients_preview or []:
                ingredient_id = ingredient.get("ingredient_id")
                if not ingredient_id:
                    continue
                existing = ingredient_totals.setdefault(
                    ingredient_id,
                    {
                        "ingredient_id": ingredient_id,
                        "code": ingredient.get("code", ""),
                        "name": ingredient.get("name", ""),
                        "quantity": 0,
                    },
                )
                existing["quantity"] += int(ingredient.get("quantity") or 0)
            for change in claim.durability_changes or []:
                item_id = change.get("item_id")
                if not item_id:
                    continue
                existing = durability_totals.setdefault(
                    item_id,
                    {
                        "item_id": item_id,
                        "name": change.get("name", ""),
                        "slot": change.get("slot", ""),
                        "durability": {
                            "current": None,
                            "max": None,
                        },
                        "removed": 0,
                    },
                )
                existing["removed"] += int(change.get("removed") or 0)
                existing["name"] = change.get("name", existing["name"])
                existing["slot"] = change.get("slot", existing["slot"])
                durability = change.get("durability") or {
                    "current": change.get("durability_current"),
                    "max": change.get("durability_max"),
                }
                existing["durability"] = {
                    "current": durability.get("current"),
                    "max": durability.get("max"),
                }

        auto_run.runs_claimed = len(claims)
        auto_run.success_count = sum(1 for claim in claims if claim.is_success)
        auto_run.failure_count = sum(1 for claim in claims if not claim.is_success)
        auto_run.experience_total = sum(claim.experience for claim in claims)
        auto_run.money_total_copper = sum(claim.money_copper for claim in claims)
        auto_run.items_total = sum(claim.items_count for claim in claims)
        auto_run.ingredients_total = sum(claim.ingredients_count for claim in claims)
        auto_run.current_hp = claims[-1].current_hp if claims else 0
        auto_run.max_hp = claims[-1].max_hp if claims else 0
        auto_run.durability_loss_total = sum(claim.durability_loss for claim in claims)
        hp_loss_total = sum(claim.hp_loss for claim in claims)
        auto_run.durability_changes = list(durability_totals.values())
        auto_run.summary = {
            "hp_loss_total": hp_loss_total,
            "items_preview": item_previews[:3],
            "ingredients_preview": list(ingredient_totals.values())[:5],
            "durability_changes": auto_run.durability_changes,
        }

    @classmethod
    def _record_claim(cls, auto_run: AutoDungeonRun, result: ClaimResult) -> AutoDungeonRunClaim:
        """Идемпотентно учитывает один claim в сводке автозапуска."""

        auto_claim, _created = AutoDungeonRunClaim.objects.get_or_create(
            dungeon_run=result.run,
            defaults={
                "auto_run": auto_run,
                **cls._claim_defaults(result),
            },
        )
        cls._rebuild_summary(auto_run)
        auto_run.save(
            update_fields=[
                "runs_claimed",
                "success_count",
                "failure_count",
                "experience_total",
                "money_total_copper",
                "items_total",
                "ingredients_total",
                "current_hp",
                "max_hp",
                "durability_loss_total",
                "durability_changes",
                "summary",
                "updated_at",
            ]
        )
        return auto_claim

    @staticmethod
    def _validation_text(exc: serializers.ValidationError) -> str:
        detail = exc.detail
        if isinstance(detail, list):
            return " ".join(str(item) for item in detail)
        if isinstance(detail, dict):
            return " ".join(str(item) for value in detail.values() for item in (value if isinstance(value, list) else [value]))
        return str(detail)

    @classmethod
    def _map_start_blocker(cls, exc: serializers.ValidationError, locale=DEFAULT_LOCALE) -> tuple[str, str]:
        text = cls._validation_text(exc)
        mappings = [
            ("location_limit_reached", "daily_limit_reached"),
            ("category_limit_reached", "category_limit_reached"),
            ("hp_too_low", "hp_too_low"),
            ("broken_equipment", "broken_items_block_run"),
            ("location_unavailable", "dungeon_not_found"),
            ("active_run_conflict", "active_run_exists"),
            ("active_run_conflict", "unclaimed_run_exists"),
        ]
        for code, key in mappings:
            translated = message(key, locale)
            if translated in text:
                return code, translated
        return "system_error", message("auto_run_system_error", locale)

    @classmethod
    def _stop_auto_run_locked(
        cls,
        auto_run: AutoDungeonRun,
        *,
        code: str,
        stop_message: str,
        details: dict | None = None,
    ) -> None:
        auto_run.status = AutoDungeonRunStatus.STOPPED
        auto_run.summary_unread = True
        auto_run.stopped_at = timezone.now()
        auto_run.stop_reason_code = code
        auto_run.stop_reason_message = stop_message[:255]
        auto_run.stop_reason_details = details or {}
        auto_run.save(
            update_fields=[
                "status",
                "summary_unread",
                "stopped_at",
                "stop_reason_code",
                "stop_reason_message",
                "stop_reason_details",
                "updated_at",
            ]
        )

    @classmethod
    def _stop_auto_run(
        cls,
        auto_run_id: int,
        *,
        code: str,
        stop_message: str,
        details: dict | None = None,
    ) -> None:
        with transaction.atomic():
            auto_run = AutoDungeonRun.objects.select_for_update().get(pk=auto_run_id)
            cls._stop_auto_run_locked(
                auto_run,
                code=code,
                stop_message=stop_message,
                details=details,
            )

    @classmethod
    def _stop_system_error(cls, auto_run_id: int, exc: Exception, locale=DEFAULT_LOCALE) -> None:
        cls._stop_auto_run(
            auto_run_id,
            code="system_error",
            stop_message=message("auto_run_system_error", locale),
            details={
                "exception": exc.__class__.__name__,
                "auto_run_id": auto_run_id,
            },
        )

    @classmethod
    def _claim_current_run_for_accounting(cls, user, run, locale=DEFAULT_LOCALE) -> ClaimResult:
        if run.status == DungeonRunStatus.CLAIMED:
            # Best-effort legacy recovery for runs claimed before the worker's
            # claim/accounting path became atomic. Only persisted claim, item,
            # and ingredient data can be reconstructed here.
            return DungeonRunService.claim_run(user, run.id, locale=locale)

        DungeonRunService._finalize_locked(run)
        return DungeonRunService.claim_run(user, run.id, locale=locale)

    @classmethod
    def _claim_current_run(cls, auto_run_id: int, locale=DEFAULT_LOCALE) -> ClaimResult | None:
        with transaction.atomic():
            auto_run = (
                AutoDungeonRun.objects.select_for_update()
                .select_related("current_run", "user")
                .get(pk=auto_run_id)
            )
            if auto_run.status not in (AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING):
                return None
            run = (
                DungeonRun.objects.select_for_update()
                .select_related("location", "character", "character__character_class")
                .get(pk=auto_run.current_run_id)
            )
            if run.status == DungeonRunStatus.IN_PROGRESS and run.ends_at > timezone.now():
                return None
            if run.status not in (
                DungeonRunStatus.IN_PROGRESS,
                DungeonRunStatus.SUCCESS_WAITING_CLAIM,
                DungeonRunStatus.FAILED_WAITING_CLAIM,
                DungeonRunStatus.CLAIMED,
            ):
                return None
            if run.status == DungeonRunStatus.CLAIMED and not hasattr(run, "claim"):
                return None
            return cls._claim_current_run_for_accounting(auto_run.user, run, locale=locale)

    @classmethod
    def _record_claim_for_current_run(
        cls,
        auto_run_id: int,
        result: ClaimResult,
    ) -> bool:
        with transaction.atomic():
            auto_run = AutoDungeonRun.objects.select_for_update().get(pk=auto_run_id)
            if auto_run.status not in (AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING):
                return False
            if auto_run.current_run_id != result.run.id:
                return False
            cls._record_claim(auto_run, result)
            return True

    @classmethod
    def _finish_after_claim(cls, auto_run_id: int, claimed_run_id: int, locale=DEFAULT_LOCALE) -> bool:
        with transaction.atomic():
            auto_run = (
                AutoDungeonRun.objects.select_for_update()
                .select_related("user")
                .get(pk=auto_run_id)
            )
            if auto_run.status not in (AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING):
                return False
            if auto_run.current_run_id != claimed_run_id:
                return False
            if auto_run.status == AutoDungeonRunStatus.STOPPING:
                cls._stop_auto_run_locked(
                    auto_run,
                    code="player_stopped",
                    stop_message=message("auto_run_player_stopped", locale),
                )
                return True

            try:
                next_run = DungeonRunService.start_run(
                    auto_run.user,
                    auto_run.location_id,
                    locale=locale,
                    bypass_auto_guards=True,
                )
            except serializers.ValidationError as exc:
                code, stop_message = cls._map_start_blocker(exc, locale)
                cls._stop_auto_run_locked(
                    auto_run,
                    code=code,
                    stop_message=stop_message,
                    details={"message": cls._validation_text(exc), "auto_run_id": auto_run_id},
                )
                return True

            auto_run.current_run = next_run
            auto_run.save(update_fields=["current_run", "updated_at"])
            return True

    @classmethod
    def process_due_auto_runs(cls, limit: int = 100, locale=DEFAULT_LOCALE) -> int:
        now = timezone.now()
        auto_run_ids = list(
            AutoDungeonRun.objects.filter(
                status__in=(AutoDungeonRunStatus.ACTIVE, AutoDungeonRunStatus.STOPPING)
            )
            .filter(
                Q(current_run__status=DungeonRunStatus.IN_PROGRESS, current_run__ends_at__lte=now)
                | Q(
                    current_run__status__in=(
                        DungeonRunStatus.SUCCESS_WAITING_CLAIM,
                        DungeonRunStatus.FAILED_WAITING_CLAIM,
                    )
                )
                | Q(current_run__status=DungeonRunStatus.CLAIMED, current_run__claim__isnull=False)
            )
            .order_by("current_run__ends_at", "id")
            .values_list("id", flat=True)[:limit]
        )
        processed = 0
        for auto_run_id in auto_run_ids:
            try:
                if cls.process_single_auto_run(auto_run_id, locale=locale):
                    processed += 1
            except Exception:
                logger.exception("Auto run processing failed", extra={"auto_run_id": auto_run_id})
                continue
        return processed

    @classmethod
    def process_single_auto_run(cls, auto_run_id: int, locale=DEFAULT_LOCALE) -> bool:
        try:
            result = cls._claim_current_run(auto_run_id, locale=locale)
            if result is None:
                return False
            if not cls._record_claim_for_current_run(auto_run_id, result):
                return False
            return cls._finish_after_claim(auto_run_id, result.run.id, locale=locale)
        except Exception as exc:
            cls._stop_system_error(auto_run_id, exc, locale)
            raise
