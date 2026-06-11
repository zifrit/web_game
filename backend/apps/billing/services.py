from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import Character, MoneyTransaction

from .models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    PremiumTopUp,
    PremiumTopUpEvent,
    PremiumTopUpOffer,
    UserPremiumBalance,
)


class PremiumCurrencyService:
    """Единственная точка изменения баланса премиум-валюты пользователя."""

    @classmethod
    @transaction.atomic
    def grant(cls, *, user, amount: int, reason: str, metadata=None, idempotency_key=None):
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
    def charge(
        cls,
        *,
        user,
        amount: int,
        reason: str,
        metadata=None,
        idempotency_key=None,
        insufficient_message: str = "not_enough_premium",
        locale=DEFAULT_LOCALE,
    ):
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
            raise serializers.ValidationError(message(insufficient_message, locale))

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


class PremiumTopUpService:
    """Сервис жизненного цикла пополнения премиум-валюты."""

    @classmethod
    @transaction.atomic
    def create_pending(
        cls,
        *,
        user,
        offer_id: int,
        idempotency_key: str | None = None,
        metadata=None,
        locale=DEFAULT_LOCALE,
    ) -> PremiumTopUp:
        """Создаёт pending top-up со снимком активного пакета пополнения."""

        if idempotency_key:
            existing = PremiumTopUp.objects.filter(
                user=user,
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        try:
            offer = PremiumTopUpOffer.objects.get(id=offer_id, is_active=True)
        except PremiumTopUpOffer.DoesNotExist as exc:
            raise serializers.ValidationError(message("shop_offer_not_found", locale)) from exc

        return PremiumTopUp.objects.create(
            user=user,
            offer=offer,
            premium_amount=offer.premium_amount,
            price_amount_minor=offer.price_amount_minor,
            price_currency=offer.price_currency,
            status=PremiumTopUp.Status.PENDING,
            checkout_url=None,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

    @classmethod
    @transaction.atomic
    def mark_succeeded(
        cls,
        *,
        top_up_id: int,
        provider: str = "",
        provider_payment_id: str | None = None,
        metadata=None,
    ) -> PremiumTopUp:
        """Подтверждает успешную оплату и начисляет премиум-валюту ровно один раз."""

        top_up = PremiumTopUp.objects.select_for_update().select_related(
            "user",
            "premium_transaction",
        ).get(id=top_up_id)

        if top_up.status == PremiumTopUp.Status.SUCCEEDED:
            return top_up

        if top_up.status not in (PremiumTopUp.Status.CREATED, PremiumTopUp.Status.PENDING):
            raise serializers.ValidationError("Top-up cannot be marked as succeeded from its current status.")

        provider = provider or top_up.provider
        provider_payment_id = provider_payment_id or top_up.provider_payment_id
        grant_transaction = PremiumCurrencyService.grant(
            user=top_up.user,
            amount=top_up.premium_amount,
            reason=PremiumCurrencyTransaction.Reason.PAYMENT,
            idempotency_key=f"premium-top-up:{top_up.id}:payment",
            metadata={
                "premium_top_up_id": top_up.id,
                "provider": provider,
                "provider_payment_id": provider_payment_id,
                **(metadata or {}),
            },
        )

        top_up.status = PremiumTopUp.Status.SUCCEEDED
        top_up.provider = provider or ""
        top_up.provider_payment_id = provider_payment_id
        top_up.premium_transaction = grant_transaction
        top_up.metadata = {**(top_up.metadata or {}), **(metadata or {})}
        top_up.save(
            update_fields=[
                "status",
                "provider",
                "provider_payment_id",
                "premium_transaction",
                "metadata",
                "updated_at",
            ]
        )
        return top_up

    @classmethod
    def record_event(
        cls,
        *,
        provider: str,
        provider_event_id: str,
        event_type: str,
        payload=None,
        top_up: PremiumTopUp | None = None,
    ) -> PremiumTopUpEvent:
        """Сохраняет входящее событие провайдера для будущего webhook-flow."""

        event, _ = PremiumTopUpEvent.objects.get_or_create(
            provider=provider,
            provider_event_id=provider_event_id,
            defaults={
                "top_up": top_up,
                "event_type": event_type,
                "payload": payload or {},
            },
        )
        return event


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

        # Обе валюты проходят через один шов кошельков.
        from apps.game.services.wallets import MONEY_COPPER, PREMIUM_CURRENCY, get_wallet

        premium_transaction = get_wallet(PREMIUM_CURRENCY).charge(
            user,
            amount=offer.premium_cost,
            reason=PremiumCurrencyTransaction.Reason.EXCHANGE_TO_MONEY,
            metadata={
                "exchange_offer_id": offer.id,
                "money_copper_reward": offer.money_copper_reward,
            },
            locale=locale,
        )

        get_wallet(MONEY_COPPER).grant(
            user,
            amount=offer.money_copper_reward,
            reason=MoneyTransaction.Reason.EXCHANGE_FROM_PREMIUM,
            metadata={"exchange_offer_id": offer.id, "premium_cost": offer.premium_cost},
        )

        return CurrencyExchangeTransaction.objects.create(
            user=user,
            character=character,
            offer=offer,
            premium_spent=offer.premium_cost,
            money_copper_received=offer.money_copper_reward,
            premium_transaction=premium_transaction,
        )
