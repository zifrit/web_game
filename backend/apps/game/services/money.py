from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import MoneyTransaction, User


class MoneyService:
    """Единственная точка изменения медного баланса пользователя (money_copper).

    Сервис сам блокирует строку User, владеет инвариантом неотрицательности и
    пишет неизменяемый леджер. Вызывающие не трогают поле money_copper напрямую
    и читают итоговый баланс из MoneyTransaction.balance_after.
    """

    @classmethod
    @transaction.atomic
    def grant(cls, *, user, amount: int, reason: str, metadata=None, idempotency_key=None) -> MoneyTransaction:
        """Начисляет медь и пишет запись в леджер."""

        if amount <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        user_row = User.objects.select_for_update().get(pk=user.pk)

        existing = cls._existing_transaction(idempotency_key)
        if existing is not None:
            return existing

        user_row.money_copper += amount
        user_row.save(update_fields=["money_copper", "updated_at"])

        return cls._record(user_row, amount, reason, idempotency_key, metadata)

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
        insufficient_message: str = "not_enough_money",
        locale: str = DEFAULT_LOCALE,
    ) -> MoneyTransaction:
        """Списывает медь, проверяя достаточность баланса."""

        if amount <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        user_row = User.objects.select_for_update().get(pk=user.pk)

        existing = cls._existing_transaction(idempotency_key)
        if existing is not None:
            return existing

        if user_row.money_copper < amount:
            raise serializers.ValidationError(message(insufficient_message, locale))

        user_row.money_copper -= amount
        user_row.save(update_fields=["money_copper", "updated_at"])

        return cls._record(user_row, -amount, reason, idempotency_key, metadata)

    @staticmethod
    def get_amount(user) -> int:
        """Возвращает актуальный медный баланс из БД (без кэша экземпляра)."""

        return (
            User.objects.filter(pk=user.pk)
            .values_list("money_copper", flat=True)
            .first()
            or 0
        )

    # --- внутренние помощники ---

    @staticmethod
    def _existing_transaction(idempotency_key) -> MoneyTransaction | None:
        """Возвращает ранее записанную транзакцию по ключу идемпотентности, если есть."""

        if not idempotency_key:
            return None
        return MoneyTransaction.objects.filter(idempotency_key=idempotency_key).first()

    @staticmethod
    def _record(user_row, signed_amount: int, reason: str, idempotency_key, metadata) -> MoneyTransaction:
        """Пишет неизменяемую запись леджера для выполненного движения."""

        return MoneyTransaction.objects.create(
            user=user_row,
            amount=signed_amount,
            reason=reason,
            balance_after=user_row.money_copper,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )
