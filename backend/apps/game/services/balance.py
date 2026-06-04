from __future__ import annotations

from typing import Any

from apps.game.models import Character, CharacterClass

from .config import rarity_config
from .formulas import GameFormulaService


class GameBalanceService:
    """Сервис базового баланса: создание героя и параметры редкостей."""

    @staticmethod
    def create_character(user, name: str, character_class: CharacterClass) -> Character:
        """Создаёт героя с начальными статами класса и кэширует его силу."""

        character = Character.objects.create(
            user=user,
            name=name,
            character_class=character_class,
            base_health=character_class.start_health,
            base_attack=character_class.start_attack,
            base_defense=character_class.start_defense,
            base_critical_chance=character_class.start_critical_chance,
            base_evasion=character_class.start_evasion,
        )
        GameFormulaService.refresh_power_cache(character)
        return character

    @staticmethod
    def rarity_config(rarity: str) -> dict[str, Any]:
        """Возвращает параметры редкости из БД или встроенного набора по умолчанию."""

        return rarity_config(rarity)
