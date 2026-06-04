from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.widgets import AutocompleteSelect

from .models import (
    Character,
    CharacterClass,
    DungeonLocation,
    DungeonLocationItemTemplate,
    DungeonMiniGameAttempt,
    DungeonMiniGameConfig,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunClaimItem,
    EquipmentSlotConfig,
    GameConfig,
    ItemTemplate,
    MediaAsset,
    MiniGameCardFace,
    RarityConfig,
    RepairTransaction,
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
    list_display = ("key", "name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("key", "name")
    autocomplete_fields = ("media",)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "character_class", "level", "experience", "power_cached")
    list_filter = ("character_class", "level")
    search_fields = ("name", "user__email")
    autocomplete_fields = ("user", "character_class", "avatar_media")
    list_select_related = ("user", "character_class", "avatar_media")


class DungeonLocationItemTemplateInline(admin.TabularInline):
    model = DungeonLocationItemTemplate
    extra = 1
    fields = ("item_template", "chance")
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


@admin.register(DungeonLocation)
class DungeonLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_seconds", "required_power", "item_drop_chance", "has_mini_game", "is_active", "sort_order")
    list_filter = ("has_mini_game", "is_active")
    search_fields = ("name", "description")
    autocomplete_fields = ("media",)
    inlines = [DungeonLocationItemTemplateInline]


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
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user_item", "user_item__owner_user", "user_item__template")


@admin.register(DungeonRunClaim)
class DungeonRunClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "dungeon_run", "user", "character", "experience_claimed", "money_claimed_copper", "created_at")
    autocomplete_fields = ("dungeon_run", "user", "character")
    list_select_related = ("dungeon_run", "dungeon_run__location", "user", "character", "character__user", "character__character_class")
    inlines = [DungeonRunClaimItemInline]


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


@admin.register(RepairTransaction)
class RepairTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")
    autocomplete_fields = ("user", "item")
    list_select_related = ("user", "item", "item__owner_user", "item__template")
    readonly_fields = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")
