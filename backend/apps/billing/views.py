from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.services import all_balances

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    PremiumTopUp,
    PremiumTopUpOffer,
)
from .serializers import (
    CurrencyExchangeOfferDetailSerializer,
    CurrencyExchangeOfferSerializer,
    CurrencyExchangeTransactionSerializer,
    PremiumCurrencyTransactionSerializer,
    PremiumTopUpOfferSerializer,
    PremiumTopUpSerializer,
)
from .services import CurrencyExchangeService, PremiumTopUpService


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
        return Response(
            {
                "transaction": CurrencyExchangeTransactionSerializer(transaction_obj).data,
                "balances": all_balances(request.user),
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


class PremiumTopUpOfferListView(APIView):
    """API-ручка списка активных пакетов пополнения премиум-валюты."""

    def get(self, request):
        """Возвращает активные пакеты пополнения по порядку сортировки."""

        offers = PremiumTopUpOffer.objects.filter(is_active=True).order_by("sort_order", "id")
        return Response(PremiumTopUpOfferSerializer(offers, many=True).data)


class PremiumTopUpCreateView(APIView):
    """API-ручка создания pending top-up для выбранного пакета."""

    throttle_scope = "economy"

    def post(self, request, pk):
        """Создаёт попытку пополнения с idempotency key из заголовка."""

        top_up = PremiumTopUpService.create_pending(
            user=request.user,
            offer_id=pk,
            idempotency_key=request.headers.get("Idempotency-Key"),
            locale=request_locale(request),
        )
        return Response(PremiumTopUpSerializer(top_up).data)


class PremiumTopUpListView(APIView):
    """API-ручка истории попыток пополнения текущего пользователя."""

    def get(self, request):
        """Возвращает top-up записи только текущего пользователя, новые сверху."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        top_ups = PremiumTopUp.objects.filter(user=request.user).order_by("-created_at", "-id")[:limit]
        return Response({"results": PremiumTopUpSerializer(top_ups, many=True).data})
