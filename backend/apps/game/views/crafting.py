from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.serializers import CraftPotionSerializer, CraftRecipeSerializer
from apps.game.services import CraftService


class CraftRecipeListView(APIView):
    """API-ручка списка активных рецептов крафта."""

    def get(self, request):
        """Возвращает определения рецептов с зельем и предзаполненными ингредиентами."""

        locale = request_locale(request)
        recipes = CraftService.list_recipes(request.user, locale=locale)
        serializer = CraftRecipeSerializer(
            recipes, many=True, context={"request": request, "locale": locale}
        )
        return Response(serializer.data)


class CraftPotionView(APIView):
    """API-ручка крафта батча зелий по рецепту."""

    throttle_scope = "economy"

    def post(self, request):
        """Списывает ингредиенты, выдаёт зелья и возвращает итог крафта."""

        locale = request_locale(request)
        serializer = CraftPotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = CraftService.craft_potions(
            request.user,
            recipe_id=serializer.validated_data["recipe_id"],
            quantity=serializer.validated_data["quantity"],
            locale=locale,
        )
        return Response(result)
