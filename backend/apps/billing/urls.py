from django.urls import path

from .views import (
    ExchangeCurrencyView,
    ExchangeOfferDetailView,
    ExchangeOfferListView,
    ExchangeTransactionListView,
    PremiumTransactionListView,
)

urlpatterns = [
    path("exchange-offers", ExchangeOfferListView.as_view(), name="billing_exchange_offers"),
    path("exchange-offers/<int:pk>", ExchangeOfferDetailView.as_view(), name="billing_exchange_offer_detail"),
    path("exchange-offers/<int:pk>/exchange", ExchangeCurrencyView.as_view(), name="billing_exchange"),
    path("exchange-transactions", ExchangeTransactionListView.as_view(), name="billing_exchange_transactions"),
    path("premium-transactions", PremiumTransactionListView.as_view(), name="billing_premium_transactions"),
]
