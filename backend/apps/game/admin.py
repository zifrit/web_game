import json

from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.widgets import AutocompleteSelect
from django.utils.html import format_html
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
from django_celery_beat.models import PeriodicTask

from .services.config import GameConfigService
from .services.formulas import GameFormulaService

from .models import (
    AutoDungeonRun,
    AutoDungeonRunClaim,
    CeleryTaskLog,
    Character,
    CharacterClass,
    DungeonIngredientDrop,
    DungeonLimitCategory,
    DungeonLocation,
    DungeonLocationItemTemplate,
    DungeonMiniGameAttempt,
    DungeonMiniGameConfig,
    CraftRecipe,
    CraftRecipeIngredient,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunClaimItem,
    EquipmentSlotConfig,
    GameConfig,
    HeroIngredientStorage,
    HeroPotionStorage,
    IngredientTemplate,
    ItemTemplate,
    MediaAsset,
    MiniGameCardFace,
    MoneyTransaction,
    PotionTemplate,
    RarityConfig,
    RepairTransaction,
    ShopOffer,
    ShopOfferIngredient,
    ShopOfferItem,
    ShopOfferPotion,
    ShopPurchase,
    User,
    UserItem,
    UserTwoFactor,
)


class CachedSelectedAutocompleteSelect(AutocompleteSelect):
    def __init__(self, *args, selected_labels=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_labels = selected_labels or {}

    def optgroups(self, name, value, attr=None):
        default = (None, [], 0)
        groups = [default]
        selected_choices = {
            str(v) for v in value if str(v) not in self.choices.field.empty_values
        }
        if not self.is_required and not self.allow_multiple_selected:
            default[1].append(self.create_option(name, "", "", False, 0))

        choices = [
            (choice, self.selected_labels[choice])
            for choice in selected_choices
            if choice in self.selected_labels
        ]
        missing_choices = selected_choices - self.selected_labels.keys()

        if missing_choices:
            remote_model_opts = self.field.remote_field.model._meta
            to_field_name = getattr(
                self.field.remote_field, "field_name", remote_model_opts.pk.attname
            )
            to_field_name = remote_model_opts.get_field(to_field_name).attname
            choices.extend(
                (getattr(obj, to_field_name), self.choices.field.label_from_instance(obj))
                for obj in self.choices.queryset.using(self.db).filter(
                    **{"%s__in" % to_field_name: missing_choices}
                )
            )

        for index, (option_value, option_label) in enumerate(choices, start=len(default[1])):
            default[1].append(self.create_option(name, option_value, option_label, True, index))
        return groups


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "money_copper", "is_staff", "is_active", "created_at")
    search_fields = ("email",)
    autocomplete_fields = ("avatar_media",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Game", {"fields": ("money_copper", "avatar_media")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_active")} ),)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "asset_type", "original_url", "created_at")
    list_filter = ("asset_type",)
    list_display_links = ("id", "name", "asset_type")
    search_fields = ("name", "original", "large", "medium", "small")


@admin.register(UserTwoFactor)
class UserTwoFactorAdmin(admin.ModelAdmin):
    list_display = ("user", "totp_protection", "setup_pending", "confirmed_at", "last_verified_at", "updated_at")
    list_filter = ("totp_protection",)
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    readonly_fields = (
        "user",
        "totp_protection",
        "setup_pending",
        "pending_started_at",
        "confirmed_at",
        "last_verified_at",
        "last_timecode",
        "created_at",
        "updated_at",
    )
    exclude = ("active_secret_ciphertext", "pending_secret_ciphertext")

    @admin.display(boolean=True, description="Настройка начата")
    def setup_pending(self, obj):
        return bool(obj.pending_secret_ciphertext)


@admin.register(CharacterClass)
class CharacterClassAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "male_media", "female_media", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("key", "name")
    autocomplete_fields = ("male_media", "female_media")


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "character_class", "gender", "level", "experience", "power_cached")
    list_filter = ("character_class", "gender", "level")
    search_fields = ("name", "user__email")
    autocomplete_fields = ("user", "character_class", "avatar_media")
    list_select_related = ("user", "character_class", "avatar_media")
    actions = (
        "level_up_1",
        "level_up_3",
        "level_up_5",
        "level_up_10",
        "level_down_1",
        "level_down_3",
        "level_down_5",
        "level_down_10",
    )

    def _adjust_levels(self, request, queryset, delta: int) -> None:
        """Сдвигает уровень выбранных героев на delta и пересчитывает их характеристики."""

        config = GameConfigService.get_config("experience_curve_config")
        max_level = int(config.get("max_level", 20))
        updated = 0
        skipped = 0
        for character in queryset.select_related("character_class"):
            new_level = max(1, min(max_level, character.level + delta))
            if new_level == character.level:
                skipped += 1
                continue
            character.level = new_level
            # Тот же пересчёт статов от уровня, что и при клейме забега.
            GameFormulaService.apply_level_stats(character)
            character.save(
                update_fields=[
                    "level",
                    "max_hp",
                    "intellect",
                    "attack",
                    "defense",
                    "critical_chance",
                    "evasion",
                    "updated_at",
                ]
            )
            GameFormulaService.clamp_current_hp(character)
            GameFormulaService.refresh_power_cache(character)
            updated += 1
        self.message_user(
            request,
            f"Изменён уровень (Δ{delta:+d}): обновлено {updated}, пропущено {skipped} (упёрлись в лимит 1..{max_level}).",
            messages.SUCCESS if updated else messages.WARNING,
        )

    @admin.action(description="Уровень: +1")
    def level_up_1(self, request, queryset):
        self._adjust_levels(request, queryset, 1)

    @admin.action(description="Уровень: +3")
    def level_up_3(self, request, queryset):
        self._adjust_levels(request, queryset, 3)

    @admin.action(description="Уровень: +5")
    def level_up_5(self, request, queryset):
        self._adjust_levels(request, queryset, 5)

    @admin.action(description="Уровень: +10")
    def level_up_10(self, request, queryset):
        self._adjust_levels(request, queryset, 10)

    @admin.action(description="Уровень: −1")
    def level_down_1(self, request, queryset):
        self._adjust_levels(request, queryset, -1)

    @admin.action(description="Уровень: −3")
    def level_down_3(self, request, queryset):
        self._adjust_levels(request, queryset, -3)

    @admin.action(description="Уровень: −5")
    def level_down_5(self, request, queryset):
        self._adjust_levels(request, queryset, -5)

    @admin.action(description="Уровень: −10")
    def level_down_10(self, request, queryset):
        self._adjust_levels(request, queryset, -10)


class DungeonLocationItemTemplateInline(admin.TabularInline):
    model = DungeonLocationItemTemplate
    extra = 1
    fields = ("item_template", "item_rarity", "chance")
    readonly_fields = ("item_rarity",)
    autocomplete_fields = ("item_template",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("location", "item_template")

    def get_formset(self, request, obj=None, **kwargs):
        selected_labels = {}
        if obj is not None:
            selected_labels = {
                str(item_template_id): item_template_name
                for item_template_id, item_template_name in self.model.objects.filter(
                    location=obj
                ).values_list("item_template_id", "item_template__name")
            }
        request._dungeon_location_item_template_labels = selected_labels
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "item_template" and "widget" not in kwargs:
            kwargs["widget"] = CachedSelectedAutocompleteSelect(
                db_field,
                self.admin_site,
                using=kwargs.get("using"),
                selected_labels=getattr(request, "_dungeon_location_item_template_labels", {}),
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(ordering="item_template__rarity_key", description="Ранг")
    def item_rarity(self, obj):
        if not obj or not obj.item_template_id:
            return ""
        return obj.item_template.rarity_key


class DungeonIngredientDropInline(admin.TabularInline):
    model = DungeonIngredientDrop
    extra = 1
    fields = ("ingredient", "chance_percent", "min_quantity", "max_quantity")
    autocomplete_fields = ("ingredient",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("location", "ingredient")


@admin.register(DungeonLimitCategory)
class DungeonLimitCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "limit_count", "limit_period_count", "limit_period_unit", "sort_order")
    list_filter = ("limit_period_unit",)
    search_fields = ("name", "code")


@admin.register(DungeonLocation)
class DungeonLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type", "limit_category", "duration_seconds", "required_power", "hp_loss_success_percent", "hp_loss_fail_percent", "item_drop_chance", "has_mini_game", "daily_limit", "is_active", "sort_order")
    list_editable = ("location_type", "limit_category", "duration_seconds", "required_power", "hp_loss_success_percent", "hp_loss_fail_percent", "item_drop_chance", "has_mini_game", "daily_limit", "is_active", "sort_order")
    list_filter = ("location_type", "limit_category", "has_mini_game", "is_active")
    search_fields = ("name", "description")
    autocomplete_fields = ("media", "limit_category")
    inlines = [DungeonLocationItemTemplateInline, DungeonIngredientDropInline]


@admin.register(DungeonMiniGameConfig)
class DungeonMiniGameConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "difficulty",
        "pairs_count",
        "time_limit_seconds",
        "reward_duration_reduction_percent",
        "max_reduction_seconds",
        "is_active",
        "sort_order",
    )
    list_filter = ("difficulty", "is_active")
    search_fields = ("name",)


@admin.register(MiniGameCardFace)
class MiniGameCardFaceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    prepopulated_fields = {"code": ("name",)}


@admin.register(DungeonMiniGameAttempt)
class DungeonMiniGameAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dungeon_run",
        "user",
        "status",
        "difficulty",
        "moves_count",
        "matched_pairs_count",
        "duration_reduction_seconds",
        "system_error",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "system_error", "config__difficulty")
    search_fields = ("id", "user__email", "character__name", "dungeon_run__location__name")
    autocomplete_fields = ("dungeon_run", "config", "user", "character")
    list_select_related = ("dungeon_run", "dungeon_run__location", "config", "user", "character")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(ordering="config__difficulty", description="Сложность")
    def difficulty(self, obj):
        return obj.config.get_difficulty_display()


@admin.register(DungeonLocationItemTemplate)
class DungeonLocationItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "location", "item_template", "chance", "item_slot", "item_type", "item_rarity", "created_at")
    list_editable = ("chance",)
    list_filter = ("location", "chance", "item_template__slot", "item_template__item_type", "item_template__rarity_key")
    search_fields = ("location__name", "item_template__name")
    autocomplete_fields = ("location", "item_template")
    list_select_related = ("location", "item_template")

    @admin.display(ordering="item_template__slot", description="Слот")
    def item_slot(self, obj):
        return obj.item_template.slot

    @admin.display(ordering="item_template__item_type", description="Тип")
    def item_type(self, obj):
        return obj.item_template.item_type

    @admin.display(ordering="item_template__rarity_key", description="Ранг")
    def item_rarity(self, obj):
        return obj.item_template.rarity_key


@admin.register(ItemTemplate)
class ItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("id","name", "slot","allowed_classes", "item_type","rarity_key", "is_active","created_at")
    list_filter = ("slot", "item_type", "is_active","rarity_key")
    search_fields = ("name",)
    autocomplete_fields = ("media",)


@admin.register(RarityConfig)
class RarityConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "stat_multiplier", "economy_multiplier", "min_item_level", "max_item_level", "is_active", "sort_order")


@admin.register(EquipmentSlotConfig)
class EquipmentSlotConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "is_active", "sort_order")


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "is_active", "updated_at")
    search_fields = ("key", "description")


@admin.register(DungeonRun)
class DungeonRunAdmin(admin.ModelAdmin):
    list_display = ("id", "character", "location", "status", "started_at", "ends_at", "is_success","success_chance")
    list_filter = ("status", "location", "is_success")
    search_fields = ("id", "character__name", "character__user__email", "location__name", "status")
    autocomplete_fields = ("character", "location")
    list_select_related = ("character", "character__user", "character__character_class", "location")
    readonly_fields = ("created_at", "updated_at")


class DungeonRunClaimItemInline(admin.TabularInline):
    model = DungeonRunClaimItem
    extra = 0
    autocomplete_fields = ("user_item",)
    readonly_fields = ("user_item", "created_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user_item", "user_item__owner_user", "user_item__template")


@admin.register(DungeonRunClaim)
class DungeonRunClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "dungeon_run", "user", "character", "experience_claimed", "money_claimed_copper", "created_at")
    autocomplete_fields = ("dungeon_run", "user", "character")
    search_fields = ("user__email", "character__name", "dungeon_run__location__name")
    list_select_related = ("dungeon_run", "dungeon_run__location", "user", "character", "character__user", "character__character_class")
    inlines = [DungeonRunClaimItemInline]


class AutoDungeonRunClaimInline(admin.TabularInline):
    model = AutoDungeonRunClaim
    extra = 0


@admin.register(AutoDungeonRun)
class AutoDungeonRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "character",
        "location",
        "status",
        "summary_unread",
        "runs_claimed",
        "stop_reason_code",
        "started_at",
        "stopped_at",
    )
    list_filter = ("status", "summary_unread", "stop_reason_code", "location")
    search_fields = (
        "user__email",
        "character__name",
        "location__name",
        "stop_reason_message",
    )
    autocomplete_fields = ("user", "character", "location", "current_run")
    inlines = [AutoDungeonRunClaimInline]


@admin.register(AutoDungeonRunClaim)
class AutoDungeonRunClaimAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "auto_run",
        "dungeon_run",
        "claim",
        "is_success",
        "experience",
        "money_copper",
        "hp_loss",
        "counted_at",
    )
    list_filter = ("is_success",)
    search_fields = (
        "auto_run__user__email",
        "auto_run__character__name",
        "dungeon_run__location__name",
    )
    autocomplete_fields = ("auto_run", "dungeon_run", "claim")


@admin.register(UserItem)
class UserItemAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_user", "equipped_character", "slot", "rarity", "item_level", "durability_current", "durability_max")
    list_filter = ("slot", "rarity", "item_level")
    search_fields = ("name", "owner_user__email")
    autocomplete_fields = ("owner_user", "source_character", "equipped_character", "template")
    list_select_related = (
        "owner_user",
        "source_character",
        "source_character__user",
        "source_character__character_class",
        "equipped_character",
        "equipped_character__user",
        "equipped_character__character_class",
        "template",
    )


@admin.register(PotionTemplate)
class PotionTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "heal_percent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    autocomplete_fields = ("media",)


@admin.register(HeroPotionStorage)
class HeroPotionStorageAdmin(admin.ModelAdmin):
    list_display = ("character", "potion", "count")
    list_editable = ("count",)
    search_fields = ("character__name", "potion__code", "potion__name")
    autocomplete_fields = ("character", "potion")
    list_select_related = ("character", "potion")


@admin.register(IngredientTemplate)
class IngredientTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "is_active", "sort_order")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name")
    autocomplete_fields = ("media",)


class CraftRecipeIngredientInline(admin.TabularInline):
    model = CraftRecipeIngredient
    extra = 1
    fields = ("ingredient", "quantity")
    autocomplete_fields = ("ingredient",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("recipe", "ingredient")


@admin.register(CraftRecipe)
class CraftRecipeAdmin(admin.ModelAdmin):
    list_display = ("code", "difficulty", "potion", "required_hero_level", "is_active", "sort_order")
    list_filter = ("difficulty", "is_active")
    search_fields = ("code", "potion__code", "potion__name")
    autocomplete_fields = ("potion",)
    inlines = [CraftRecipeIngredientInline]


@admin.register(HeroIngredientStorage)
class HeroIngredientStorageAdmin(admin.ModelAdmin):
    list_display = ("character", "ingredient", "count")
    list_editable = ("count",)
    search_fields = ("character__name", "ingredient__code", "ingredient__name")
    autocomplete_fields = ("character", "ingredient")
    list_select_related = ("character", "ingredient")


@admin.register(RepairTransaction)
class RepairTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")
    autocomplete_fields = ("user", "item")
    list_select_related = ("user", "item", "item__owner_user", "item__template")
    readonly_fields = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")


@admin.register(MoneyTransaction)
class MoneyTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "reason", "balance_after", "created_at")
    list_filter = ("reason",)
    search_fields = ("id", "user__email", "idempotency_key")
    list_select_related = ("user",)
    readonly_fields = (
        "user",
        "amount",
        "reason",
        "balance_after",
        "idempotency_key",
        "metadata",
        "created_at",
        "updated_at",
    )


class ShopOfferIngredientInline(admin.TabularInline):
    model = ShopOfferIngredient
    extra = 1
    fields = ("ingredient_template", "chance")
    autocomplete_fields = ("ingredient_template",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("offer", "ingredient_template")


class ShopOfferPotionInline(admin.TabularInline):
    model = ShopOfferPotion
    extra = 1
    fields = ("potion_template", "chance")
    autocomplete_fields = ("potion_template",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("offer", "potion_template")


class ShopOfferItemInline(admin.TabularInline):
    model = ShopOfferItem
    extra = 1
    fields = ("item_template", "chance")
    autocomplete_fields = ("item_template",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("offer", "item_template")


@admin.register(ShopOffer)
class ShopOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "display_name",
        "reward_kind",
        "delivery_mode",
        "quantity",
        "price_money_copper",
        "price_premium_currency",
        "is_active",
        "sort_order",
        "created_at",
    )
    list_editable = ("price_money_copper", "price_premium_currency",)
    list_filter = ("reward_kind", "delivery_mode", "is_active")
    search_fields = ("id",)
    autocomplete_fields = ("media",)
    inlines = [ShopOfferIngredientInline, ShopOfferPotionInline, ShopOfferItemInline]

    @admin.display(description="Название")
    def display_name(self, obj: ShopOffer) -> str:
        """Возвращает локализованное имя предложения для колонки списка."""

        return obj.name_i18n.get("ru") or obj.name_i18n.get("en") or f"ShopOffer #{obj.id}"


@admin.register(ShopPurchase)
class ShopPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "character",
        "offer",
        "purchase_count",
        "payment_currency",
        "unit_price_snapshot",
        "total_price_snapshot",
        "reward_kind_snapshot",
        "delivery_mode_snapshot",
        "created_at",
    )
    list_filter = ("payment_currency", "reward_kind_snapshot", "delivery_mode_snapshot")
    search_fields = ("id", "user__email", "character__name")
    list_select_related = ("user", "character", "offer")
    readonly_fields = (
        "user",
        "character",
        "offer",
        "purchase_count",
        "payment_currency",
        "unit_price_snapshot",
        "total_price_snapshot",
        "reward_kind_snapshot",
        "delivery_mode_snapshot",
        "quantity_snapshot",
        "result_payload",
        "created_at",
        "updated_at",
    )

def _get_task_map() -> dict:
    from apps.game.tasks import (
        complete_due_dungeon_runs,
        daily_gift,
        process_due_auto_dungeon_runs,
    )

    return {
        "complete_due_dungeon_runs": complete_due_dungeon_runs,
        "daily_gift": daily_gift,
        "process_due_auto_dungeon_runs": process_due_auto_dungeon_runs,
    }


@admin.register(CeleryTaskLog)
class CeleryTaskLogAdmin(admin.ModelAdmin):
    list_display = ("task_name", "status_badge", "result_short", "triggered_by", "celery_task_id", "created_at")
    list_filter = ("status", "task_name")
    search_fields = ("task_name", "celery_task_id", "triggered_by__email")
    readonly_fields = ("task_name", "celery_task_id", "triggered_by", "status", "result", "created_at", "updated_at")
    actions = ("run_selected_tasks",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Статус")
    def status_badge(self, obj: CeleryTaskLog) -> str:
        colors = {
            CeleryTaskLog.Status.DISPATCHED: "#888",
            CeleryTaskLog.Status.SUCCESS: "#2e7d32",
            CeleryTaskLog.Status.FAILURE: "#c62828",
        }
        color = colors.get(obj.status, "#888")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Результат")
    def result_short(self, obj: CeleryTaskLog) -> str:
        return obj.result[:80] if obj.result else "—"

    @admin.action(description="▶ Выполнить выбранные задачи")
    def run_selected_tasks(self, request, queryset):
        task_map = _get_task_map()
        task_keys = queryset.values_list("task_name", flat=True).distinct()
        dispatched, unknown = [], []

        for task_key in task_keys:
            task_fn = task_map.get(task_key)
            if task_fn is None:
                unknown.append(task_key)
                continue
            log = CeleryTaskLog.objects.create(
                task_name=task_key,
                triggered_by=request.user,
                status=CeleryTaskLog.Status.DISPATCHED,
            )
            result = task_fn.apply_async(kwargs={"log_id": log.id})
            log.celery_task_id = result.id
            log.save(update_fields=["celery_task_id"])
            dispatched.append(task_key)

        if dispatched:
            self.message_user(
                request,
                f"Отправлено в очередь: {', '.join(dispatched)}.",
                messages.SUCCESS,
            )
        if unknown:
            self.message_user(
                request,
                f"Неизвестные задачи (пропущены): {', '.join(unknown)}.",
                messages.WARNING,
            )


try:
    admin.site.unregister(PeriodicTask)
except NotRegistered:
    pass


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(BasePeriodicTaskAdmin):
    @admin.action(description="Запустить выбранные задачи")
    def run_tasks(self, request, queryset):
        task_ids = []

        for periodic_task in queryset:
            headers = json.loads(periodic_task.headers or "{}")
            async_result = self.celery_app.send_task(
                periodic_task.task,
                args=json.loads(periodic_task.args),
                kwargs=json.loads(periodic_task.kwargs),
                queue=periodic_task.queue or None,
                exchange=periodic_task.exchange or None,
                routing_key=periodic_task.routing_key or None,
                headers={
                    **headers,
                    "periodic_task_name": periodic_task.name,
                },
            )
            task_ids.append(async_result.id)

        tasks_run = len(task_ids)
        self.message_user(
            request,
            "{0} task{1} {2} successfully run".format(
                tasks_run,
                "" if tasks_run == 1 else "s",
                "was" if tasks_run == 1 else "were",
            ),
        )
