"""Хранилище live-стейта memory-pairs мини-игры в Redis (django cache, db 1).

Пока партия идёт, истина живёт здесь; в Postgres попадает только финальный
снимок. Ключ привязан к забегу (одна попытка на забег).
"""

from __future__ import annotations

from contextlib import contextmanager

from django.core.cache import cache
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message

STATE_PREFIX = "minigame:state:"
LOCK_PREFIX = "minigame:lock:"
LOCK_TIMEOUT_SECONDS = 5


class MiniGameStore:
    """Тонкая обёртка над django cache для стейта и лока партии по `run_id`."""

    @staticmethod
    def _state_key(run_id: int) -> str:
        return f"{STATE_PREFIX}{run_id}"

    @staticmethod
    def _lock_key(run_id: int) -> str:
        return f"{LOCK_PREFIX}{run_id}"

    @classmethod
    def load(cls, run_id: int) -> dict | None:
        """Возвращает стейт партии или None, если ключ отсутствует/истёк."""

        return cache.get(cls._state_key(run_id))

    @classmethod
    def save(cls, run_id: int, state: dict, ttl_seconds: int) -> None:
        """Сохраняет стейт с TTL (секунды до истечения попытки + буфер)."""

        cache.set(cls._state_key(run_id), state, max(1, ttl_seconds))

    @classmethod
    def clear(cls, run_id: int) -> None:
        """Удаляет стейт партии (после финала)."""

        cache.delete(cls._state_key(run_id))

    @classmethod
    @contextmanager
    def lock(cls, run_id: int, locale=DEFAULT_LOCALE):
        """Короткий лок вокруг read-modify-write хода; иначе `mini_game_busy`."""

        key = cls._lock_key(run_id)
        if not cache.add(key, "1", LOCK_TIMEOUT_SECONDS):
            raise serializers.ValidationError(message("mini_game_busy", locale))
        try:
            yield
        finally:
            cache.delete(key)
