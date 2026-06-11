from django.core.exceptions import ValidationError
from django.db import models

from .base import MediaAsset, TimestampedModel
from .characters import Character
from .users import User


class ItemTemplate(TimestampedModel):
    """Шаблон предмета, из которого генерируются экземпляры добычи."""

    SLOT_WEAPON = "weapon"
    SLOT_CHOICES = [
        ("weapon", "Weapon"),
        ("helmet", "Helmet"),
        ("armor", "Armor"),
        ("boots", "Boots"),
        ("ring", "Ring"),
    ]
    ITEM_TYPE_CHOICES = [
        ("sword", "Sword"),
        ("dagger", "Dagger"),
        ("staff", "Staff"),
        ("bow", "Bow"),
        ("helmet", "Helmet"),
        ("armor", "Armor"),
        ("boots", "Boots"),
        ("ring", "Ring"),
    ]

    name = models.CharField("Название", max_length=120)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    media = models.ForeignKey(MediaAsset, verbose_name="Медиа", null=True, blank=True, on_delete=models.SET_NULL)
    slot = models.CharField("Слот", max_length=20, choices=SLOT_CHOICES)
    item_type = models.CharField("Тип предмета", max_length=20, choices=ITEM_TYPE_CHOICES)
    rarity_key = models.CharField("Ранг предмета", max_length=20, null=True, blank=True, db_index=True)
    allowed_classes = models.JSONField("Разрешённые классы", null=True, blank=True)
    possible_stats = models.JSONField("Возможные характеристики")
    min_durability = models.PositiveIntegerField("Минимальная прочность", default=10)
    max_durability = models.PositiveIntegerField("Максимальная прочность", default=20)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        ordering = ["slot", "name"]
        verbose_name = "Шаблон предмета"
        verbose_name_plural = "Шаблоны предметов"

    def clean(self) -> None:
        """Проверяет, что минимальная прочность не превышает максимальную."""

        if self.min_durability > self.max_durability:
            raise ValidationError("min_durability cannot exceed max_durability")

    def __str__(self) -> str:
        """Возвращает название шаблона предмета."""

        return f"{self.name} {self.rarity_key}"


class UserItem(TimestampedModel):
    """Конкретный предмет в инвентаре пользователя или экипировке героя."""

    owner_user = models.ForeignKey(User, verbose_name="Владелец", related_name="items", on_delete=models.CASCADE)
    source_character = models.ForeignKey(Character, verbose_name="Герой-источник", null=True, blank=True, related_name="looted_items", on_delete=models.SET_NULL)
    equipped_character = models.ForeignKey(Character, verbose_name="Экипирован героем", null=True, blank=True, related_name="equipped_items", on_delete=models.SET_NULL)
    template = models.ForeignKey(ItemTemplate, verbose_name="Шаблон", on_delete=models.PROTECT)
    name = models.CharField("Название", max_length=160)
    slot = models.CharField("Слот", max_length=20)
    item_type = models.CharField("Тип предмета", max_length=20)
    rarity = models.CharField("Редкость", max_length=20)
    item_level = models.PositiveIntegerField("Уровень предмета")
    stats = models.JSONField("Характеристики")
    durability_current = models.PositiveIntegerField("Текущая прочность")
    durability_max = models.PositiveIntegerField("Максимальная прочность")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Предмет пользователя"
        verbose_name_plural = "Предметы пользователей"

    @property
    def is_broken(self) -> bool:
        """Показывает, сломан ли предмет и перестал ли он давать характеристики."""

        return self.durability_current <= 0

    def __str__(self) -> str:
        """Возвращает название предмета пользователя."""

        return self.name


class RepairTransaction(models.Model):
    """Запись о ремонте предмета и списанной стоимости."""

    user = models.ForeignKey(User, verbose_name="Пользователь", related_name="repair_transactions", on_delete=models.CASCADE)
    item = models.ForeignKey(UserItem, verbose_name="Предмет", related_name="repair_transactions", on_delete=models.CASCADE)
    cost_copper = models.PositiveIntegerField("Стоимость в медных монетах")
    durability_before = models.PositiveIntegerField("Прочность до ремонта")
    durability_after = models.PositiveIntegerField("Прочность после ремонта")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Транзакция ремонта"
        verbose_name_plural = "Транзакции ремонта"
