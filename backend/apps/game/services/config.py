from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from apps.game.models import GameConfig, RarityConfig

from .ranks import MAX_RANK_LEVEL, RANKS


DEFAULT_CONFIGS: dict[str, dict[str, Any]] = {
    "power_formula_config": {
        "intellect": 1.5,
        "attack": 2.0,
        "defense": 1.7,
        "critical_chance": 1.5,
        "evasion": 1.5,
    },
    "success_chance_config": {"base": 75, "power_delta_multiplier": 0.6, "min": 1, "max": 100},
    "repair_cost_config": {"copper_per_durability": 10},
    "experience_curve_config": {"base": 100, "exponent": 1.5, "max_level": MAX_RANK_LEVEL},
    "stat_caps": {"critical_chance": 60, "evasion": 50},
    "durability_loss_config": {"success": 1, "failure": 5},
    "hp_penalty_config": {
        "safe_threshold_percent": 50,
        "mid_threshold_percent": 30,
        "block_below_percent": 10,
        "mid_penalty": 5,
        "low_penalty": 15,
    },
}

DEFAULT_RARITIES = {
    rank.key: {
        "name": rank.label,
        "stat_multiplier": rank.stat_multiplier,
        "economy_multiplier": Decimal(rank.economy_multiplier),
        "min_item_level": rank.min_level,
        "max_item_level": rank.max_level,
        "min_stats_count": rank.min_stats_count,
        "max_stats_count": rank.max_stats_count,
    }
    for rank in RANKS
}


_GAME_CONFIG_CACHE: dict[str, dict[str, Any]] = {}
_RARITY_CONFIG_CACHE: dict[str, RarityConfig] | None = None


def _invalidate_game_config_cache(*_args, **_kwargs) -> None:
    """Сбрасывает кэш игровых настроек при изменении или удалении записей."""

    _GAME_CONFIG_CACHE.clear()


def _invalidate_rarity_config_cache(*_args, **_kwargs) -> None:
    """Сбрасывает кэш конфигурации редкостей при изменении записей."""

    global _RARITY_CONFIG_CACHE
    _RARITY_CONFIG_CACHE = None


class RarityConfigCache:
    """Кэш активных RarityConfig в памяти процесса с инвалидацией по сигналу."""

    @staticmethod
    def all_active() -> dict[str, RarityConfig]:
        """Возвращает словарь активных редкостей по ключу, кэшированный в памяти."""

        global _RARITY_CONFIG_CACHE
        if _RARITY_CONFIG_CACHE is None:
            _RARITY_CONFIG_CACHE = {
                rc.key: rc for rc in RarityConfig.objects.filter(is_active=True)
            }
        return _RARITY_CONFIG_CACHE

    @staticmethod
    def all_ordered() -> list[RarityConfig]:
        """Возвращает активные редкости, отсортированные по sort_order."""

        return sorted(RarityConfigCache.all_active().values(), key=lambda rc: rc.sort_order)


class GameConfigService:
    """Сервис чтения игровых настроек с дефолтами и переопределениями из БД."""

    @staticmethod
    def get_config(key: str) -> dict[str, Any]:
        """Возвращает активную настройку по ключу, объединяя БД с DEFAULT_CONFIGS."""

        cached = _GAME_CONFIG_CACHE.get(key)
        if cached is not None:
            return cached.copy()
        value = DEFAULT_CONFIGS.get(key, {}).copy()
        db_config = GameConfig.objects.filter(key=key, is_active=True).first()
        if db_config and isinstance(db_config.value, dict):
            value.update(db_config.value)
        _GAME_CONFIG_CACHE[key] = value.copy()
        return value


def rarity_config(rarity: str) -> dict[str, Any]:
    """Возвращает параметры редкости из БД или встроенного набора по умолчанию."""

    configs = RarityConfigCache.all_active()
    db_config = configs.get(rarity)
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
