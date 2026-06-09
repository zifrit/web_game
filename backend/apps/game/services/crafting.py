from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    CraftRecipe,
    HeroIngredientStorage,
    HeroPotionStorage,
)


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

        recipe_ingredients = list(recipe.ingredients.all())
        storages = {
            s.ingredient_id: s
            for s in HeroIngredientStorage.objects.select_for_update().filter(
                character=character,
                ingredient_id__in=[ri.ingredient_id for ri in recipe_ingredients],
            )
        }

        for ri in recipe_ingredients:
            need = ri.quantity * quantity
            have = storages.get(ri.ingredient_id)
            if have is None or have.count < need:
                raise serializers.ValidationError(message("not_enough_ingredients", locale))

        for ri in recipe_ingredients:
            storage = storages[ri.ingredient_id]
            storage.count -= ri.quantity * quantity
            storage.save(update_fields=["count", "updated_at"])

        pot, _ = HeroPotionStorage.objects.select_for_update().get_or_create(
            character=character,
            potion=recipe.potion,
            defaults={"count": 0},
        )
        pot.count += quantity
        pot.save(update_fields=["count", "updated_at"])

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
