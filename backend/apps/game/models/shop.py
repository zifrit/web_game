from django.core.exceptions import ValidationError
from django.db import models

from .base import MediaAsset, TimestampedModel


class ShopOffer(TimestampedModel):
    """Предложение системного магазина: один или несколько случайных наград."""

    class RewardKind(models.TextChoices):
        INGREDIENT = "ingredient", "Ингредиент"
        POTION = "potion", "Зелье"
        ITEM = "item", "Предмет"

    class DeliveryMode(models.TextChoices):
        SINGLE = "single", "Одиночная"
        CHEST = "chest", "Сундук"

    reward_kind = models.CharField("Тип награды", max_length=32, choices=RewardKind.choices)
    delivery_mode = models.CharField("Режим выдачи", max_length=32, choices=DeliveryMode.choices)

    name_i18n = models.JSONField("Переводы названия", default=dict)
    description_i18n = models.JSONField("Переводы описания", default=dict, blank=True)

    quantity = models.PositiveIntegerField("Количество наград за покупку", default=1)

    price_money_copper = models.PositiveIntegerField("Цена в медных монетах", null=True, blank=True)
    price_premium_currency = models.PositiveIntegerField("Цена в премиум-валюте", null=True, blank=True)

    media = models.ForeignKey(
        MediaAsset,
        verbose_name="Медиа",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shop_offers",
    )

    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Предложение магазина"
        verbose_name_plural = "Предложения магазина"

    def clean(self) -> None:
        """Проверяет наличие хотя бы одной цены и правило количества для single."""

        errors: dict[str, str] = {}

        if self.price_money_copper is None and self.price_premium_currency is None:
            errors["price_money_copper"] = "Offer must have at least one price."
            errors["price_premium_currency"] = "Offer must have at least one price."

        if self.delivery_mode == self.DeliveryMode.SINGLE and self.quantity != 1:
            errors["quantity"] = "Single offer must have quantity = 1."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        """Возвращает локализованное имя или техническое обозначение предложения."""

        return self.name_i18n.get("ru") or self.name_i18n.get("en") or f"ShopOffer #{self.id}"


class ShopOfferIngredient(TimestampedModel):
    """Запись возможного ингредиента-награды предложения с весом шанса."""

    offer = models.ForeignKey(
        "game.ShopOffer",
        verbose_name="Предложение",
        related_name="ingredient_entries",
        on_delete=models.CASCADE,
    )
    ingredient_template = models.ForeignKey(
        "game.IngredientTemplate",
        verbose_name="Шаблон ингредиента",
        on_delete=models.PROTECT,
    )
    chance = models.PositiveIntegerField("Вес шанса", default=1)

    class Meta:
        verbose_name = "Ингредиент предложения"
        verbose_name_plural = "Ингредиенты предложения"

    def clean(self) -> None:
        """Проверяет, что вес шанса положительный."""

        if self.chance < 1:
            raise ValidationError({"chance": "Chance must be greater than 0."})

    def __str__(self) -> str:
        """Возвращает связку предложения и шаблона ингредиента."""

        return f"{self.offer_id} → {self.ingredient_template_id}"


class ShopOfferPotion(TimestampedModel):
    """Запись возможного зелья-награды предложения с весом шанса."""

    offer = models.ForeignKey(
        "game.ShopOffer",
        verbose_name="Предложение",
        related_name="potion_entries",
        on_delete=models.CASCADE,
    )
    potion_template = models.ForeignKey(
        "game.PotionTemplate",
        verbose_name="Шаблон зелья",
        on_delete=models.PROTECT,
    )
    chance = models.PositiveIntegerField("Вес шанса", default=1)

    class Meta:
        verbose_name = "Зелье предложения"
        verbose_name_plural = "Зелья предложения"

    def clean(self) -> None:
        """Проверяет, что вес шанса положительный."""

        if self.chance < 1:
            raise ValidationError({"chance": "Chance must be greater than 0."})

    def __str__(self) -> str:
        """Возвращает связку предложения и шаблона зелья."""

        return f"{self.offer_id} → {self.potion_template_id}"


class ShopOfferItem(TimestampedModel):
    """Запись возможного предмета-награды предложения с весом шанса."""

    offer = models.ForeignKey(
        "game.ShopOffer",
        verbose_name="Предложение",
        related_name="item_entries",
        on_delete=models.CASCADE,
    )
    item_template = models.ForeignKey(
        "game.ItemTemplate",
        verbose_name="Шаблон предмета",
        on_delete=models.PROTECT,
    )
    chance = models.PositiveIntegerField("Вес шанса", default=1)

    class Meta:
        verbose_name = "Предмет предложения"
        verbose_name_plural = "Предметы предложения"

    def clean(self) -> None:
        """Проверяет, что вес шанса положительный."""

        if self.chance < 1:
            raise ValidationError({"chance": "Chance must be greater than 0."})

    def __str__(self) -> str:
        """Возвращает связку предложения и шаблона предмета."""

        return f"{self.offer_id} → {self.item_template_id}"


class ShopPurchase(TimestampedModel):
    """Историческая запись покупки в магазине со снимком условий сделки."""

    class PaymentCurrency(models.TextChoices):
        MONEY_COPPER = "money_copper", "Медные монеты"
        PREMIUM_CURRENCY = "premium_currency", "Премиум-валюта"

    user = models.ForeignKey(
        "game.User",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="shop_purchases",
    )
    character = models.ForeignKey(
        "game.Character",
        verbose_name="Герой",
        on_delete=models.CASCADE,
        related_name="shop_purchases",
    )
    offer = models.ForeignKey(
        "game.ShopOffer",
        verbose_name="Предложение",
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    purchase_count = models.PositiveIntegerField("Число покупок", default=1)

    payment_currency = models.CharField(
        "Валюта оплаты",
        max_length=32,
        choices=PaymentCurrency.choices,
    )

    unit_price_snapshot = models.PositiveIntegerField("Снимок цены за единицу")
    total_price_snapshot = models.PositiveIntegerField("Снимок итоговой цены")

    reward_kind_snapshot = models.CharField("Снимок типа награды", max_length=32)
    delivery_mode_snapshot = models.CharField("Снимок режима выдачи", max_length=32)
    quantity_snapshot = models.PositiveIntegerField("Снимок количества наград")

    result_payload = models.JSONField("Результат выдачи", default=dict)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Покупка в магазине"
        verbose_name_plural = "Покупки в магазине"

    def __str__(self) -> str:
        """Возвращает идентификаторы покупки, пользователя и предложения."""

        return f"Purchase #{self.id} user={self.user_id} offer={self.offer_id}"
