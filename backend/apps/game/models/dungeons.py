import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .base import MediaAsset, TimestampedModel


_SVG_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_SVG_ON_ATTR_RE = re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
_SVG_EXTERNAL_HREF_RE = re.compile(
    r"\s(?:xlink:)?href\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE
)


def sanitize_svg_markup(markup: str) -> str:
    """Убирает из SVG потенциально опасные части перед инлайном на фронте.

    Контент admin-only, но раз он встраивается в DOM напрямую — вырезаем
    `<script>`, обработчики событий `on*` и внешние ссылки `href`/`xlink:href`.
    """

    if not markup:
        return ""
    cleaned = _SVG_SCRIPT_RE.sub("", markup)
    cleaned = _SVG_ON_ATTR_RE.sub("", cleaned)

    def _strip_external(match: "re.Match[str]") -> str:
        value = match.group(1).strip("\"'").strip()
        if value.startswith("#"):
            return match.group(0)
        return ""

    cleaned = _SVG_EXTERNAL_HREF_RE.sub(_strip_external, cleaned)
    return cleaned.strip()
from .characters import Character
from .items import ItemTemplate, UserItem
from .users import User


class LocationType(models.TextChoices):
    """Тип локации: боевой данж или мирная ресурсная локация."""

    DUNGEON = "dungeon", "Данж"
    RESOURCE = "resource", "Ресурсная локация"


class DungeonLimitCategory(TimestampedModel):
    """Балансировочная группа локаций с общим лимитом стартов."""

    class PeriodUnit(models.TextChoices):
        HOUR = "hour", "Час"
        DAY = "day", "День"
        WEEK = "week", "Неделя"
        MONTH = "month", "Месяц"

    code = models.SlugField("Код", max_length=64, unique=True)
    name = models.CharField("Название", max_length=120)
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    limit_count = models.PositiveIntegerField("Лимит стартов (0 = без лимита)", default=0)
    limit_period_count = models.PositiveIntegerField(
        "Количество единиц периода",
        default=1,
        validators=[MinValueValidator(1)],
    )
    limit_period_unit = models.CharField(
        "Единица периода",
        max_length=16,
        choices=PeriodUnit.choices,
        default=PeriodUnit.DAY,
    )
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Категория лимита локаций"
        verbose_name_plural = "Категории лимитов локаций"

    def __str__(self) -> str:
        return self.name


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
    hp_loss_success_percent = models.FloatField("Потеря HP при успехе, %", default=0)
    hp_loss_fail_percent = models.FloatField("Потеря HP при провале, %", default=0)
    item_drop_chance = models.FloatField("Шанс выпадения предмета")
    has_mini_game = models.BooleanField("Доступна мини-игра", default=False)
    location_type = models.CharField(
        "Тип локации",
        max_length=16,
        choices=LocationType.choices,
        default=LocationType.DUNGEON,
        db_index=True,
    )
    limit_category = models.ForeignKey(
        DungeonLimitCategory,
        verbose_name="Категория лимита",
        related_name="locations",
        on_delete=models.PROTECT,
    )
    daily_limit = models.PositiveIntegerField("Дневной лимит заходов (0 = без лимита)", default=0)
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Локация подземелья"
        verbose_name_plural = "Локации подземелий"

    def clean(self) -> None:
        """Проверяет диапазоны наград, шанс дропа и наличие активного лута."""

        if self.experience_min > self.experience_max:
            raise ValidationError("experience_min cannot exceed experience_max")
        if self.money_min_copper > self.money_max_copper:
            raise ValidationError("money_min_copper cannot exceed money_max_copper")
        if not 0 <= self.item_drop_chance <= 100:
            raise ValidationError("item_drop_chance must be between 0 and 100")
        if not 0 <= self.hp_loss_success_percent <= 100:
            raise ValidationError("hp_loss_success_percent must be between 0 and 100")
        if not 0 <= self.hp_loss_fail_percent <= 100:
            raise ValidationError("hp_loss_fail_percent must be between 0 and 100")
        if self.location_type == LocationType.RESOURCE:
            if self.required_power:
                raise ValidationError("resource location must have required_power = 0")
            if self.experience_min or self.experience_max:
                raise ValidationError("resource location must have zero experience")
            if self.money_min_copper or self.money_max_copper:
                raise ValidationError("resource location must have zero money reward")
            if self.item_drop_chance:
                raise ValidationError("resource location must have item_drop_chance = 0")
            if self.hp_loss_success_percent or self.hp_loss_fail_percent:
                raise ValidationError("resource location must have zero hp loss")
            if self.daily_limit <= 0:
                raise ValidationError("resource location must have daily_limit > 0")
        # if (
        #     self.pk
        #     and self.is_active
        #     and self.item_drop_chance > 0
        #     and not self.location_item_templates.filter(item_template__is_active=True).exists()
        # ):
        #     raise ValidationError("active dungeon with item_drop_chance > 0 must have at least one active item template")

    def __str__(self) -> str:
        """Возвращает название локации подземелья."""

        return self.name


class DungeonLocationItemTemplate(TimestampedModel):
    """Связь локации подземелья с шаблоном предмета, который может выпасть."""

    location = models.ForeignKey(DungeonLocation, verbose_name="Локация", related_name="location_item_templates", on_delete=models.CASCADE)
    item_template = models.ForeignKey(ItemTemplate, verbose_name="Шаблон предмета", related_name="template_locations", on_delete=models.CASCADE)
    chance = models.PositiveSmallIntegerField("Вес выпадения", validators=[MinValueValidator(1), MaxValueValidator(100)])

    class Meta:
        unique_together = ("location", "item_template")
        constraints = [
            models.CheckConstraint(
                condition=Q(chance__gte=1, chance__lte=100),
                name="dungeon_location_item_template_chance_1_100",
            ),
        ]
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


class DungeonMiniGameDifficulty(models.TextChoices):
    """Доступные размеры memory-pairs мини-игры."""

    SIX = "6", "6/6"
    EIGHT = "8", "8/8"
    TEN = "10", "10/10"
    TWELVE = "12", "12/12"


class MiniGameCardFace(TimestampedModel):
    """SVG-лицо карточки memory-pairs, управляемое контентом из БД."""

    code = models.SlugField("Кодовое обозначение", max_length=64, unique=True)
    name = models.CharField("Название", max_length=120, blank=True, default="")
    name_i18n = models.JSONField("Переводы названия", default=dict, blank=True)
    svg_markup = models.TextField("SVG-разметка")
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Лицо карты мини-игры"
        verbose_name_plural = "Лица карт мини-игр"

    def clean(self) -> None:
        """Прогоняет SVG через санитайзер перед сохранением."""

        self.svg_markup = sanitize_svg_markup(self.svg_markup)

    def save(self, *args, **kwargs):
        """Гарантирует санитизацию даже при сохранении в обход формы."""

        self.svg_markup = sanitize_svg_markup(self.svg_markup)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает кодовое обозначение лица карты."""

        return self.code


class DungeonMiniGameConfig(TimestampedModel):
    """Настройки мини-игры: сложность, таймер и процентное ускорение прохождения."""

    name = models.CharField("Название", max_length=120)
    difficulty = models.CharField("Сложность", max_length=8, choices=DungeonMiniGameDifficulty.choices, unique=True)
    pairs_count = models.PositiveSmallIntegerField("Количество пар")
    time_limit_seconds = models.PositiveIntegerField("Лимит времени в секундах")
    reward_duration_reduction_percent = models.PositiveSmallIntegerField(
        "Процент сокращения времени забега",
        default=10,
        validators=[MaxValueValidator(100)],
    )
    max_reduction_seconds = models.PositiveIntegerField("Абсолютный потолок сокращения в секундах", default=600)
    card_face_codes = models.JSONField("Коды лиц карт", default=list, blank=True)
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "pairs_count"]
        constraints = [
            models.CheckConstraint(
                condition=Q(pairs_count__in=[6, 8, 10, 12]),
                name="dungeon_mini_game_pairs_count_allowed",
            ),
        ]
        verbose_name = "Настройка мини-игры данжа"
        verbose_name_plural = "Настройки мини-игр данжей"

    def clean(self) -> None:
        """Проверяет, что набор лиц состоит из активных кодов и покрывает все пары."""

        codes = self.card_face_codes or []
        if not isinstance(codes, list) or any(not isinstance(code, str) for code in codes):
            raise ValidationError("card_face_codes must be a list of string codes")
        if len(set(codes)) != len(codes):
            raise ValidationError("card_face_codes must not contain duplicates")
        if len(codes) < self.pairs_count:
            raise ValidationError("card_face_codes must contain at least pairs_count codes")
        existing = set(
            MiniGameCardFace.objects.filter(code__in=codes, is_active=True).values_list("code", flat=True)
        )
        missing = [code for code in codes if code not in existing]
        if missing:
            raise ValidationError(f"unknown or inactive card face codes: {', '.join(missing)}")

    def __str__(self) -> str:
        """Возвращает человекочитаемую сложность мини-игры."""

        return f"{self.name} ({self.get_difficulty_display()})"


class DungeonMiniGameAttemptStatus(models.TextChoices):
    """Статусы попытки прохождения мини-игры."""

    IN_PROGRESS = "IN_PROGRESS", "In progress"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


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
    ingredients_reward = models.JSONField("Награда ингредиентами", null=True, blank=True)
    durability_loss = models.PositiveIntegerField("Потеря прочности", null=True, blank=True)
    hp_loss = models.PositiveIntegerField("Потеря HP", null=True, blank=True)

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


class DungeonMiniGameAttempt(TimestampedModel):
    """История одной попытки пройти мини-игру ускорения для забега."""

    IN_PROGRESS = DungeonMiniGameAttemptStatus.IN_PROGRESS
    SUCCESS = DungeonMiniGameAttemptStatus.SUCCESS
    FAILED = DungeonMiniGameAttemptStatus.FAILED

    dungeon_run = models.ForeignKey(DungeonRun, verbose_name="Забег", related_name="mini_game_attempts", on_delete=models.CASCADE)
    config = models.ForeignKey(DungeonMiniGameConfig, verbose_name="Настройка", related_name="attempts", on_delete=models.PROTECT)
    user = models.ForeignKey(User, verbose_name="Пользователь", related_name="dungeon_mini_game_attempts", on_delete=models.CASCADE)
    character = models.ForeignKey(Character, verbose_name="Герой", related_name="dungeon_mini_game_attempts", on_delete=models.CASCADE)
    status = models.CharField("Статус", max_length=32, choices=DungeonMiniGameAttemptStatus.choices, default=DungeonMiniGameAttemptStatus.IN_PROGRESS)
    started_at = models.DateTimeField("Дата старта", default=timezone.now)
    expires_at = models.DateTimeField("Дата истечения таймера")
    completed_at = models.DateTimeField("Дата завершения", null=True, blank=True)
    board = models.JSONField("Карточки поля")
    matched_card_ids = models.JSONField("Открытые совпавшие карточки", default=list, blank=True)
    open_card_id = models.CharField("Текущая открытая карточка", max_length=64, blank=True, default="")
    moves_count = models.PositiveIntegerField("Количество ходов", default=0)
    matched_pairs_count = models.PositiveSmallIntegerField("Найдено пар", default=0)
    duration_reduction_seconds = models.PositiveIntegerField("Сокращение времени в секундах", default=0)
    system_error = models.BooleanField("Завершено из-за системной ошибки", default=False)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["dungeon_run"], name="unique_mini_game_attempt_per_dungeon_run"),
        ]
        verbose_name = "Попытка мини-игры данжа"
        verbose_name_plural = "Попытки мини-игр данжей"

    def __str__(self) -> str:
        """Возвращает краткое описание попытки мини-игры."""

        return f"Mini-game #{self.pk} for run #{self.dungeon_run_id} [{self.status}]"


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
