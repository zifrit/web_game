from django.urls import path

from .views import (
    CharacterClassListView,
    CharacterCreateView,
    CharacterMeView,
    DungeonLocationDetailView,
    DungeonLocationListView,
    DungeonRunClaimView,
    DungeonRunCurrentView,
    DungeonRunHistoryView,
    DungeonRunStartView,
    InventoryItemDetailView,
    InventoryItemEquipView,
    InventoryItemRepairPreviewView,
    InventoryItemRepairView,
    InventoryItemUnequipView,
    InventoryView,
    LeaderboardView,
)

urlpatterns = [
    path("character-classes", CharacterClassListView.as_view(), name="character_classes"),
    path("characters", CharacterCreateView.as_view(), name="character_create"),
    path("characters/me", CharacterMeView.as_view(), name="character_me"),
    path("dungeons", DungeonLocationListView.as_view(), name="dungeon_list"),
    path("dungeons/<int:pk>", DungeonLocationDetailView.as_view(), name="dungeon_detail"),
    path("dungeon-runs", DungeonRunStartView.as_view(), name="dungeon_run_start"),
    path("dungeon-runs/current", DungeonRunCurrentView.as_view(), name="dungeon_run_current"),
    path("dungeon-runs/<int:pk>/claim", DungeonRunClaimView.as_view(), name="dungeon_run_claim"),
    path("dungeon-runs/history", DungeonRunHistoryView.as_view(), name="dungeon_run_history"),
    path("inventory", InventoryView.as_view(), name="inventory"),
    path("inventory/items/<int:item_id>", InventoryItemDetailView.as_view(), name="inventory_item_detail"),
    path("inventory/items/<int:item_id>/repair-preview", InventoryItemRepairPreviewView.as_view(), name="inventory_item_repair_preview"),
    path("inventory/items/<int:item_id>/repair", InventoryItemRepairView.as_view(), name="inventory_item_repair"),
    path("inventory/items/<int:item_id>/equip", InventoryItemEquipView.as_view(), name="inventory_item_equip"),
    path("inventory/items/<int:item_id>/unequip", InventoryItemUnequipView.as_view(), name="inventory_item_unequip"),
    path("leaderboard", LeaderboardView.as_view(), name="leaderboard"),
]

