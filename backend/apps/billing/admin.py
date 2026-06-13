from django.contrib import admin

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    PremiumTopUp,
    PremiumTopUpEvent,
    PremiumTopUpOffer,
    UserPremiumBalance,
)


@admin.register(UserPremiumBalance)
class UserPremiumBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "updated_at")
    search_fields = ("user__email",)
    list_select_related = ("user",)
    readonly_fields = ("user", "amount", "created_at", "updated_at")


@admin.register(PremiumCurrencyTransaction)
class PremiumCurrencyTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "reason", "balance_after", "created_at")
    list_filter = ("reason",)
    search_fields = ("id", "user__email", "idempotency_key")
    list_select_related = ("user",)
    readonly_fields = (
        "user",
        "amount",
        "reason",
        "balance_after",
        "idempotency_key",
        "metadata",
        "created_at",
        "updated_at",
    )


@admin.register(PremiumTopUpOffer)
class PremiumTopUpOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "premium_amount",
        "price_amount_minor",
        "price_currency",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "price_currency")


@admin.register(PremiumTopUp)
class PremiumTopUpAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "offer",
        "premium_amount",
        "price_amount_minor",
        "price_currency",
        "status",
        "provider",
        "created_at",
    )
    list_filter = ("status", "provider", "price_currency")
    search_fields = ("id", "user__email", "idempotency_key", "provider_payment_id")
    list_select_related = ("user", "offer", "premium_transaction", "refund_transaction")
    readonly_fields = (
        "user",
        "offer",
        "premium_amount",
        "price_amount_minor",
        "price_currency",
        "status",
        "provider",
        "provider_payment_id",
        "checkout_url",
        "idempotency_key",
        "metadata",
        "premium_transaction",
        "refund_transaction",
        "provider_refund_id",
        "refunded_at",
        "created_at",
        "updated_at",
    )


@admin.register(PremiumTopUpEvent)
class PremiumTopUpEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "provider_event_id",
        "event_type",
        "processing_status",
        "processed_at",
        "created_at",
    )
    list_filter = ("provider", "event_type", "processing_status")
    search_fields = ("id", "provider", "provider_event_id")
    list_select_related = ("top_up",)
    readonly_fields = (
        "top_up",
        "provider",
        "provider_event_id",
        "event_type",
        "payload",
        "processing_status",
        "processed_at",
        "created_at",
        "updated_at",
    )


@admin.register(CurrencyExchangeOffer)
class CurrencyExchangeOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "premium_cost", "money_copper_reward", "is_active", "sort_order")
    list_filter = ("is_active",)


@admin.register(CurrencyExchangeTransaction)
class CurrencyExchangeTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "character",
        "offer",
        "premium_spent",
        "money_copper_received",
        "created_at",
    )
    search_fields = ("id", "user__email", "character__name")
    list_select_related = ("user", "character", "offer")
    readonly_fields = (
        "user",
        "character",
        "offer",
        "premium_spent",
        "money_copper_received",
        "premium_transaction",
        "created_at",
        "updated_at",
    )
