from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_EVEN

from django.utils import timezone

from apps.game.models import Character, UserItem

from .config import GameConfigService


STAT_KEYS = ("max_hp", "intellect", "attack", "defense", "critical_chance", "evasion")
POWER_STAT_KEYS = ("intellect", "attack", "defense", "critical_chance", "evasion")


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
        max_hp_per_level = profile.get("max_hp_per_level", profile.get("health_per_level", 5))
        stats = {
            "max_hp": float(max_hp_per_level) * levels_gained,
            "intellect": float(profile.get("intellect_per_level", 1)) * levels_gained,
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
    def intrinsic_character_stats(cls, character: Character) -> dict[str, float]:
        """Считает собственные характеристики героя от класса и уровня без экипировки."""

        character_class = character.character_class
        stats = {
            "max_hp": float(character_class.start_max_hp),
            "intellect": float(character_class.start_intellect),
            "attack": float(character_class.start_attack),
            "defense": float(character_class.start_defense),
            "critical_chance": float(character_class.start_critical_chance),
            "evasion": float(character_class.start_evasion),
        }
        for key, value in cls.level_growth_stats(character).items():
            stats[key] += value
        return stats

    @classmethod
    def apply_level_stats(cls, character: Character) -> dict[str, float]:
        """Обновляет сохранённые характеристики героя по текущему уровню."""

        stats = cls.intrinsic_character_stats(character)
        character.max_hp = int(round(stats["max_hp"]))
        character.intellect = int(round(stats["intellect"]))
        character.attack = int(round(stats["attack"]))
        character.defense = int(round(stats["defense"]))
        character.critical_chance = stats["critical_chance"]
        character.evasion = stats["evasion"]
        return {
            "max_hp": float(character.max_hp),
            "intellect": float(character.intellect),
            "attack": float(character.attack),
            "defense": float(character.defense),
            "critical_chance": character.critical_chance,
            "evasion": character.evasion,
        }

    @classmethod
    def character_stats(cls, character: Character, include_equipment: bool = True) -> dict[str, float]:
        """Собирает итоговые характеристики героя с уровнем, экипировкой и капами."""

        stats = {
            "max_hp": float(character.max_hp),
            "intellect": float(character.intellect),
            "attack": float(character.attack),
            "defense": float(character.defense),
            "critical_chance": float(character.critical_chance),
            "evasion": float(character.evasion),
        }
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
        return round(sum(float(stats.get(key, 0)) * float(config.get(key, 0)) for key in POWER_STAT_KEYS), 2)

    @classmethod
    def refresh_power_cache(cls, character: Character) -> float:
        """Пересчитывает силу героя и точечно сохраняет её кэш в БД."""

        power = cls.character_stats(character)["power"]
        character.power_cached = power
        character.power_updated_at = timezone.now()
        character.save(update_fields=["power_cached", "power_updated_at", "updated_at"])
        return power

    @staticmethod
    def success_chance(character_power: float, required_power: float, hp_penalty: float = 0.0) -> float:
        """Считает шанс успеха забега по силе героя, требуемой силе и штрафу за низкое HP."""

        config = GameConfigService.get_config("success_chance_config")
        raw = float(config["base"]) + (character_power - required_power) * float(config["power_delta_multiplier"]) - float(hp_penalty)
        return round(max(float(config["min"]), min(float(config["max"]), raw)), 2)

    @staticmethod
    def hp_percent(current_hp: int, max_hp: int) -> float:
        """Возвращает процент текущего HP от максимума (0 при нулевом максимуме)."""

        if max_hp <= 0:
            return 0.0
        return current_hp / max_hp * 100

    @classmethod
    def hp_success_penalty(cls, current_hp: int, max_hp: int) -> float:
        """Возвращает штраф к шансу успеха за низкое HP по порогам из конфига."""

        config = GameConfigService.get_config("hp_penalty_config")
        pct = cls.hp_percent(current_hp, max_hp)
        if pct >= float(config["safe_threshold_percent"]):
            return 0.0
        if pct >= float(config["mid_threshold_percent"]):
            return float(config["mid_penalty"])
        return float(config["low_penalty"])

    @classmethod
    def is_hp_too_low_to_start(cls, current_hp: int, max_hp: int) -> bool:
        """Проверяет, что HP ниже порога, при котором обычный данж нельзя стартовать."""

        config = GameConfigService.get_config("hp_penalty_config")
        return cls.hp_percent(current_hp, max_hp) < float(config["block_below_percent"])

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

    @staticmethod
    def hp_loss(max_hp: int, loss_percent: float) -> int:
        """Считает абсолютную потерю HP от максимума по проценту (минимум 1, округление вверх)."""

        if loss_percent <= 0 or max_hp <= 0:
            return 0
        return max(1, math.ceil(max_hp * float(loss_percent) / 100))

    @classmethod
    def clamp_current_hp(cls, character: Character) -> int:
        """Ограничивает current_hp текущим максимумом HP (с учётом экипировки) и сохраняет при изменении."""

        total_max_hp = int(cls.character_stats(character)["max_hp"])
        if character.current_hp > total_max_hp:
            character.current_hp = total_max_hp
            character.save(update_fields=["current_hp", "updated_at"])
        return character.current_hp
