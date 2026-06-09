from rest_framework import serializers

from .common import localized_name, media_payload, serializer_locale


class HeroIngredientSerializer(serializers.Serializer):
    """Сериализатор строки склада ингредиентов героя для фронта."""

    id = serializers.IntegerField(source="ingredient_id")
    code = serializers.CharField(source="ingredient.code")
    name = serializers.SerializerMethodField()
    category = serializers.CharField(source="ingredient.category")
    count = serializers.IntegerField()
    media = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        """Возвращает локализованное название ингредиента."""

        return localized_name(obj.ingredient, serializer_locale(self.context))

    def get_media(self, obj):
        """Возвращает компактный набор URL иконки ингредиента."""

        return media_payload(obj.ingredient.media, self.context)
