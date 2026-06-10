from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import Character, HeroPotionStorage

from .formulas import GameFormulaService
from .storages import POTION_STORAGE


class PotionService:
    """Сервис использования зелий лечения и просмотра склада зелий героя."""

    @staticmethod
    def _get_character(user, locale=DEFAULT_LOCALE) -> Character:
        """Возвращает героя пользователя или выбрасывает локализованную ошибку."""

        try:
            return user.character
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

    @classmethod
    @transaction.atomic
    def use_potion(cls, user, potion_id: int, quantity: int = 1, locale=DEFAULT_LOCALE) -> dict:
        """Транзакционно лечит героя зельями, списывает их со склада и возвращает итог."""

        quantity = max(int(quantity), 1)
        character = cls._get_character(user, locale)
        character = (
            Character.objects.select_for_update()
            .select_related("character_class")
            .get(pk=character.pk)
        )
        max_hp = int(GameFormulaService.character_stats(character)["max_hp"])
        if character.current_hp >= max_hp:
            raise serializers.ValidationError(message("hp_already_full", locale))

        storage = POTION_STORAGE.withdraw(
            character,
            potion_id,
            quantity,
            insufficient_message="not_enough_potions",
            missing_message="potion_not_owned",
            locale=locale,
        )

        heal_per = GameFormulaService.potion_heal(max_hp, storage.potion.heal_percent)
        total_heal = heal_per * quantity
        new_hp = min(max_hp, character.current_hp + total_heal)
        healed = new_hp - character.current_hp

        character.current_hp = new_hp
        character.save(update_fields=["current_hp", "updated_at"])

        return {
            "potion_id": potion_id,
            "used": quantity,
            "healed": healed,
            "current_hp": new_hp,
            "max_hp": max_hp,
            "remaining": storage.count,
        }

    @classmethod
    def list_potions(cls, user, locale=DEFAULT_LOCALE):
        """Возвращает склад зелий героя с положительным количеством."""

        character = cls._get_character(user, locale)
        return (
            HeroPotionStorage.objects.filter(character=character, count__gt=0)
            .select_related("potion", "potion__media")
            .order_by("potion__sort_order")
        )
