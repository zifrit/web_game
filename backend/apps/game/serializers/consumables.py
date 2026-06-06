from rest_framework import serializers

from apps.game.models import HeroPotionStorage

from .common import localized_name, media_payload, serializer_locale


class HeroPotionSerializer(serializers.Serializer):
    """Сериализатор строки склада зелий героя для фронта."""

    id = serializers.IntegerField(source="potion_id")
    code = serializers.CharField(source="potion.code")
    name = serializers.SerializerMethodField()
    heal_percent = serializers.IntegerField(source="potion.heal_percent")
    count = serializers.IntegerField()
    media = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        """Возвращает локализованное название зелья."""

        return localized_name(obj.potion, serializer_locale(self.context))

    def get_media(self, obj):
        """Возвращает компактный набор URL иконки зелья."""

        return media_payload(obj.potion.media, self.context)


class UsePotionSerializer(serializers.Serializer):
    """Сериализатор запроса использования зелья."""

    potion_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)
