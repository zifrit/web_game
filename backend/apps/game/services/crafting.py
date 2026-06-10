from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import Character, CraftRecipe

from .storages import INGREDIENT_STORAGE, POTION_STORAGE


class CraftService:
    """Сервис крафта зелий по предзаполненным рецептам (сложность = рецепт)."""

    @staticmethod
    def _get_character(user, locale=DEFAULT_LOCALE) -> Character:
        """Возвращает героя пользователя или выбрасывает локализованную ошибку."""

        try:
            return user.character
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

    @classmethod
    @transaction.atomic
    def craft_potions(cls, user, recipe_id: int, quantity: int = 1, locale=DEFAULT_LOCALE) -> dict:
        """Транзакционно варит батч зелий: списывает ингредиенты, выдаёт зелья."""

        quantity = max(int(quantity), 1)
        character = cls._get_character(user, locale)
        character = Character.objects.select_for_update().get(pk=character.pk)

        try:
            recipe = (
                CraftRecipe.objects.prefetch_related("ingredients__ingredient")
                .get(pk=recipe_id, is_active=True)
            )
        except CraftRecipe.DoesNotExist as exc:
            raise serializers.ValidationError(message("recipe_not_found", locale)) from exc

        if character.level < recipe.required_hero_level:
            raise serializers.ValidationError(message("hero_level_too_low", locale))

        # Детерминированный порядок захвата блокировок складов (по ingredient_id)
        # исключает дедлоки между параллельными крафтами. Списание идёт по одному;
        # нехватка любого ингредиента бросает ошибку и откатывает транзакцию целиком.
        recipe_ingredients = sorted(recipe.ingredients.all(), key=lambda ri: ri.ingredient_id)
        for ri in recipe_ingredients:
            INGREDIENT_STORAGE.withdraw(
                character,
                ri.ingredient_id,
                ri.quantity * quantity,
                insufficient_message="not_enough_ingredients",
                locale=locale,
            )

        pot = POTION_STORAGE.deposit(character, recipe.potion_id, quantity)

        return {
            "recipe_id": recipe.id,
            "potion_id": recipe.potion_id,
            "potion_code": recipe.potion.code,
            "crafted": quantity,
            "potion_count": pot.count,
        }

    @classmethod
    def list_recipes(cls, user, locale=DEFAULT_LOCALE):
        """Возвращает определения активных рецептов крафта с зельем и ингредиентами."""

        return (
            CraftRecipe.objects.filter(is_active=True)
            .select_related("potion", "potion__media")
            .prefetch_related("ingredients__ingredient__media")
            .order_by("sort_order")
        )
