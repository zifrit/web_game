from __future__ import annotations

import random
from hashlib import sha256

from django.conf import settings
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
from apps.game.services.mini_game_store import MiniGameStore


class DungeonMiniGameService:
    """Сервис memory-pairs мини-игры: live-стейт в Redis, финальный снимок в БД."""

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _get_run_for_update(user, run_id: int, locale=DEFAULT_LOCALE) -> DungeonRun:
        try:
            run = (
                DungeonRun.objects.select_for_update()
                .select_related("character", "character__user", "location")
                .get(pk=run_id)
            )
        except DungeonRun.DoesNotExist as exc:
            raise serializers.ValidationError(message("run_not_owned", locale)) from exc
        if run.character.user_id != user.id:
            raise serializers.ValidationError(message("run_not_owned", locale))
        return run

    @staticmethod
    def _load_attempt(user, attempt_id: int, locale=DEFAULT_LOCALE) -> DungeonMiniGameAttempt:
        try:
            attempt = (
                DungeonMiniGameAttempt.objects.select_related(
                    "dungeon_run", "dungeon_run__location", "config"
                ).get(pk=attempt_id)
            )
        except DungeonMiniGameAttempt.DoesNotExist as exc:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale)) from exc
        if attempt.user_id != user.id:
            raise serializers.ValidationError(message("mini_game_attempt_not_found", locale))
        return attempt

    @staticmethod
    def _ttl_seconds(expires_at) -> int:
        remaining = int((expires_at - timezone.now()).total_seconds())
        return remaining + settings.MINIGAME_STATE_TTL_BUFFER_SECONDS

    # ------------------------------------------------------------------ payloads

    @staticmethod
    def config_payload(config: DungeonMiniGameConfig) -> dict:
        """Возвращает публичные настройки выбранной сложности."""

        return {
            "id": config.id,
            "difficulty": config.get_difficulty_display(),
            "pairs_count": config.pairs_count,
            "time_limit_seconds": config.time_limit_seconds,
            "reward_duration_reduction_percent": config.reward_duration_reduction_percent,
            "max_reduction_seconds": config.max_reduction_seconds,
        }

    @classmethod
    def mini_game_payload(cls, run: DungeonRun) -> dict | None:
        """Минимальное состояние мини-игры для активного забега (для DungeonRunSerializer)."""

        if run.status != DungeonRunStatus.IN_PROGRESS or not run.location.has_mini_game:
            return None
        attempt = run.mini_game_attempts.order_by("-started_at").first()
        return {
            "available": attempt is None,
            "started": attempt is not None,
            "status": attempt.status if attempt else None,
            "attempt_id": attempt.id if attempt else None,
        }

    @staticmethod
    def _card_public(card: dict, matched_ids: set, open_card_id: str) -> dict:
        """Публичная карточка: код лица раскрывается только для matched/open."""

        revealed = card["id"] in matched_ids or card["id"] == open_card_id
        if card["id"] in matched_ids:
            state = "matched"
        elif card["id"] == open_card_id:
            state = "open"
        else:
            state = "hidden"
        return {
            "id": card["id"],
            "position": card["position"],
            "state": state,
            "code": card["face"] if revealed else None,
        }

    @classmethod
    def attempt_payload(cls, attempt: DungeonMiniGameAttempt, *, include_board: bool = True) -> dict:
        """Публичное состояние попытки. Для активной партии читает live-стейт из Redis."""

        state = None
        if attempt.status == DungeonMiniGameAttemptStatus.IN_PROGRESS:
            state = MiniGameStore.load(attempt.dungeon_run_id)

        if state is not None:
            matched_ids = set(state.get("matched_card_ids") or [])
            open_card_id = state.get("open_card_id") or ""
            moves_count = state.get("moves_count", 0)
            matched_pairs_count = state.get("matched_pairs_count", 0)
        else:
            matched_ids = set(attempt.matched_card_ids or [])
            open_card_id = attempt.open_card_id or ""
            moves_count = attempt.moves_count
            matched_pairs_count = attempt.matched_pairs_count

        payload = {
            "id": attempt.id,
            "status": attempt.status,
            "config": cls.config_payload(attempt.config),
            "started_at": attempt.started_at,
            "expires_at": attempt.expires_at,
            "completed_at": attempt.completed_at,
            "moves_count": moves_count,
            "matched_pairs_count": matched_pairs_count,
            "duration_reduction_seconds": attempt.duration_reduction_seconds,
            "system_error": attempt.system_error,
        }
        if include_board:
            payload["board"] = [
                cls._card_public(card, matched_ids, open_card_id)
                for card in sorted(attempt.board, key=lambda item: item["position"])
            ]
        return payload

    # ------------------------------------------------------------------ board

    @staticmethod
    def _build_board(run_id: int, config: DungeonMiniGameConfig) -> list[dict]:
        """Детерминированная (run+config+соль), но непредсказуемая раскладка из кодов лиц."""

        codes = list(config.card_face_codes or [])
        face_seed = int(
            sha256(f"faces:{run_id}:{config.id}:{settings.MINIGAME_BOARD_SALT}".encode()).hexdigest()[:16],
            16,
        )
        random.Random(face_seed).shuffle(codes)
        faces = codes[: config.pairs_count]

        cards = [
            {"id": f"{pair_index}-{copy_index}", "position": 0, "pair_key": face, "face": face}
            for pair_index, face in enumerate(faces)
            for copy_index in range(2)
        ]
        seed = int(
            sha256(f"{run_id}:{config.id}:{config.pairs_count}:{settings.MINIGAME_BOARD_SALT}".encode()).hexdigest()[:16],
            16,
        )
        rng = random.Random(seed)
        rng.shuffle(cards)
        for position, card in enumerate(cards, start=1):
            card["position"] = position
        return cards

    @classmethod
    def _new_state(cls, attempt: DungeonMiniGameAttempt) -> dict:
        return {
            "attempt_id": attempt.id,
            "config_id": attempt.config_id,
            "board": attempt.board,
            "matched_card_ids": [],
            "open_card_id": "",
            "moves_count": 0,
            "matched_pairs_count": 0,
            "expires_at": attempt.expires_at.isoformat(),
            "last_move": None,
        }

    # ------------------------------------------------------------------ finalize

    @classmethod
    def _reward_reduction_seconds(cls, run: DungeonRun, config: DungeonMiniGameConfig, now) -> int:
        """Процент от длительности данжа с абсолютным потолком и клампом по старту."""

        raw = round(run.location.duration_seconds * config.reward_duration_reduction_percent / 100)
        capped = min(raw, config.max_reduction_seconds)
        latest_allowed_end = max(run.started_at, run.ends_at - timezone.timedelta(seconds=capped))
        return max(0, int((run.ends_at - latest_allowed_end).total_seconds()))

    @classmethod
    def _finalize(
        cls,
        attempt: DungeonMiniGameAttempt,
        *,
        success: bool,
        state: dict | None,
        system_error: bool = False,
        now=None,
    ) -> DungeonMiniGameAttempt:
        """Единая точка флаша Redis→Postgres и расчёта ускорения. Чистит Redis-ключ."""

        now = now or timezone.now()
        if state is not None:
            attempt.moves_count = state.get("moves_count", attempt.moves_count)
            attempt.matched_pairs_count = state.get("matched_pairs_count", attempt.matched_pairs_count)
            attempt.matched_card_ids = sorted(state.get("matched_card_ids") or [])
        attempt.open_card_id = ""
        attempt.completed_at = now
        attempt.system_error = system_error

        reduction = 0
        if success:
            attempt.status = DungeonMiniGameAttemptStatus.SUCCESS
            run = DungeonRun.objects.select_for_update().select_related("location").get(pk=attempt.dungeon_run_id)
            if run.status == DungeonRunStatus.IN_PROGRESS:
                reduction = cls._reward_reduction_seconds(run, attempt.config, now)
                if reduction > 0:
                    run.ends_at = run.ends_at - timezone.timedelta(seconds=reduction)
                    run.save(update_fields=["ends_at", "updated_at"])
        else:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED

        attempt.duration_reduction_seconds = reduction
        attempt.save(
            update_fields=[
                "status",
                "completed_at",
                "moves_count",
                "matched_pairs_count",
                "matched_card_ids",
                "open_card_id",
                "duration_reduction_seconds",
                "system_error",
                "updated_at",
            ]
        )
        MiniGameStore.clear(attempt.dungeon_run_id)
        return attempt

    @classmethod
    def _finished_payload(cls, attempt: DungeonMiniGameAttempt, *, matched=None, opened_cards=None) -> dict:
        reward = None
        if attempt.status == DungeonMiniGameAttemptStatus.SUCCESS:
            reward = {"type": "dungeon_time_boost_seconds", "value": attempt.duration_reduction_seconds}
        return {
            "finished": True,
            "matched": matched,
            "attempt": cls.attempt_payload(attempt, include_board=True),
            "opened_cards": opened_cards or [],
            "reward_granted": reward is not None,
            "reward": reward,
        }

    # ------------------------------------------------------------------ commands

    @classmethod
    @transaction.atomic
    def start_attempt(cls, user, run_id: int, *, config_id: int, locale=DEFAULT_LOCALE) -> DungeonMiniGameAttempt:
        """Создаёт попытку выбранной сложности или возвращает активную для забега."""

        run = cls._get_run_for_update(user, run_id, locale)
        if run.status != DungeonRunStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_run_not_active", locale))
        if not run.location.has_mini_game:
            raise serializers.ValidationError(message("mini_game_not_available", locale))

        existing = run.mini_game_attempts.select_related("config").first()
        if existing:
            if existing.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
                raise serializers.ValidationError(message("mini_game_already_finished", locale))
            if existing.expires_at <= timezone.now():
                cls._finalize(existing, success=False, state=MiniGameStore.load(run.id))
                raise serializers.ValidationError(message("mini_game_already_finished", locale))
            # Резюме активной партии: восстановим Redis-стейт из БД при потере ключа.
            if MiniGameStore.load(run.id) is None:
                MiniGameStore.save(run.id, cls._new_state(existing), cls._ttl_seconds(existing.expires_at))
            return existing

        if not config_id:
            raise serializers.ValidationError(message("mini_game_config_required", locale))
        try:
            config = DungeonMiniGameConfig.objects.get(pk=config_id, is_active=True)
        except DungeonMiniGameConfig.DoesNotExist as exc:
            raise serializers.ValidationError(message("mini_game_config_invalid", locale)) from exc
        if len(config.card_face_codes or []) < config.pairs_count:
            raise serializers.ValidationError(message("mini_game_config_invalid", locale))

        now = timezone.now()
        expires_at = now + timezone.timedelta(seconds=config.time_limit_seconds)
        attempt = DungeonMiniGameAttempt.objects.create(
            dungeon_run=run,
            config=config,
            user=user,
            character=run.character,
            started_at=now,
            expires_at=expires_at,
            board=cls._build_board(run.id, config),
        )
        MiniGameStore.save(run.id, cls._new_state(attempt), cls._ttl_seconds(expires_at))
        return attempt

    @classmethod
    @transaction.atomic
    def reveal_card(cls, user, attempt_id: int, *, card_id: str, locale=DEFAULT_LOCALE) -> dict:
        """Открывает первую карточку хода. При потере Redis-ключа — победа по системной ошибке."""

        attempt = cls._load_attempt(user, attempt_id, locale)
        if attempt.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_already_finished", locale))

        run_id = attempt.dungeon_run_id
        with MiniGameStore.lock(run_id, locale):
            state = MiniGameStore.load(run_id)
            if state is None:
                cls._finalize(attempt, success=True, state=None, system_error=True)
                return cls._finished_payload(attempt)

            now = timezone.now()
            if attempt.expires_at <= now:
                cls._finalize(attempt, success=False, state=state)
                return cls._finished_payload(attempt, matched=False)

            cards_by_id = {card["id"]: card for card in state["board"]}
            card = cards_by_id.get(card_id)
            if not card:
                raise serializers.ValidationError(message("mini_game_invalid_move", locale))
            matched_ids = set(state.get("matched_card_ids") or [])
            if card_id in matched_ids:
                raise serializers.ValidationError(message("mini_game_card_already_matched", locale))

            open_card_id = state.get("open_card_id") or ""
            if open_card_id and open_card_id != card_id:
                open_card = cards_by_id.get(open_card_id)
                if open_card:
                    return {"finished": False, "card": cls._card_public(open_card, matched_ids, open_card_id)}

            state["open_card_id"] = card_id
            MiniGameStore.save(run_id, state, cls._ttl_seconds(attempt.expires_at))
            return {"finished": False, "card": cls._card_public(card, matched_ids, card_id)}

    @classmethod
    @transaction.atomic
    def make_move(cls, user, attempt_id: int, *, first_card_id: str, second_card_id: str, locale=DEFAULT_LOCALE) -> dict:
        """Проверяет ход на backend; ускорение — только при честном завершении."""

        attempt = cls._load_attempt(user, attempt_id, locale)
        if attempt.status != DungeonMiniGameAttemptStatus.IN_PROGRESS:
            raise serializers.ValidationError(message("mini_game_already_finished", locale))

        run_id = attempt.dungeon_run_id
        with MiniGameStore.lock(run_id, locale):
            state = MiniGameStore.load(run_id)
            if state is None:
                cls._finalize(attempt, success=True, state=None, system_error=True)
                return cls._finished_payload(attempt)

            now = timezone.now()
            if attempt.expires_at <= now:
                cls._finalize(attempt, success=False, state=state)
                return cls._finished_payload(attempt, matched=False)

            signature = "|".join(sorted([first_card_id, second_card_id]))
            last_move = state.get("last_move")
            if last_move and last_move.get("signature") == signature:
                return last_move["response"]

            if first_card_id == second_card_id:
                raise serializers.ValidationError(message("mini_game_invalid_move", locale))
            open_card_id = state.get("open_card_id") or ""
            if open_card_id and open_card_id != first_card_id:
                raise serializers.ValidationError(message("mini_game_invalid_move", locale))

            cards_by_id = {card["id"]: card for card in state["board"]}
            first_card = cards_by_id.get(first_card_id)
            second_card = cards_by_id.get(second_card_id)
            if not first_card or not second_card:
                raise serializers.ValidationError(message("mini_game_invalid_move", locale))
            matched_ids = set(state.get("matched_card_ids") or [])
            if first_card_id in matched_ids or second_card_id in matched_ids:
                raise serializers.ValidationError(message("mini_game_card_already_matched", locale))

            is_match = first_card["pair_key"] == second_card["pair_key"]
            state["moves_count"] = state.get("moves_count", 0) + 1
            state["open_card_id"] = ""
            if is_match:
                matched_ids.update([first_card_id, second_card_id])
                state["matched_card_ids"] = sorted(matched_ids)
                state["matched_pairs_count"] = state.get("matched_pairs_count", 0) + 1

            solved = is_match and state["matched_pairs_count"] >= attempt.config.pairs_count
            if solved:
                cls._finalize(attempt, success=True, state=state)
                response = cls._finished_payload(
                    attempt,
                    matched=True,
                    opened_cards=[
                        cls._card_public(first_card, set(state["matched_card_ids"]), ""),
                        cls._card_public(second_card, set(state["matched_card_ids"]), ""),
                    ],
                )
                return response

            opened_state = "matched" if is_match else "temporary_open"
            response = {
                "finished": False,
                "matched": is_match,
                "attempt": {
                    "id": attempt.id,
                    "status": attempt.status,
                    "moves_count": state["moves_count"],
                    "matched_pairs_count": state["matched_pairs_count"],
                },
                "opened_cards": [
                    {"id": first_card["id"], "position": first_card["position"], "state": opened_state, "code": first_card["face"]},
                    {"id": second_card["id"], "position": second_card["position"], "state": opened_state, "code": second_card["face"]},
                ],
                "reward_granted": False,
                "reward": None,
            }
            state["last_move"] = {"signature": signature, "response": response}
            MiniGameStore.save(run_id, state, cls._ttl_seconds(attempt.expires_at))
            return response

    # ------------------------------------------------------------------ reconcile

    @staticmethod
    def expire_attempt_if_needed(attempt: DungeonMiniGameAttempt, now=None) -> DungeonMiniGameAttempt:
        """Помечает активную попытку проваленной, если её таймер истёк (для истории)."""

        now = now or timezone.now()
        if attempt.status == DungeonMiniGameAttemptStatus.IN_PROGRESS and attempt.expires_at <= now:
            attempt.status = DungeonMiniGameAttemptStatus.FAILED
            attempt.completed_at = now
            attempt.save(update_fields=["status", "completed_at", "updated_at"])
            MiniGameStore.clear(attempt.dungeon_run_id)
        return attempt
