from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .base import MediaAsset, TimestampedModel
from .characters import Character
from .items import ItemTemplate, UserItem
from .users import User


class DungeonLocation(TimestampedModel):
    """Локация подземелья с длительностью, требованиями и наградами."""

    name = models.CharField("Название", max_length=120)
    description = models.TextField("Описание", blank=True, default="")
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    description_i18n = models.JSONField("Переводы описания", default=dict, blank=True)
    media = models.ForeignKey(MediaAsset, verbose_name="Медиа", null=True, blank=True, on_delete=models.SET_NULL)
    duration_seconds = models.PositiveIntegerField("Длительность в секундах")
    required_power = models.FloatField("Требуемая сила")
    experience_min = models.PositiveIntegerField("Минимум опыта")
    experience_max = models.PositiveIntegerField("Максимум опыта")
    money_min_copper = models.PositiveIntegerField("Минимум медных монет")
    money_max_copper = models.PositiveIntegerField("Максимум медных монет")
    item_drop_chance = models.FloatField("Шанс выпадения предмета")
    rarity_chances = models.JSONField("Шансы редкостей")
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Локация подземелья"
        verbose_name_plural = "Локации подземелий"

    def clean(self) -> None:
        """Проверяет диапазоны наград, шанс дропа и сумму шансов редкостей."""

        if self.experience_min > self.experience_max:
            raise ValidationError("experience_min cannot exceed experience_max")
        if self.money_min_copper > self.money_max_copper:
            raise ValidationError("money_min_copper cannot exceed money_max_copper")
        if not 0 <= self.item_drop_chance <= 100:
            raise ValidationError("item_drop_chance must be between 0 and 100")
        if round(sum(self.rarity_chances.values())) != 100:
            raise ValidationError("rarity_chances must sum to 100")

    def __str__(self) -> str:
        """Возвращает название локации подземелья."""

        return self.name


class DungeonLocationItemTemplate(TimestampedModel):
    """Связь локации подземелья с шаблоном предмета, который может выпасть."""

    location = models.ForeignKey(DungeonLocation, verbose_name="Локация", related_name="location_item_templates", on_delete=models.CASCADE)
    item_template = models.ForeignKey(ItemTemplate, verbose_name="Шаблон предмета", related_name="template_locations", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("location", "item_template")
        verbose_name = "Предмет локации подземелья"
        verbose_name_plural = "Предметы локаций подземелий"

    def __str__(self) -> str:
        """Возвращает связь локации и шаблона предмета."""

        return f"{self.location} -> {self.item_template}"


class DungeonRunStatus(models.TextChoices):
    """Статусы прохождения подземелья."""

    IN_PROGRESS = "IN_PROGRESS", "In progress"
    SUCCESS_WAITING_CLAIM = "SUCCESS_WAITING_CLAIM", "Success waiting claim"
    FAILED_WAITING_CLAIM = "FAILED_WAITING_CLAIM", "Failed waiting claim"
    CLAIMED = "CLAIMED", "Claimed"


class DungeonRun(TimestampedModel):
    """Один запуск героя в подземелье с таймером, шансом успеха и наградами."""

    IN_PROGRESS = DungeonRunStatus.IN_PROGRESS
    SUCCESS_WAITING_CLAIM = DungeonRunStatus.SUCCESS_WAITING_CLAIM
    FAILED_WAITING_CLAIM = DungeonRunStatus.FAILED_WAITING_CLAIM
    CLAIMED = DungeonRunStatus.CLAIMED

    character = models.ForeignKey(Character, verbose_name="Герой", related_name="dungeon_runs", on_delete=models.CASCADE)
    location = models.ForeignKey(DungeonLocation, verbose_name="Локация", on_delete=models.PROTECT)
    status = models.CharField("Статус", max_length=32, choices=DungeonRunStatus.choices, default=DungeonRunStatus.IN_PROGRESS)
    started_at = models.DateTimeField("Дата старта", default=timezone.now)
    ends_at = models.DateTimeField("Дата завершения")
    completed_at = models.DateTimeField("Дата фактического завершения", null=True, blank=True)
    success_chance = models.FloatField("Шанс успеха")
    is_success = models.BooleanField("Успешно", null=True, blank=True)
    experience_reward = models.PositiveIntegerField("Награда опытом", null=True, blank=True)
    money_reward_copper = models.PositiveIntegerField("Награда в медных монетах", null=True, blank=True)
    items_reward = models.JSONField("Награда предметами", null=True, blank=True)
    durability_loss = models.PositiveIntegerField("Потеря прочности", null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Забег в подземелье"
        verbose_name_plural = "Забеги в подземелья"
        constraints = [
            models.UniqueConstraint(
                fields=["character"],
                condition=Q(status=DungeonRunStatus.IN_PROGRESS),
                name="unique_in_progress_run_per_character",
            )
        ]

    def __str__(self) -> str:
        """Возвращает краткое описание забега героя в подземелье."""

        return f"{self.character} @ {self.location} [{self.status}]"


class DungeonRunClaim(models.Model):
    """Идемпотентная запись о получении наград за завершённый забег."""

    dungeon_run = models.OneToOneField(DungeonRun, verbose_name="Забег", related_name="claim", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Пользователь", related_name="dungeon_claims", on_delete=models.CASCADE)
    character = models.ForeignKey(Character, verbose_name="Герой", related_name="dungeon_claims", on_delete=models.CASCADE)
    experience_claimed = models.PositiveIntegerField("Полученный опыт")
    money_claimed_copper = models.PositiveIntegerField("Полученные медные монеты")
    created_at = models.DateTimeField("Дата получения", auto_now_add=True)

    class Meta:
        verbose_name = "Получение награды"
        verbose_name_plural = "Получения наград"

    def __str__(self) -> str:
        """Возвращает техническое описание получения награды."""

        return f"Claim #{self.pk} for run #{self.dungeon_run_id}"


class DungeonRunClaimItem(models.Model):
    """Связь полученной награды с выданным пользователю предметом."""

    claim = models.ForeignKey(DungeonRunClaim, verbose_name="Получение награды", related_name="claim_items", on_delete=models.CASCADE)
    user_item = models.ForeignKey(UserItem, verbose_name="Предмет пользователя", related_name="claim_links", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Предмет из награды"
        verbose_name_plural = "Предметы из наград"
