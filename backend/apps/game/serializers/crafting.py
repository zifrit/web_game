from rest_framework import serializers

from .common import localized_name, media_payload, serializer_locale


class CraftRecipeIngredientSerializer(serializers.Serializer):
    """Сериализатор слота рецепта: ингредиент и количество на одно зелье."""

    ingredient_id = serializers.IntegerField()
    code = serializers.CharField(source="ingredient.code")
    name = serializers.SerializerMethodField()
    quantity = serializers.IntegerField()
    media = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        """Возвращает локализованное название ингредиента."""

        return localized_name(obj.ingredient, serializer_locale(self.context))

    def get_media(self, obj):
        """Возвращает компактный набор URL иконки ингредиента."""

        return media_payload(obj.ingredient.media, self.context)


class CraftRecipePotionSerializer(serializers.Serializer):
    """Сериализатор готового зелья рецепта для панели крафта."""

    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.SerializerMethodField()
    heal_percent = serializers.IntegerField()
    media = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        """Возвращает локализованное название зелья."""

        return localized_name(obj, serializer_locale(self.context))

    def get_media(self, obj):
        """Возвращает компактный набор URL иконки зелья."""

        return media_payload(obj.media, self.context)


class CraftRecipeSerializer(serializers.Serializer):
    """Сериализатор определения рецепта крафта для фронта."""

    id = serializers.IntegerField()
    code = serializers.CharField()
    difficulty = serializers.CharField()
    required_hero_level = serializers.IntegerField()
    potion = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()

    def get_potion(self, obj):
        """Возвращает вложенное готовое зелье рецепта."""

        return CraftRecipePotionSerializer(obj.potion, context=self.context).data

    def get_ingredients(self, obj):
        """Возвращает список предзаполненных слотов рецепта."""

        return CraftRecipeIngredientSerializer(
            obj.ingredients.all(), many=True, context=self.context
        ).data


class CraftPotionSerializer(serializers.Serializer):
    """Сериализатор запроса крафта батча зелий."""

    recipe_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)
