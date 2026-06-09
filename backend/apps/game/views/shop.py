from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import ShopOffer, ShopPurchase
from apps.game.serializers import (
    BuyShopOfferRequestSerializer,
    ShopOfferDetailSerializer,
    ShopOfferListSerializer,
    ShopPurchaseSerializer,
)
from apps.game.services import ShopService


class ShopOfferListView(APIView):
    """API-ручка списка активных предложений магазина (без возможных наград)."""

    def get(self, request):
        """Возвращает лёгкий список активных предложений по порядку сортировки."""

        offers = ShopOffer.objects.filter(is_active=True).select_related("media").order_by("sort_order", "id")
        serializer = ShopOfferListSerializer(
            offers, many=True, context={"request": request, "locale": request_locale(request)}
        )
        return Response(serializer.data)


class ShopOfferDetailView(APIView):
    """API-ручка детальной карточки предложения с возможными наградами."""

    def get(self, request, pk):
        """Возвращает предложение с шансами наград и процентами."""

        offer = get_object_or_404(
            ShopOffer.objects.filter(is_active=True)
            .select_related("media")
            .prefetch_related(
                "ingredient_entries__ingredient_template__media",
                "potion_entries__potion_template__media",
                "item_entries__item_template__media",
            ),
            pk=pk,
        )
        serializer = ShopOfferDetailSerializer(
            offer, context={"request": request, "locale": request_locale(request)}
        )
        return Response(serializer.data)


class BuyShopOfferView(APIView):
    """API-ручка покупки предложения магазина выбранной валютой."""

    throttle_scope = "economy"

    def post(self, request, pk):
        """Совершает покупку, выдаёт награды и возвращает обновлённые балансы."""

        locale = request_locale(request)
        request_serializer = BuyShopOfferRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        result = ShopService.buy_offer(
            user=request.user,
            offer_id=pk,
            purchase_count=request_serializer.validated_data["purchase_count"],
            payment_currency=request_serializer.validated_data["payment_currency"],
            locale=locale,
        )

        purchase_data = ShopPurchaseSerializer(
            result["purchase"], context={"request": request, "locale": locale}
        ).data
        return Response({"purchase": purchase_data, "balances": result["balances"]})


class ShopPurchasesView(APIView):
    """API-ручка истории покупок текущего пользователя."""

    def get(self, request):
        """Возвращает покупки только текущего пользователя, новые сверху."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        purchases = (
            ShopPurchase.objects.filter(user=request.user)
            .select_related("offer")
            .order_by("-created_at", "-id")[:limit]
        )
        serializer = ShopPurchaseSerializer(
            purchases, many=True, context={"request": request, "locale": request_locale(request)}
        )
        return Response({"results": serializer.data})
