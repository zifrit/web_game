from django.core.exceptions import ValidationError
from django.db import models

from .base import TimestampedModel


class RarityConfig(models.Model):
    """Настройка редкости предметов и её влияния на уровень и характеристики."""

    key = models.SlugField("Ключ редкости", primary_key=True)
    name = models.CharField("Название", max_length=80)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    stat_multiplier = models.FloatField("Множитель характеристик")
    min_item_level = models.PositiveIntegerField("Минимальный уровень предмета")
    max_item_level = models.PositiveIntegerField("Максимальный уровень предмета")
    min_stats_count = models.PositiveIntegerField("Минимум характеристик")
    max_stats_count = models.PositiveIntegerField("Максимум характеристик")
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Редкость"
        verbose_name_plural = "Редкости"

    def clean(self) -> None:
        """Проверяет корректность диапазонов уровней и количества характеристик."""

        if self.min_item_level > self.max_item_level:
            raise ValidationError("min_item_level cannot exceed max_item_level")
        if self.min_stats_count > self.max_stats_count:
            raise ValidationError("min_stats_count cannot exceed max_stats_count")

    def __str__(self) -> str:
        """Возвращает название редкости."""

        return self.name


class EquipmentSlotConfig(models.Model):
    """Справочник слотов экипировки, доступных в игре."""

    key = models.SlugField("Ключ слота", primary_key=True)
    name = models.CharField("Название", max_length=80)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Слот экипировки"
        verbose_name_plural = "Слоты экипировки"

    def __str__(self) -> str:
        """Возвращает название слота экипировки."""

        return self.name


class GameConfig(TimestampedModel):
    """Гибкая игровая настройка для формул, экономики и баланса."""

    key = models.SlugField("Ключ настройки", unique=True)
    value = models.JSONField("Значение")
    description = models.TextField("Описание", blank=True, default="")
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Игровая настройка"
        verbose_name_plural = "Игровые настройки"

    def __str__(self) -> str:
        """Возвращает ключ игровой настройки."""

        return self.key
