from __future__ import annotations

import random
from hashlib import sha256

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    DungeonMiniGameAttempt,
    DungeonMiniGameAttemptStatus,
    DungeonMiniGameConfig,
    DungeonRun,
    DungeonRunStatus,
)


MEMORY_PAIR_FACES = (
    "ember",
    "rune",
    "moon",
    "blade",
    "crown",
    "torch",
    "gate",
    "ash",
    "star",
    "shield",
    "key",
    "flask",
)


class DungeonMiniGameService:
    """Сервис попыток memory-pairs мини-игры и ускорения активного забега."""

    @staticmethod
    def _get_run_for_update(user, run_id: int, locale=DEFAULT_LOCALE) -> DungeonRun:
        try:
            run = (
                DungeonRun.objects.select_for_update()
                .select_related("character", "character__user", "location")
                .get(pk=run_id)
            )
            if run.location.mini_game_config_id:
                run.location.mini_game_config = DungeonMiniGameConfig.objects.get(pk=run.location.mini_game_config_id)
        except DungeonRun.DoesNotExist as exc:
            raise serializers.ValidationError(message("run_not_owned", locale)) from exc
        if run.character.user_id != user.id:
            raise serializers.ValidationError(message("run_not_owned", locale))
        return run

    @staticmethod
    def _config_for_run(run: DungeonRun) -> DungeonMiniGameConfig | None:
        config = run.location.mini_game_config
        if config and config.is_active:
            return config
        return None

    @classmethod
    def mini_game_payload(cls, run: DungeonRun) -> dict | None:
        """Возвращает минимальное состояние мини-игры для активного забега."""

        if run.status != DungeonRunStatus.IN_PROGRESS or not run.location.has_mini_game:
            return None

        attempt = run.mini_game_attempts.select_related("config").order_by("-started_at").first()
        if attempt and attempt.status == DungeonMiniGameAttemptStatus.IN_PROGRESS:
            cls.expire_attempt_if_needed(attempt)
            attempt.refresh_from_db()
        config = attempt.config if attempt else cls._config_for_run(run)
        if not config:
            return None

        return {
            "available": attempt is None and config.is_active,
            "started": attempt is not None,
            "status": attempt.status if attempt else None,
        }

    @staticmethod
    def config_payload(config: DungeonMiniGameConfig) -> dict:
        """Возвращает публичные настройки мини-игры."""

        return {
            "id": config.id,
            "difficulty": config.get_difficulty_display(),
            "pairs_count": config.pairs_count,
            "time_limit_seconds": config.time_limit_seconds,
            "reward_duration_reduction_seconds": config.reward_duration_reduction_seconds,
        }

    @classmethod
    def attempt_payload(cls, attempt: DungeonMiniGameAttempt, *, include_board: bool = True) -> dict:
        """Возвращает публичное состояние попытки мини-игры."""

        matched_ids = set(attempt.matched_card_ids or [])
        payload = {
            "id": attempt.id,
            "status": attempt.status,
            "config": cls.config_payload(attempt.config),
            "started_at": attempt.started_at,
            "expires_at": attempt.expires_at,
            "completed_at": attempt.completed_at,
            "moves_count": attempt.moves_count,
            "matched_pairs_count": attempt.matched_pairs_count,
            "duration_reduction_seconds": attempt.duration_reduction_seconds,
        }
        if include_board:
            payload["board"] = [
                {
                    "id": card["id"],
                    "position": card["position"],
                    "state": "matched" if card["id"] in matched_ids else "hidden",
                    "face": card["face"] if card["id"] in matched_ids else None,
                    "image_url": cls.face_image_url(card["face"]) if card["id"] in matched_ids else None,
                }
                for card in sorted(attempt.board, key=lambda item: item["position"])
            ]
        return payload

    @staticmethod
    def face_image_url(face: str) -> str:
        """Возвращает путь к публичной картинке лица карточки."""

        return f"/memory-faces/{face}.svg"

    @classmethod
    def _opened_card_payload(cls, card: dict, *, state: str) -> dict:
        return {
            "id": card["id"],
            "position": card["position"],
            "state": state,
            "face": card["face"],
            "image_url": cls.face_image_url(card["face"]),
        }

    @staticmethod
    def _reward_reduction_seconds(run: DungeonRun, config: DungeonMiniGameConfig) -> int:
        """Считает фиксированное ускорение без ухода раньше старта забега."""

        latest_allowed_end = max(run.started_at, run.ends_at - timezone.timedelta(seconds=config.reward_duration_reduction_seconds))
        return max(0, int((run.ends_at - latest_allowed_end).total_seconds()))

    @classmethod
    @transaction.atomic
    def start_attempt(cls, user, run_id: int, locale=DEFAULT_LOCALE) -> DungeonMiniGameAttempt:
        """Создаёт или возвращает активную попытку мини-игры для забега."""

        run = cls._get_run_for_update(user, run_id, locale)
        if run.status != DungeonRunStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_run_not_active", locale))
        if not run.location.has_mini_game:
            raise serializers.ValidationError(message("mini_game_not_available", locale))

        existing = run.mini_game_attempts.select_related("config").first()
        if existing:
            cls.expire_attempt_if_needed(existing)
            existing.refresh_from_db()
            if existing.status == DungeonMiniGameAttemptStatus.IN_PROGRESS:
                if existing.open_card_id:
                    existing.open_card_id = ""
                    existing.save(update_fields=["open_card_id", "updated_at"])
                return existing
            raise serializers.ValidationError(message("mini_game_already_finished", locale))

        config = cls._config_for_run(run)
        if not config:
            raise serializers.ValidationError(message("mini_game_not_available", locale))

        now = timezone.now()
        return DungeonMiniGameAttempt.objects.create(
            dungeon_run=run,
            config=config,
            user=user,
            character=run.character,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=config.time_limit_seconds),
            board=cls._build_board(run.id, config),
        )

    @classmethod
    @transaction.atomic
    def finish_attempt(
        cls,
        user,
        attempt_id: int,
        *,
        success: bool,
        moves_count: int,
        matched_pairs_count: int,
        locale=DEFAULT_LOCALE,
    ) -> DungeonMiniGameAttempt:
        """Фиксирует итог попытки и при успехе ускоряет активный забег."""

        try:
            attempt = (
                DungeonMiniGameAttempt.objects.select_for_update()
                .select_related("dungeon_run", "dungeon_run__character", "dungeon_run__location", "config")
                .get(pk=attempt_id)
            )
        except DungeonMiniGameAttempt.DoesNotExist as exc:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale)) from exc
        if attempt.user_id != user.id:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale))
        if attempt.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
            return attempt

        now = timezone.now()
        attempt.moves_count = max(0, moves_count)
        attempt.matched_pairs_count = min(max(0, matched_pairs_count), attempt.config.pairs_count)
        expired = attempt.expires_at <= now
        solved = success and attempt.matched_pairs_count >= attempt.config.pairs_count

        if expired or not solved or attempt.dungeon_run.status != DungeonRunStatus.IN_PROGRESS:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED
            attempt.completed_at = now
            attempt.save(update_fields=["status", "completed_at", "moves_count", "matched_pairs_count", "updated_at"])
            return attempt

        run = DungeonRun.objects.select_for_update().get(pk=attempt.dungeon_run_id)
        reduction = cls._reward_reduction_seconds(run, attempt.config)
        if reduction > 0 and run.status == DungeonRunStatus.IN_PROGRESS:
            run.ends_at = run.ends_at - timezone.timedelta(seconds=reduction)
            run.save(update_fields=["ends_at", "updated_at"])

        attempt.status = DungeonMiniGameAttemptStatus.SUCCESS
        attempt.completed_at = now
        attempt.duration_reduction_seconds = reduction
        attempt.save(
            update_fields=[
                "status",
                "completed_at",
                "moves_count",
                "matched_pairs_count",
                "duration_reduction_seconds",
                "updated_at",
            ]
        )
        return attempt

    @classmethod
    @transaction.atomic
    def reveal_card(cls, user, attempt_id: int, *, card_id: str, locale=DEFAULT_LOCALE) -> dict:
        """Открывает первую карточку хода и возвращает только её публичное лицо."""

        try:
            attempt = (
                DungeonMiniGameAttempt.objects.select_for_update()
                .select_related("dungeon_run", "config")
                .get(pk=attempt_id)
            )
        except DungeonMiniGameAttempt.DoesNotExist as exc:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale)) from exc
        if attempt.user_id != user.id:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale))
        if attempt.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_already_finished", locale))

        now = timezone.now()
        if attempt.expires_at <= now:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED
            attempt.completed_at = now
            attempt.save(update_fields=["status", "completed_at", "updated_at"])
            raise serializers.ValidationError(message("mini_game_expired", locale))

        cards_by_id = {card["id"]: card for card in attempt.board}
        card = cards_by_id.get(card_id)
        if not card:
            raise serializers.ValidationError(message("mini_game_invalid_move", locale))

        matched_ids = set(attempt.matched_card_ids or [])
        if card_id in matched_ids:
            raise serializers.ValidationError(message("mini_game_card_already_matched", locale))
        if attempt.open_card_id and attempt.open_card_id != card_id:
            open_card = cards_by_id.get(attempt.open_card_id)
            if open_card:
                return cls._opened_card_payload(open_card, state="temporary_open")

        attempt.open_card_id = card_id
        attempt.save(update_fields=["open_card_id", "updated_at"])
        return cls._opened_card_payload(card, state="temporary_open")

    @classmethod
    @transaction.atomic
    def make_move(cls, user, attempt_id: int, *, first_card_id: str, second_card_id: str, locale=DEFAULT_LOCALE) -> dict:
        """Проверяет ход memory-pairs на backend и выдаёт ускорение только при честном завершении."""

        try:
            attempt = (
                DungeonMiniGameAttempt.objects.select_for_update()
                .select_related("dungeon_run", "config")
                .get(pk=attempt_id)
            )
        except DungeonMiniGameAttempt.DoesNotExist as exc:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale)) from exc
        if attempt.user_id != user.id:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale))
        if attempt.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_already_finished", locale))

        now = timezone.now()
        if attempt.expires_at <= now:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED
            attempt.completed_at = now
            attempt.save(update_fields=["status", "completed_at", "updated_at"])
            raise serializers.ValidationError(message("mini_game_expired", locale))
        if first_card_id == second_card_id:
            raise serializers.ValidationError(message("mini_game_invalid_move", locale))
        if attempt.open_card_id and attempt.open_card_id != first_card_id:
            raise serializers.ValidationError(message("mini_game_invalid_move", locale))

        cards_by_id = {card["id"]: card for card in attempt.board}
        first_card = cards_by_id.get(first_card_id)
        second_card = cards_by_id.get(second_card_id)
        if not first_card or not second_card:
            raise serializers.ValidationError(message("mini_game_invalid_move", locale))

        matched_ids = set(attempt.matched_card_ids or [])
        if first_card_id in matched_ids or second_card_id in matched_ids:
            raise serializers.ValidationError(message("mini_game_card_already_matched", locale))

        is_match = first_card["pair_key"] == second_card["pair_key"]
        attempt.moves_count += 1
        if is_match:
            matched_ids.update([first_card_id, second_card_id])
            attempt.matched_card_ids = sorted(matched_ids)
            attempt.matched_pairs_count += 1

        reward = None
        if is_match and attempt.matched_pairs_count >= attempt.config.pairs_count:
            attempt.status = DungeonMiniGameAttemptStatus.SUCCESS
            attempt.completed_at = now
            run = DungeonRun.objects.select_for_update().get(pk=attempt.dungeon_run_id)
            reduction = cls._reward_reduction_seconds(run, attempt.config)
            if reduction > 0 and run.status == DungeonRunStatus.IN_PROGRESS:
                run.ends_at = run.ends_at - timezone.timedelta(seconds=reduction)
                run.save(update_fields=["ends_at", "updated_at"])
            attempt.duration_reduction_seconds = reduction
            reward = {"type": "dungeon_time_boost_seconds", "value": reduction}

        attempt.open_card_id = ""
        attempt.save(
            update_fields=[
                "status",
                "completed_at",
                "moves_count",
                "matched_pairs_count",
                "matched_card_ids",
                "open_card_id",
                "duration_reduction_seconds",
                "updated_at",
            ]
        )
        return {
            "matched": is_match,
            "attempt": cls.attempt_payload(attempt, include_board=True),
            "opened_cards": [
                cls._opened_card_payload(first_card, state="matched" if is_match else "temporary_open"),
                cls._opened_card_payload(second_card, state="matched" if is_match else "temporary_open"),
            ],
            "reward_granted": reward is not None,
            "reward": reward,
        }

    @staticmethod
    def expire_attempt_if_needed(attempt: DungeonMiniGameAttempt, now=None) -> DungeonMiniGameAttempt:
        """Помечает активную попытку проваленной, если её таймер истёк."""

        now = now or timezone.now()
        if attempt.status == DungeonMiniGameAttemptStatus.IN_PROGRESS and attempt.expires_at <= now:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED
            attempt.completed_at = now
            attempt.save(update_fields=["status", "completed_at", "updated_at"])
        return attempt

    @staticmethod
    def _build_board(run_id: int, config: DungeonMiniGameConfig) -> list[dict]:
        faces = list(MEMORY_PAIR_FACES[: config.pairs_count])
        cards = [
            {"id": f"{pair_index}-{copy_index}", "position": 0, "pair_key": face, "face": face}
            for pair_index, face in enumerate(faces)
            for copy_index in range(2)
        ]
        seed = int(sha256(f"{run_id}:{config.id}:{config.pairs_count}".encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        rng.shuffle(cards)
        for position, card in enumerate(cards, start=1):
            card["position"] = position
        return cards
