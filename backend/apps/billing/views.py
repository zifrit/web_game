from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
)
from .serializers import (
    CurrencyExchangeOfferDetailSerializer,
    CurrencyExchangeOfferSerializer,
    CurrencyExchangeTransactionSerializer,
    PremiumCurrencyTransactionSerializer,
)
from .services import CurrencyExchangeService, PremiumCurrencyService


class ExchangeOfferListView(APIView):
    """API-ручка списка активных предложений обмена валюты."""

    def get(self, request):
        """Возвращает активные предложения обмена по порядку сортировки."""

        offers = CurrencyExchangeOffer.objects.filter(is_active=True).order_by("sort_order", "id")
        return Response(CurrencyExchangeOfferSerializer(offers, many=True).data)


class ExchangeOfferDetailView(APIView):
    """API-ручка детального предложения обмена валюты."""

    def get(self, request, pk):
        """Возвращает одно активное предложение обмена с признаком активности."""

        offer = get_object_or_404(CurrencyExchangeOffer, pk=pk, is_active=True)
        return Response(CurrencyExchangeOfferDetailSerializer(offer).data)


class ExchangeCurrencyView(APIView):
    """API-ручка обмена премиум-валюты на медные монеты."""

    throttle_scope = "economy"

    def post(self, request, pk):
        """Выполняет обмен и возвращает запись транзакции и обновлённые балансы."""

        locale = request_locale(request)
        transaction_obj = CurrencyExchangeService.exchange(
            user=request.user, offer_id=pk, locale=locale
        )
        request.user.refresh_from_db(fields=["money_copper"])
        return Response(
            {
                "transaction": CurrencyExchangeTransactionSerializer(transaction_obj).data,
                "balances": {
                    "premium_currency": PremiumCurrencyService.get_amount(request.user),
                    "money_copper": request.user.money_copper,
                },
            }
        )


class ExchangeTransactionListView(APIView):
    """API-ручка истории обменов валюты текущего пользователя."""

    def get(self, request):
        """Возвращает обмены только текущего пользователя, новые сверху."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        transactions = CurrencyExchangeTransaction.objects.filter(user=request.user).order_by(
            "-created_at", "-id"
        )[:limit]
        return Response({"results": CurrencyExchangeTransactionSerializer(transactions, many=True).data})


class PremiumTransactionListView(APIView):
    """API-ручка истории движений премиум-валюты текущего пользователя."""

    def get(self, request):
        """Возвращает записи леджера только текущего пользователя, новые сверху."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        transactions = PremiumCurrencyTransaction.objects.filter(user=request.user).order_by(
            "-created_at", "-id"
        )[:limit]
        return Response({"results": PremiumCurrencyTransactionSerializer(transactions, many=True).data})
