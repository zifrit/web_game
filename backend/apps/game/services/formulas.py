from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_EVEN

from apps.game.models import Character, UserItem

from .config import GameConfigService


STAT_KEYS = ("health", "attack", "defense", "critical_chance", "evasion")


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

        from .balance import GameBalanceService

        missing = max(item.durability_max - item.durability_current, 0)
        multiplier = Decimal(str(GameBalanceService.rarity_config(item.rarity)["economy_multiplier"]))
        return int((multiplier * Decimal(missing) * Decimal("2.5")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    @staticmethod
    def destroy_refund(item: UserItem) -> int:
        """Считает возврат денег за уничтожение предмета."""

        from .balance import GameBalanceService

        multiplier = Decimal(str(GameBalanceService.rarity_config(item.rarity)["economy_multiplier"]))
        return int((multiplier * Decimal(item.durability_current) * Decimal("2")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    @staticmethod
    def durability_loss(is_success: bool) -> int:
        """Возвращает потерю прочности экипировки для успешного или провального забега."""

        config = GameConfigService.get_config("durability_loss_config")
        return int(config["success" if is_success else "failure"])
