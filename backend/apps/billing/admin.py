from django.contrib import admin

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    UserPremiumBalance,
)


@admin.register(UserPremiumBalance)
class UserPremiumBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "updated_at")
    search_fields = ("user__email",)
    list_select_related = ("user",)
    readonly_fields = ("user", "amount", "created_at", "updated_at")

    def has_delete_permission(self, request, obj=None) -> bool:
        """Запрещает удаление балансов: они привязаны к пользователю."""

        return False


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

    def has_add_permission(self, request) -> bool:
        """Запрещает ручное добавление: начисления только через сервис."""

        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Запрещает удаление: премиум-леджер неизменяем."""

        return False


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

    def has_add_permission(self, request) -> bool:
        """Запрещает ручное добавление: обмен выполняется только через сервис."""

        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Запрещает удаление записей обмена."""

        return False
