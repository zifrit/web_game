from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import Character, User

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    UserPremiumBalance,
)


class PremiumCurrencyService:
    """Единственная точка изменения баланса премиум-валюты пользователя."""

    @classmethod
    @transaction.atomic
    def add(cls, *, user, amount: int, reason: str, metadata=None, idempotency_key=None):
        """Начисляет премиум-валюту и пишет запись в неизменяемый леджер."""

        if amount <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        balance, _ = UserPremiumBalance.objects.select_for_update().get_or_create(
            user=user,
            defaults={"amount": 0},
        )

        if idempotency_key:
            existing = PremiumCurrencyTransaction.objects.filter(
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        balance.amount += amount
        balance.save(update_fields=["amount", "updated_at"])

        return PremiumCurrencyTransaction.objects.create(
            user=user,
            amount=amount,
            reason=reason,
            balance_after=balance.amount,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

    @classmethod
    @transaction.atomic
    def spend(cls, *, user, amount: int, reason: str, metadata=None, idempotency_key=None, locale=DEFAULT_LOCALE):
        """Списывает премиум-валюту, проверяя достаточность баланса."""

        if amount <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        balance, _ = UserPremiumBalance.objects.select_for_update().get_or_create(
            user=user,
            defaults={"amount": 0},
        )

        if idempotency_key:
            existing = PremiumCurrencyTransaction.objects.filter(
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        if balance.amount < amount:
            raise serializers.ValidationError(message("not_enough_premium", locale))

        balance.amount -= amount
        balance.save(update_fields=["amount", "updated_at"])

        return PremiumCurrencyTransaction.objects.create(
            user=user,
            amount=-amount,
            reason=reason,
            balance_after=balance.amount,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

    @staticmethod
    def get_amount(user) -> int:
        """Возвращает актуальный баланс премиум-валюты из БД (без кэша связи) или 0."""

        return (
            UserPremiumBalance.objects.filter(user=user)
            .values_list("amount", flat=True)
            .first()
            or 0
        )


class CurrencyExchangeService:
    """Обмен премиум-валюты на игровые медные монеты пользователя."""

    @classmethod
    @transaction.atomic
    def exchange(cls, *, user, offer_id: int, locale=DEFAULT_LOCALE) -> CurrencyExchangeTransaction:
        """Списывает премиум, начисляет монеты пользователю, пишет запись обмена."""

        try:
            offer = CurrencyExchangeOffer.objects.get(id=offer_id, is_active=True)
        except CurrencyExchangeOffer.DoesNotExist as exc:
            raise serializers.ValidationError(message("shop_offer_not_found", locale)) from exc

        try:
            character = Character.objects.get(user=user)
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

        # money_copper живёт на User (не на Character), поэтому блокируем строку User.
        user_row = User.objects.select_for_update().get(pk=user.pk)

        premium_transaction = PremiumCurrencyService.spend(
            user=user,
            amount=offer.premium_cost,
            reason=PremiumCurrencyTransaction.Reason.EXCHANGE_TO_MONEY,
            metadata={
                "exchange_offer_id": offer.id,
                "money_copper_reward": offer.money_copper_reward,
            },
            locale=locale,
        )

        user_row.money_copper += offer.money_copper_reward
        user_row.save(update_fields=["money_copper", "updated_at"])

        return CurrencyExchangeTransaction.objects.create(
            user=user_row,
            character=character,
            offer=offer,
            premium_spent=offer.premium_cost,
            money_copper_received=offer.money_copper_reward,
            premium_transaction=premium_transaction,
        )
