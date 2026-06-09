from django.db import models

from .base import TimestampedModel


class MoneyTransaction(TimestampedModel):
    """Неизменяемая запись леджера движений медных монет пользователя."""

    class Reason(models.TextChoices):
        ADMIN_GRANT = "admin_grant", "Начисление администратором"
        DUNGEON_REWARD = "dungeon_reward", "Награда за подземелье"
        SHOP_PURCHASE = "shop_purchase", "Покупка в магазине"
        REPAIR = "repair", "Ремонт предметов"
        DESTROY_REFUND = "destroy_refund", "Возврат за уничтожение"
        EXCHANGE_FROM_PREMIUM = "exchange_from_premium", "Обмен с премиум-валюты"

    user = models.ForeignKey(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="money_transactions",
    )
    amount = models.IntegerField("Сумма (со знаком)")
    reason = models.CharField("Причина", max_length=64, choices=Reason.choices)
    balance_after = models.PositiveIntegerField("Баланс после операции")
    idempotency_key = models.CharField(
        "Ключ идемпотентности",
        max_length=128,
        null=True,
        blank=True,
        unique=True,
    )
    metadata = models.JSONField("Метаданные", default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Транзакция медных монет"
        verbose_name_plural = "Транзакции медных монет"

    def __str__(self) -> str:
        """Возвращает пользователя, сумму и причину движения."""

        return f"{self.user_id}: {self.amount} ({self.reason})"
