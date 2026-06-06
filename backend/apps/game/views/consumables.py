from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.serializers import HeroPotionSerializer, UsePotionSerializer
from apps.game.services import PotionService


class PotionListView(APIView):
    """API-ручка просмотра склада зелий героя."""

    def get(self, request):
        """Возвращает зелья героя с положительным количеством."""

        locale = request_locale(request)
        potions = PotionService.list_potions(request.user, locale=locale)
        serializer = HeroPotionSerializer(potions, many=True, context={"request": request, "locale": locale})
        return Response(serializer.data)


class PotionUseView(APIView):
    """API-ручка использования зелья лечения героем."""

    throttle_scope = "economy"

    def post(self, request):
        """Использует зелье, лечит героя и возвращает обновлённые HP и остаток."""

        locale = request_locale(request)
        serializer = UsePotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = PotionService.use_potion(
            request.user,
            potion_id=serializer.validated_data["potion_id"],
            quantity=serializer.validated_data["quantity"],
            locale=locale,
        )
        return Response(result)
