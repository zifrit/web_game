from __future__ import annotations

import random

from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    DungeonIngredientDrop,
    DungeonLocation,
    HeroIngredientStorage,
)


class IngredientService:
    """Сервис склада ингредиентов героя: начисление и просмотр."""

    @staticmethod
    def _get_character(user, locale=DEFAULT_LOCALE) -> Character:
        """Возвращает героя пользователя или выбрасывает локализованную ошибку."""

        try:
            return user.character
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

    @classmethod
    def list_ingredients(cls, user, locale=DEFAULT_LOCALE):
        """Возвращает склад ингредиентов героя с положительным количеством."""

        character = cls._get_character(user, locale)
        return (
            HeroIngredientStorage.objects.filter(character=character, count__gt=0)
            .select_related("ingredient", "ingredient__media")
            .order_by("ingredient__sort_order")
        )


class IngredientDropService:
    """Сервис броска дропа ингредиентов за один забег в локацию."""

    @staticmethod
    def roll_drops(location: DungeonLocation) -> list[dict]:
        """Делает независимый бросок шанса по каждой записи дроп-таблицы локации."""

        result: list[dict] = []
        for drop in location.ingredient_drops.all():
            if random.uniform(0, 100) <= drop.chance_percent:
                quantity = random.randint(drop.min_quantity, drop.max_quantity)
                result.append({"ingredient_id": drop.ingredient_id, "quantity": quantity})
        return result
