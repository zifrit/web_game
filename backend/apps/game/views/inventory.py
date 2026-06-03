from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import Character, UserItem
from apps.game.serializers import InventorySerializer, UserItemDetailSerializer
from apps.game.services import InventoryService


def request_item_ids(request) -> list[int]:
    """Читает список id предметов из JSON body."""

    item_ids = request.data.get("item_ids", [])
    return item_ids if isinstance(item_ids, list) else []


class InventoryView(APIView):
    """API-ручка просмотра инвентаря и экипировки героя."""

    def get(self, request):
        """Возвращает экипировку, сводку характеристик и страницу предметов."""

        character = get_object_or_404(
            Character.objects.select_related("character_class", "user").prefetch_related("equipped_items__template__media"),
            user=request.user,
        )
        self.check_object_permissions(request, character)
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 24))
        except (TypeError, ValueError):
            page_size = 24
        page_size = min(max(page_size, 1), 24)
        return Response(
            InventorySerializer.render(
                character,
                page=page,
                page_size=page_size,
                locale=request_locale(request),
                request=request,
            )
        )


class InventoryItemDetailView(APIView):
    """API-ручка детальной карточки предмета пользователя."""

    def get(self, request, item_id):
        """Возвращает характеристики, прочность, медиа и возможность экипировки."""

        item = get_object_or_404(UserItem.objects.select_related("template__media"), pk=item_id, owner_user=request.user)
        self.check_object_permissions(request, item)
        character = Character.objects.select_related("character_class", "avatar_media").get(user=request.user)
        return Response(UserItemDetailSerializer(item, context={"request": request, "character": character}).data)


class InventoryItemRepairPreviewView(APIView):
    """API-ручка предварительного расчёта ремонта предмета."""

    def get(self, request, item_id):
        """Возвращает стоимость ремонта одного предмета через массовую логику."""

        return Response(InventoryService.repair_preview(request.user, [item_id]))


class InventoryItemRepairView(APIView):
    """API-ручка ремонта предмета пользователя."""

    throttle_scope = "inventory_write"

    def post(self, request, item_id):
        """Ремонтирует один предмет через массовую логику и списывает медные монеты."""

        result = InventoryService.repair_items(request.user, [item_id], locale=request_locale(request))
        item = get_object_or_404(UserItem, pk=item_id, owner_user=request.user)
        self.check_object_permissions(request, item)
        result["durability"] = {"current": item.durability_current, "max": item.durability_max}
        return Response(result)


class InventoryItemsRepairPreviewView(APIView):
    """API-ручка предварительного расчёта массового ремонта предметов."""

    def post(self, request):
        """Возвращает стоимость ремонта выбранных предметов."""

        return Response(InventoryService.repair_preview(request.user, request_item_ids(request)))


class InventoryItemsRepairView(APIView):
    """API-ручка массового ремонта предметов пользователя."""

    throttle_scope = "inventory_write"

    def post(self, request):
        """Ремонтирует выбранные предметы до максимальной прочности."""

        return Response(InventoryService.repair_items(request.user, request_item_ids(request), locale=request_locale(request)))


class InventoryItemsDestroyPreviewView(APIView):
    """API-ручка предварительного расчёта уничтожения предметов."""

    def post(self, request):
        """Возвращает сумму возврата за уничтожение выбранных предметов."""

        return Response(InventoryService.destroy_preview(request.user, request_item_ids(request)))


class InventoryItemsDestroyView(APIView):
    """API-ручка массового уничтожения предметов пользователя."""

    throttle_scope = "inventory_write"

    def post(self, request):
        """Удаляет выбранные предметы и начисляет возврат."""

        return Response(InventoryService.destroy_items(request.user, request_item_ids(request), locale=request_locale(request)))


class InventoryItemEquipView(APIView):
    """API-ручка экипировки предмета на героя."""

    throttle_scope = "inventory_write"

    def post(self, request, item_id):
        """Экипирует предмет в соответствующий слот и возвращает новую силу героя."""

        locale = request_locale(request)
        item, replaced_item, character = InventoryService.equip(request.user, item_id, locale=locale)
        character = Character.objects.select_related("character_class", "user").prefetch_related("equipped_items__template__media").get(pk=character.pk)
        return Response(
            InventorySerializer.render_mutation_response(
                character,
                item,
                replaced_item=replaced_item,
                locale=locale,
                request=request,
            )
        )


class InventoryItemUnequipView(APIView):
    """API-ручка снятия предмета с героя."""

    throttle_scope = "inventory_write"

    def post(self, request, item_id):
        """Снимает предмет, если он экипирован текущим героем, и возвращает новую силу."""

        locale = request_locale(request)
        item, character = InventoryService.unequip(request.user, item_id, locale=locale)
        character = Character.objects.select_related("character_class", "user").prefetch_related("equipped_items__template__media").get(pk=character.pk)
        return Response(InventorySerializer.render_mutation_response(character, item, locale=locale, request=request))
