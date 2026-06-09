from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .base import MediaAsset, TimestampedModel
from .characters import Character
from .dungeons import DungeonLocation


class IngredientTemplate(TimestampedModel):
    """Шаблон ингредиента крафта с иконкой и необязательной категорией."""

    class Category(models.TextChoices):
        BASIC = "basic", "Базовый"
        REGIONAL = "regional", "Региональный"
        RARE = "rare", "Редкий"

    code = models.SlugField("Код", unique=True)
    name = models.CharField("Название", max_length=120)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    description = models.TextField("Описание", blank=True, default="")
    description_i18n = models.JSONField("Переводы описания", default=dict, blank=True)
    category = models.CharField(
        "Категория",
        max_length=16,
        choices=Category.choices,
        default=Category.BASIC,
    )
    media = models.ForeignKey(
        MediaAsset,
        verbose_name="Иконка",
        null=True,
        blank=True,
        related_name="ingredient_templates",
        on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self) -> str:
        """Возвращает название ингредиента."""

        return self.name


class HeroIngredientStorage(TimestampedModel):
    """Склад ингредиентов героя: одна строка на пару (герой, ингредиент)."""

    character = models.ForeignKey(
        Character,
        verbose_name="Герой",
        related_name="ingredient_storage",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        IngredientTemplate,
        verbose_name="Ингредиент",
        related_name="storage_entries",
        on_delete=models.PROTECT,
    )
    count = models.PositiveIntegerField("Количество", default=0)

    class Meta:
        unique_together = ("character", "ingredient")
        verbose_name = "Склад ингредиентов героя"
        verbose_name_plural = "Склады ингредиентов героев"

    def __str__(self) -> str:
        """Возвращает связку героя, ингредиента и количества."""

        return f"{self.character} — {self.ingredient} x{self.count}"


class DungeonIngredientDrop(TimestampedModel):
    """Дроп-таблица ингредиентов локации: независимый бросок шанса за забег."""

    location = models.ForeignKey(
        DungeonLocation,
        verbose_name="Локация",
        related_name="ingredient_drops",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        IngredientTemplate,
        verbose_name="Ингредиент",
        related_name="dungeon_drops",
        on_delete=models.CASCADE,
    )
    chance_percent = models.PositiveSmallIntegerField(
        "Шанс выпадения, %",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    min_quantity = models.PositiveSmallIntegerField("Минимум за дроп", default=1)
    max_quantity = models.PositiveSmallIntegerField("Максимум за дроп", default=1)

    class Meta:
        unique_together = ("location", "ingredient")
        verbose_name = "Дроп ингредиента в локации"
        verbose_name_plural = "Дропы ингредиентов в локациях"

    def clean(self) -> None:
        """Проверяет, что минимальное количество не превышает максимальное."""

        if self.min_quantity > self.max_quantity:
            raise ValidationError("min_quantity cannot exceed max_quantity")

    def __str__(self) -> str:
        """Возвращает связь локации и ингредиента."""

        return f"{self.location} -> {self.ingredient}"
