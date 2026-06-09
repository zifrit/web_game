from django.db import models

from apps.game.models import TimestampedModel


class UserPremiumBalance(TimestampedModel):
    """Баланс премиум-валюты пользователя: одна строка на аккаунт."""

    user = models.OneToOneField(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="premium_balance",
    )
    amount = models.PositiveIntegerField("Баланс премиум-валюты", default=0)

    class Meta:
        verbose_name = "Баланс премиум-валюты"
        verbose_name_plural = "Балансы премиум-валюты"

    def __str__(self) -> str:
        """Возвращает связку пользователя и текущего баланса."""

        return f"{self.user_id}: {self.amount}"


class PremiumCurrencyTransaction(TimestampedModel):
    """Неизменяемая запись леджера движений премиум-валюты пользователя."""

    class Reason(models.TextChoices):
        ADMIN_GRANT = "admin_grant", "Начисление администратором"
        SHOP_PURCHASE = "shop_purchase", "Покупка в магазине"
        EXCHANGE_TO_MONEY = "exchange_to_money", "Обмен на монеты"
        PAYMENT = "payment", "Оплата"
        REFUND = "refund", "Возврат"

    user = models.ForeignKey(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="premium_transactions",
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
        verbose_name = "Транзакция премиум-валюты"
        verbose_name_plural = "Транзакции премиум-валюты"

    def __str__(self) -> str:
        """Возвращает пользователя, сумму и причину движения."""

        return f"{self.user_id}: {self.amount} ({self.reason})"


class CurrencyExchangeOffer(TimestampedModel):
    """Предложение обмена премиум-валюты на игровые медные монеты."""

    premium_cost = models.PositiveIntegerField("Стоимость в премиум-валюте")
    money_copper_reward = models.PositiveIntegerField("Награда в медных монетах")

    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Предложение обмена валюты"
        verbose_name_plural = "Предложения обмена валюты"

    def __str__(self) -> str:
        """Возвращает соотношение премиума и медных монет."""

        return f"{self.premium_cost} premium → {self.money_copper_reward} copper"


class CurrencyExchangeTransaction(TimestampedModel):
    """Запись успешного обмена премиум-валюты на медные монеты."""

    user = models.ForeignKey(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="currency_exchange_transactions",
    )
    character = models.ForeignKey(
        "game.Character",
        verbose_name="Герой",
        on_delete=models.CASCADE,
        related_name="currency_exchange_transactions",
    )
    offer = models.ForeignKey(
        "billing.CurrencyExchangeOffer",
        verbose_name="Предложение обмена",
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    premium_spent = models.PositiveIntegerField("Потрачено премиум-валюты")
    money_copper_received = models.PositiveIntegerField("Получено медных монет")

    premium_transaction = models.OneToOneField(
        "billing.PremiumCurrencyTransaction",
        verbose_name="Транзакция премиум-валюты",
        on_delete=models.PROTECT,
        related_name="exchange_transaction",
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Транзакция обмена валюты"
        verbose_name_plural = "Транзакции обмена валюты"

    def __str__(self) -> str:
        """Возвращает сумму списанного премиума и полученных монет."""

        return f"{self.user_id}: -{self.premium_spent} premium +{self.money_copper_received} copper"
