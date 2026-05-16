from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MediaAsset(TimestampedModel):
    original_url = models.URLField(blank=True, default="")
    large_url = models.URLField(blank=True, default="")
    medium_url = models.URLField(blank=True, default="")
    small_url = models.URLField(blank=True, default="")
    thumbnail_url = models.URLField(blank=True, default="")
    icon_url = models.URLField(blank=True, default="")

    def __str__(self) -> str:
        return self.original_url or f"Media #{self.pk}"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    money_copper = models.PositiveIntegerField(default=0)
    avatar_media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


class CharacterClass(models.Model):
    key = models.SlugField(primary_key=True)
    name = models.CharField(max_length=80)
    start_health = models.PositiveIntegerField()
    start_attack = models.PositiveIntegerField()
    start_defense = models.PositiveIntegerField()
    start_critical_chance = models.FloatField()
    start_evasion = models.FloatField()
    growth_profile = models.JSONField(default=dict)
    media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Character(TimestampedModel):
    user = models.OneToOneField(User, related_name="character", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    character_class = models.ForeignKey(CharacterClass, db_column="class_key", on_delete=models.PROTECT)
    avatar_media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL)
    level = models.PositiveIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)
    base_health = models.PositiveIntegerField()
    base_attack = models.PositiveIntegerField()
    base_defense = models.PositiveIntegerField()
    base_critical_chance = models.FloatField()
    base_evasion = models.FloatField()
    power_cached = models.FloatField(null=True, blank=True)
    power_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-level", "name"]

    def __str__(self) -> str:
        return self.name


class RarityConfig(models.Model):
    key = models.SlugField(primary_key=True)
    name = models.CharField(max_length=80)
    stat_multiplier = models.FloatField()
    min_item_level = models.PositiveIntegerField()
    max_item_level = models.PositiveIntegerField()
    min_stats_count = models.PositiveIntegerField()
    max_stats_count = models.PositiveIntegerField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order"]

    def clean(self) -> None:
        if self.min_item_level > self.max_item_level:
            raise ValidationError("min_item_level cannot exceed max_item_level")
        if self.min_stats_count > self.max_stats_count:
            raise ValidationError("min_stats_count cannot exceed max_stats_count")

    def __str__(self) -> str:
        return self.name


class EquipmentSlotConfig(models.Model):
    key = models.SlugField(primary_key=True)
    name = models.CharField(max_length=80)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self) -> str:
        return self.name


class GameConfig(TimestampedModel):
    key = models.SlugField(unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.key


class DungeonLocation(TimestampedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL)
    duration_seconds = models.PositiveIntegerField()
    required_power = models.FloatField()
    experience_min = models.PositiveIntegerField()
    experience_max = models.PositiveIntegerField()
    money_min_copper = models.PositiveIntegerField()
    money_max_copper = models.PositiveIntegerField()
    item_drop_chance = models.FloatField()
    rarity_chances = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def clean(self) -> None:
        if self.experience_min > self.experience_max:
            raise ValidationError("experience_min cannot exceed experience_max")
        if self.money_min_copper > self.money_max_copper:
            raise ValidationError("money_min_copper cannot exceed money_max_copper")
        if not 0 <= self.item_drop_chance <= 100:
            raise ValidationError("item_drop_chance must be between 0 and 100")
        if round(sum(self.rarity_chances.values())) != 100:
            raise ValidationError("rarity_chances must sum to 100")

    def __str__(self) -> str:
        return self.name


class ItemTemplate(TimestampedModel):
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

    name = models.CharField(max_length=120)
    media = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL)
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    allowed_classes = models.JSONField(null=True, blank=True)
    possible_stats = models.JSONField(default=dict)
    min_durability = models.PositiveIntegerField(default=10)
    max_durability = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["slot", "name"]

    def clean(self) -> None:
        if self.min_durability > self.max_durability:
            raise ValidationError("min_durability cannot exceed max_durability")

    def __str__(self) -> str:
        return self.name


class DungeonLocationItemTemplate(TimestampedModel):
    location = models.ForeignKey(DungeonLocation, related_name="location_item_templates", on_delete=models.CASCADE)
    item_template = models.ForeignKey(ItemTemplate, related_name="template_locations", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("location", "item_template")

    def __str__(self) -> str:
        return f"{self.location} -> {self.item_template}"


class DungeonRunStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    SUCCESS_WAITING_CLAIM = "SUCCESS_WAITING_CLAIM", "Success waiting claim"
    FAILED_WAITING_CLAIM = "FAILED_WAITING_CLAIM", "Failed waiting claim"
    CLAIMED = "CLAIMED", "Claimed"


class DungeonRun(TimestampedModel):
    IN_PROGRESS = DungeonRunStatus.IN_PROGRESS
    SUCCESS_WAITING_CLAIM = DungeonRunStatus.SUCCESS_WAITING_CLAIM
    FAILED_WAITING_CLAIM = DungeonRunStatus.FAILED_WAITING_CLAIM
    CLAIMED = DungeonRunStatus.CLAIMED

    character = models.ForeignKey(Character, related_name="dungeon_runs", on_delete=models.CASCADE)
    location = models.ForeignKey(DungeonLocation, on_delete=models.PROTECT)
    status = models.CharField(max_length=32, choices=DungeonRunStatus.choices, default=DungeonRunStatus.IN_PROGRESS)
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    success_chance = models.FloatField()
    is_success = models.BooleanField(null=True, blank=True)
    experience_reward = models.PositiveIntegerField(null=True, blank=True)
    money_reward_copper = models.PositiveIntegerField(null=True, blank=True)
    items_reward = models.JSONField(null=True, blank=True)
    durability_loss = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["character"],
                condition=Q(status=DungeonRunStatus.IN_PROGRESS),
                name="unique_in_progress_run_per_character",
            )
        ]

    def __str__(self) -> str:
        return f"{self.character} @ {self.location} [{self.status}]"


class UserItem(TimestampedModel):
    owner_user = models.ForeignKey(User, related_name="items", on_delete=models.CASCADE)
    source_character = models.ForeignKey(Character, null=True, blank=True, related_name="looted_items", on_delete=models.SET_NULL)
    equipped_character = models.ForeignKey(Character, null=True, blank=True, related_name="equipped_items", on_delete=models.SET_NULL)
    template = models.ForeignKey(ItemTemplate, on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    slot = models.CharField(max_length=20)
    item_type = models.CharField(max_length=20)
    rarity = models.CharField(max_length=20)
    item_level = models.PositiveIntegerField()
    stats = models.JSONField(default=dict)
    durability_current = models.PositiveIntegerField()
    durability_max = models.PositiveIntegerField()

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_broken(self) -> bool:
        return self.durability_current <= 0

    def __str__(self) -> str:
        return self.name


class DungeonRunClaim(models.Model):
    dungeon_run = models.OneToOneField(DungeonRun, related_name="claim", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="dungeon_claims", on_delete=models.CASCADE)
    character = models.ForeignKey(Character, related_name="dungeon_claims", on_delete=models.CASCADE)
    experience_claimed = models.PositiveIntegerField()
    money_claimed_copper = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Claim #{self.pk} for run #{self.dungeon_run_id}"


class DungeonRunClaimItem(models.Model):
    claim = models.ForeignKey(DungeonRunClaim, related_name="claim_items", on_delete=models.CASCADE)
    user_item = models.ForeignKey(UserItem, related_name="claim_links", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class RepairTransaction(models.Model):
    user = models.ForeignKey(User, related_name="repair_transactions", on_delete=models.CASCADE)
    item = models.ForeignKey(UserItem, related_name="repair_transactions", on_delete=models.CASCADE)
    cost_copper = models.PositiveIntegerField()
    durability_before = models.PositiveIntegerField()
    durability_after = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
