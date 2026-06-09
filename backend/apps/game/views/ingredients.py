from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.serializers import HeroIngredientSerializer
from apps.game.services import IngredientService


class IngredientListView(APIView):
    """API-ручка просмотра склада ингредиентов героя."""

    def get(self, request):
        """Возвращает ингредиенты героя с положительным количеством."""

        locale = request_locale(request)
        ingredients = IngredientService.list_ingredients(request.user, locale=locale)
        serializer = HeroIngredientSerializer(
            ingredients, many=True, context={"request": request, "locale": locale}
        )
        return Response(serializer.data)
