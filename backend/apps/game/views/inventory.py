from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import Character, UserItem
from apps.game.serializers import InventorySerializer, UserItemDetailSerializer
from apps.game.services import InventoryService


class InventoryView(APIView):
    """API-ручка просмотра инвентаря и экипировки героя."""

    def get(self, request):
        """Возвращает экипировку, сводку характеристик и страницу предметов."""

        character = get_object_or_404(
            Character.objects.select_related("character_class", "user").prefetch_related("equipped_items__template__media"),
            user=request.user,
        )
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 24))
        except (TypeError, ValueError):
            page_size = 24
        page_size = min(max(page_size, 1), 24)
        return Response(InventorySerializer.render(character, page=page, page_size=page_size, locale=request_locale(request)))


class InventoryItemDetailView(APIView):
    """API-ручка детальной карточки предмета пользователя."""

    def get(self, request, item_id):
        """Возвращает характеристики, прочность, медиа и возможность экипировки."""

        item = get_object_or_404(UserItem.objects.select_related("template__media"), pk=item_id, owner_user=request.user)
        character = getattr(request.user, "character", None)
        return Response(UserItemDetailSerializer(item, context={"request": request, "character": character}).data)


class InventoryItemRepairPreviewView(APIView):
    """API-ручка предварительного расчёта ремонта предмета."""

    def get(self, request, item_id):
        """Возвращает стоимость ремонта и возможность оплатить его текущим балансом."""

        item = get_object_or_404(UserItem, pk=item_id, owner_user=request.user)
        return Response(InventoryService.repair_preview(request.user, item))


class InventoryItemRepairView(APIView):
    """API-ручка ремонта предмета пользователя."""

    def post(self, request, item_id):
        """Ремонтирует предмет до максимальной прочности и списывает медные монеты."""

        item, cost, remaining_money = InventoryService.repair(request.user, item_id, locale=request_locale(request))
        return Response(
            {
                "success": True,
                "repair_cost_copper": cost,
                "durability": {"current": item.durability_current, "max": item.durability_max},
                "remaining_money_copper": remaining_money,
            }
        )


class InventoryItemEquipView(APIView):
    """API-ручка экипировки предмета на героя."""

    def post(self, request, item_id):
        """Экипирует предмет в соответствующий слот и возвращает новую силу героя."""

        item, new_power = InventoryService.equip(request.user, item_id, locale=request_locale(request))
        return Response({"success": True, "equipped_slot": item.slot, "item_id": item.id, "new_power": new_power})


class InventoryItemUnequipView(APIView):
    """API-ручка снятия предмета с героя."""

    def post(self, request, item_id):
        """Снимает предмет, если он экипирован текущим героем, и возвращает новую силу."""

        new_power = InventoryService.unequip(request.user, item_id, locale=request_locale(request))
        return Response({"success": True, "new_power": new_power})
