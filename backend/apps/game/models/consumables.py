from django.db import models

from .base import MediaAsset, TimestampedModel
from .characters import Character


class PotionTemplate(TimestampedModel):
    """Шаблон зелья лечения с процентом восстановления HP и иконкой."""

    code = models.SlugField("Код", unique=True)
    name = models.CharField("Название", max_length=120)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    description = models.TextField("Описание", blank=True, default="")
    description_i18n = models.JSONField("Переводы описания", default=dict, blank=True)
    heal_percent = models.PositiveSmallIntegerField("Процент лечения от максимального HP")
    media = models.ForeignKey(
        MediaAsset,
        verbose_name="Иконка",
        null=True,
        blank=True,
        related_name="potion_templates",
        on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Зелье"
        verbose_name_plural = "Зелья"

    def __str__(self) -> str:
        """Возвращает название зелья."""

        return self.name


class HeroPotionStorage(TimestampedModel):
    """Склад зелий героя: одна строка на пару (герой, зелье) с количеством."""

    character = models.ForeignKey(
        Character,
        verbose_name="Герой",
        related_name="potion_storage",
        on_delete=models.CASCADE,
    )
    potion = models.ForeignKey(
        PotionTemplate,
        verbose_name="Зелье",
        related_name="storage_entries",
        on_delete=models.PROTECT,
    )
    count = models.PositiveIntegerField("Количество", default=0)

    class Meta:
        unique_together = ("character", "potion")
        verbose_name = "Склад зелий героя"
        verbose_name_plural = "Склады зелий героев"

    def __str__(self) -> str:
        """Возвращает связку героя, зелья и количества."""

        return f"{self.character} — {self.potion} x{self.count}"
