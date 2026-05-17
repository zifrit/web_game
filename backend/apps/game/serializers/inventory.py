from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE
from apps.game.models import UserItem
from apps.game.services import InventoryService

from .common import localized_item_name, media_payload, serializer_locale


class UserItemSummarySerializer(serializers.ModelSerializer):
    """Краткий сериализатор предмета для сетки инвентаря и экипировки."""

    name = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()
    is_broken = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserItem
        fields = ["id", "name", "icon_url", "slot", "rarity", "is_broken"]

    def get_name(self, obj):
        """Возвращает локализованное название предмета с учётом редкости."""

        return localized_item_name(obj, serializer_locale(self.context))

    def get_icon_url(self, obj):
        """Возвращает URL иконки шаблона предмета."""

        return obj.template.media.icon_url if obj.template.media else ""


class UserItemDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор предмета пользователя."""

    name = serializers.SerializerMethodField()
    durability = serializers.SerializerMethodField()
    is_equipped = serializers.SerializerMethodField()
    is_broken = serializers.BooleanField(read_only=True)
    can_equip = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    class Meta:
        model = UserItem
        fields = [
            "id",
            "name",
            "slot",
            "item_type",
            "rarity",
            "item_level",
            "stats",
            "durability",
            "is_equipped",
            "is_broken",
            "can_equip",
            "media",
        ]

    def get_durability(self, obj):
        """Возвращает текущую и максимальную прочность предмета."""

        return {"current": obj.durability_current, "max": obj.durability_max}

    def get_name(self, obj):
        """Возвращает локализованное название предмета."""

        return localized_item_name(obj, serializer_locale(self.context))

    def get_is_equipped(self, obj):
        """Показывает, экипирован ли предмет текущим героем."""

        character = self.context.get("character")
        return bool(character and obj.equipped_character_id == character.id)

    def get_can_equip(self, obj):
        """Показывает, может ли текущий герой экипировать предмет."""

        character = self.context.get("character")
        return bool(character and InventoryService.can_equip(obj, character))

    def get_media(self, obj):
        """Возвращает набор URL медиа для шаблона предмета."""

        return media_payload(obj.template.media)


class InventorySerializer:
    """Рендер полного ответа инвентаря с экипировкой и пагинацией."""

    @staticmethod
    def render(character, page=1, page_size=24, locale=DEFAULT_LOCALE):
        """Собирает экипировку, предметы текущей страницы и метаданные пагинации."""

        equipment = {slot: None for slot in ["weapon", "helmet", "armor", "boots", "ring"]}
        for item in character.equipped_items.all():
            equipment[item.slot] = UserItemSummarySerializer(item, context={"locale": locale}).data
        items_qs = UserItem.objects.filter(owner_user=character.user).select_related("template__media")
        items_count = items_qs.count()
        offset = (page - 1) * page_size
        items = items_qs[offset : offset + page_size]
        total_pages = (items_count + page_size - 1) // page_size
        return {
            "equipment_summary": InventoryService.equipment_summary(character),
            "equipped": equipment,
            "items_count": items_count,
            "slots_limit": None,
            "free_slots": None,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": items_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "items": UserItemSummarySerializer(items, many=True, context={"locale": locale}).data,
        }
