from django.urls import path

from .views import (
    ExchangeCurrencyView,
    ExchangeOfferDetailView,
    ExchangeOfferListView,
    ExchangeTransactionListView,
    PremiumTopUpCreateView,
    PremiumTopUpListView,
    PremiumTopUpOfferListView,
    PremiumTransactionListView,
)

urlpatterns = [
    path("exchange-offers", ExchangeOfferListView.as_view(), name="billing_exchange_offers"),
    path("exchange-offers/<int:pk>", ExchangeOfferDetailView.as_view(), name="billing_exchange_offer_detail"),
    path("exchange-offers/<int:pk>/exchange", ExchangeCurrencyView.as_view(), name="billing_exchange"),
    path("exchange-transactions", ExchangeTransactionListView.as_view(), name="billing_exchange_transactions"),
    path("premium-transactions", PremiumTransactionListView.as_view(), name="billing_premium_transactions"),
    path("top-up-offers", PremiumTopUpOfferListView.as_view(), name="billing_top_up_offers"),
    path("top-up-offers/<int:pk>/top-ups", PremiumTopUpCreateView.as_view(), name="billing_top_up_create"),
    path("top-ups", PremiumTopUpListView.as_view(), name="billing_top_ups"),
]
