from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

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


class PremiumTopUpOffer(TimestampedModel):
    """Пакет пополнения премиум-валюты за реальные деньги."""

    premium_amount = models.PositiveIntegerField("Количество премиум-валюты")
    price_amount_minor = models.PositiveIntegerField("Цена в minor units")
    price_currency = models.CharField("Валюта цены", max_length=3, default="RUB")

    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Пакет пополнения премиум-валюты"
        verbose_name_plural = "Пакеты пополнения премиум-валюты"

    def clean(self) -> None:
        """Проверяет положительные суммы и ISO-подобный код валюты."""

        errors: dict[str, str] = {}
        if self.premium_amount <= 0:
            errors["premium_amount"] = "Premium amount must be positive."
        if self.price_amount_minor <= 0:
            errors["price_amount_minor"] = "Price amount must be positive."
        if len((self.price_currency or "").strip()) != 3:
            errors["price_currency"] = "Currency code must be 3 letters."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.price_currency = (self.price_currency or "RUB").upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает премиум и цену пакета."""

        return f"{self.premium_amount} premium for {self.price_amount_minor} {self.price_currency}"


class PremiumTopUp(TimestampedModel):
    """Попытка пополнения премиум-валюты с жизненным циклом платежа."""

    class Status(models.TextChoices):
        CREATED = "created", "Создано"
        PENDING = "pending", "Ожидает оплаты"
        SUCCEEDED = "succeeded", "Успешно"
        FAILED = "failed", "Неуспешно"
        CANCELED = "canceled", "Отменено"
        EXPIRED = "expired", "Истекло"
        REFUNDED = "refunded", "Возвращено"

    user = models.ForeignKey(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="premium_top_ups",
    )
    offer = models.ForeignKey(
        "billing.PremiumTopUpOffer",
        verbose_name="Пакет пополнения",
        on_delete=models.PROTECT,
        related_name="top_ups",
    )

    premium_amount = models.PositiveIntegerField("Снимок количества премиум-валюты")
    price_amount_minor = models.PositiveIntegerField("Снимок цены в minor units")
    price_currency = models.CharField("Снимок валюты цены", max_length=3, default="RUB")

    status = models.CharField("Статус", max_length=32, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField("Провайдер", max_length=64, blank=True)
    provider_payment_id = models.CharField(
        "ID платежа у провайдера",
        max_length=128,
        null=True,
        blank=True,
    )
    checkout_url = models.URLField("Checkout URL", null=True, blank=True)
    idempotency_key = models.CharField(
        "Ключ идемпотентности",
        max_length=128,
        null=True,
        blank=True,
    )
    metadata = models.JSONField("Метаданные", default=dict, blank=True)

    premium_transaction = models.OneToOneField(
        "billing.PremiumCurrencyTransaction",
        verbose_name="Транзакция начисления премиум-валюты",
        on_delete=models.PROTECT,
        related_name="top_up",
        null=True,
        blank=True,
    )
    refund_transaction = models.OneToOneField(
        "billing.PremiumCurrencyTransaction",
        verbose_name="Транзакция возврата премиум-валюты",
        on_delete=models.PROTECT,
        related_name="refunded_top_up",
        null=True,
        blank=True,
    )
    provider_refund_id = models.CharField(
        "ID возврата у провайдера",
        max_length=128,
        null=True,
        blank=True,
    )
    refunded_at = models.DateTimeField("Дата возврата", null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="billing_topup_unique_user_idempotency_key",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_payment_id"],
                condition=Q(provider_payment_id__isnull=False),
                name="billing_topup_unique_provider_payment",
            ),
        ]
        verbose_name = "Пополнение премиум-валюты"
        verbose_name_plural = "Пополнения премиум-валюты"

    def save(self, *args, **kwargs):
        self.price_currency = (self.price_currency or "RUB").upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает пользователя, сумму и статус пополнения."""

        return f"{self.user_id}: +{self.premium_amount} premium ({self.status})"


class PremiumTopUpEvent(TimestampedModel):
    """Сохранённое событие платёжного провайдера для будущего webhook-flow."""

    class ProcessingStatus(models.TextChoices):
        RECEIVED = "received", "Получено"
        PROCESSED = "processed", "Обработано"
        FAILED = "failed", "Ошибка"
        IGNORED = "ignored", "Проигнорировано"

    top_up = models.ForeignKey(
        "billing.PremiumTopUp",
        verbose_name="Пополнение",
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    provider = models.CharField("Провайдер", max_length=64)
    provider_event_id = models.CharField("ID события у провайдера", max_length=128)
    event_type = models.CharField("Тип события", max_length=128)
    payload = models.JSONField("Payload", default=dict, blank=True)
    processing_status = models.CharField(
        "Статус обработки",
        max_length=32,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.RECEIVED,
    )
    processed_at = models.DateTimeField("Дата обработки", null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="billing_topupevent_unique_provider_event",
            ),
        ]
        verbose_name = "Событие пополнения премиум-валюты"
        verbose_name_plural = "События пополнений премиум-валюты"

    def __str__(self) -> str:
        """Возвращает провайдера, событие и тип события."""

        return f"{self.provider}:{self.provider_event_id} ({self.event_type})"


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
