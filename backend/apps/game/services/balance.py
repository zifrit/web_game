from __future__ import annotations

from typing import Any

from apps.game.models import Character, CharacterClass, MediaAsset

from .config import rarity_config
from .formulas import GameFormulaService


class GameBalanceService:
    """Сервис базового баланса: создание героя и параметры редкостей."""

    @staticmethod
    def create_character(
        user,
        name: str,
        character_class: CharacterClass,
        gender: str = Character.Gender.MALE,
        avatar_media: MediaAsset | None = None,
    ) -> Character:
        """Создаёт героя с начальными статами класса и кэширует его силу."""

        character = Character.objects.create(
            user=user,
            name=name,
            character_class=character_class,
            gender=gender,
            avatar_media=avatar_media,
            max_hp=character_class.start_max_hp,
            current_hp=character_class.start_max_hp,
            intellect=character_class.start_intellect,
            attack=character_class.start_attack,
            defense=character_class.start_defense,
            critical_chance=character_class.start_critical_chance,
            evasion=character_class.start_evasion,
        )
        GameFormulaService.refresh_power_cache(character)
        return character

    @staticmethod
    def rarity_config(rarity: str) -> dict[str, Any]:
        """Возвращает параметры редкости из БД или встроенного набора по умолчанию."""

        return rarity_config(rarity)
