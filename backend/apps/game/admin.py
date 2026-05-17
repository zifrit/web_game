from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Character,
    CharacterClass,
    DungeonLocation,
    DungeonLocationItemTemplate,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunClaimItem,
    EquipmentSlotConfig,
    GameConfig,
    ItemTemplate,
    MediaAsset,
    RarityConfig,
    RepairTransaction,
    User,
    UserItem,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "money_copper", "is_staff", "is_active", "created_at")
    search_fields = ("email",)
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
    list_display = ("id", "name", "original_url", "icon_url", "created_at")
    search_fields = ("name", "original", "large", "medium", "small", "thumbnail", "icon")


@admin.register(CharacterClass)
class CharacterClassAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("key", "name")


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "character_class", "level", "experience", "power_cached")
    list_filter = ("character_class", "level")
    search_fields = ("name", "user__email")


class DungeonLocationItemTemplateInline(admin.TabularInline):
    model = DungeonLocationItemTemplate
    extra = 1


@admin.register(DungeonLocation)
class DungeonLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_seconds", "required_power", "item_drop_chance", "is_active", "sort_order")
    list_filter = ("is_active",)
    inlines = [DungeonLocationItemTemplateInline]


@admin.register(ItemTemplate)
class ItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slot", "item_type", "is_active", "min_durability", "max_durability")
    list_filter = ("slot", "item_type", "is_active")
    search_fields = ("name",)


@admin.register(RarityConfig)
class RarityConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "stat_multiplier", "min_item_level", "max_item_level", "is_active", "sort_order")


@admin.register(EquipmentSlotConfig)
class EquipmentSlotConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "is_active", "sort_order")


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "is_active", "updated_at")
    search_fields = ("key", "description")


@admin.register(DungeonRun)
class DungeonRunAdmin(admin.ModelAdmin):
    list_display = ("id", "character", "location", "status", "started_at", "ends_at", "is_success")
    list_filter = ("status", "location", "is_success")
    readonly_fields = ("created_at", "updated_at")


class DungeonRunClaimItemInline(admin.TabularInline):
    model = DungeonRunClaimItem
    extra = 0
    readonly_fields = ("user_item", "created_at")
    can_delete = False


@admin.register(DungeonRunClaim)
class DungeonRunClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "dungeon_run", "user", "character", "experience_claimed", "money_claimed_copper", "created_at")
    inlines = [DungeonRunClaimItemInline]


@admin.register(UserItem)
class UserItemAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_user", "equipped_character", "slot", "rarity", "item_level", "durability_current", "durability_max")
    list_filter = ("slot", "rarity", "item_level")
    search_fields = ("name", "owner_user__email")


@admin.register(RepairTransaction)
class RepairTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")
    readonly_fields = ("user", "item", "cost_copper", "durability_before", "durability_after", "created_at")
