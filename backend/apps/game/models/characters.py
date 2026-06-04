from django.db import models

from .base import MediaAsset, TimestampedModel
from .users import User


class CharacterClass(models.Model):
    """Игровой класс героя с базовыми характеристиками и ростом по уровням."""

    key = models.SlugField("Ключ класса", primary_key=True)
    name = models.CharField("Название", max_length=80)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    start_health = models.PositiveIntegerField("Стартовое здоровье")
    start_attack = models.PositiveIntegerField("Стартовая атака")
    start_defense = models.PositiveIntegerField("Стартовая защита")
    start_critical_chance = models.FloatField("Стартовый шанс критического удара")
    start_evasion = models.FloatField("Стартовое уклонение")
    growth_profile = models.JSONField("Профиль роста")
    male_media = models.ForeignKey(
        MediaAsset,
        verbose_name="Мужчина",
        null=True,
        blank=True,
        related_name="male_character_classes",
        on_delete=models.SET_NULL,
    )
    female_media = models.ForeignKey(
        MediaAsset,
        verbose_name="Женщина",
        null=True,
        blank=True,
        related_name="female_character_classes",
        on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Класс героя"
        verbose_name_plural = "Классы героев"

    def __str__(self) -> str:
        """Возвращает название класса героя."""

        return self.name


class Character(TimestampedModel):
    """Единственный герой аккаунта с прогрессом, статами и экипировкой."""

    class Gender(models.TextChoices):
        MALE = "male", "Мужчина"
        FEMALE = "female", "Женщина"

    user = models.OneToOneField(User, verbose_name="Пользователь", related_name="character", on_delete=models.CASCADE)
    name = models.CharField("Имя героя", max_length=80)
    character_class = models.ForeignKey(CharacterClass, verbose_name="Класс героя", db_column="class_key", on_delete=models.PROTECT)
    gender = models.CharField("Пол", max_length=10, choices=Gender.choices, default=Gender.MALE)
    avatar_media = models.ForeignKey(MediaAsset, verbose_name="Аватар", null=True, blank=True, on_delete=models.SET_NULL)
    level = models.PositiveIntegerField("Уровень", default=1)
    experience = models.PositiveIntegerField("Опыт", default=0)
    health = models.PositiveIntegerField("Здоровье")
    attack = models.PositiveIntegerField("Атака")
    defense = models.PositiveIntegerField("Защита")
    critical_chance = models.FloatField("Шанс критического удара")
    evasion = models.FloatField("Уклонение")
    power_cached = models.FloatField("Кэш силы", null=True, blank=True)
    power_updated_at = models.DateTimeField("Дата обновления силы", null=True, blank=True)

    class Meta:
        ordering = ["-level", "name"]
        verbose_name = "Герой"
        verbose_name_plural = "Герои"

    def __str__(self) -> str:
        """Возвращает имя героя."""

        return self.name
