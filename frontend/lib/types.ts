export type StatKey =
  | "health"
  | "attack"
  | "defense"
  | "critical_chance"
  | "evasion"
  | "power";

export type StatBlock = Partial<Record<StatKey, number>>;

export type User = {
  id: number;
  email: string;
  money_copper?: number;
  has_character: boolean;
  avatar?: MediaAssetUrls | null;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  user: User;
};

export type MediaAssetUrls = {
  original_url?: string;
  large_url?: string;
  medium_url?: string;
  small_url?: string;
  icon_url?: string;
};

export type CharacterClass = {
  key: string;
  name: string;
  start_stats: StatBlock;
  media?: MediaAssetUrls | null;
};

export type EquipmentSlot = "weapon" | "helmet" | "armor" | "boots" | "ring";

export type Character = {
  id: number;
  name: string;
  avatar?: MediaAssetUrls | null;
  class?: {
    key: string;
    name: string;
    media?: MediaAssetUrls | null;
  };
  class_key?: string;
  level: number;
  experience: number;
  experience_to_next_level?: number;
  stats?: StatBlock;
  equipment?: Record<EquipmentSlot, InventoryCard | null>;
};

export type Dungeon = {
  id: number;
  name: string;
  description: string;
  duration_seconds: number;
  required_power: number;
  success_chance: number;
  item_drop_chance: number;
  media?: MediaAssetUrls | null;
  rewards_preview?: {
    experience?: RangeValue;
    money_copper?: RangeValue;
  };
};

export type RangeValue = {
  min: number;
  max: number;
};

export type DungeonRunStatus =
  | "IN_PROGRESS"
  | "SUCCESS_WAITING_CLAIM"
  | "FAILED_WAITING_CLAIM"
  | "CLAIMED";

export type DungeonRun = {
  id: number;
  status: DungeonRunStatus;
  location: {
    id: number;
    name: string;
  };
  started_at?: string;
  ends_at?: string;
  remaining_seconds?: number;
  success_chance?: number;
  result_preview?: {
    is_success: boolean;
    experience: number;
    money_copper: number;
    items_count: number;
    durability_loss: number;
  };
};

export type CurrentRunResponse = DungeonRun | null;

export type ClaimResponse = {
  id: number;
  status: "CLAIMED";
  is_success: boolean;
  rewards: {
    experience: number;
    money_copper: number;
    items: Array<{
      id: number;
      name: string;
      rarity: string;
      item_level: number;
    }>;
    durability_loss: number;
  };
  level_up?: {
    old_level: number;
    new_level: number;
  } | null;
};

export type InventoryCard = {
  id: number;
  name?: string;
  icon_url?: string;
  slot: EquipmentSlot;
  rarity: string;
  durability?: {
    current: number;
    max: number;
  };
  is_broken: boolean;
};

export type Inventory = {
  equipment_summary: StatBlock;
  equipped: Record<EquipmentSlot, InventoryCard | null>;
  items_count: number;
  slots_limit: number | null;
  free_slots: number | null;
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  items: InventoryCard[];
};

export type ItemDetail = {
  id: number;
  name: string;
  slot: EquipmentSlot;
  item_type: string;
  rarity: string;
  item_level: number;
  stats: StatBlock;
  durability: {
    current: number;
    max: number;
  };
  is_equipped: boolean;
  is_broken: boolean;
  can_equip: boolean;
  media?: MediaAssetUrls | null;
};

export type RepairPreview = {
  item_id: number;
  durability: {
    current: number;
    max: number;
    missing: number;
  };
  repair_cost_copper: number;
  user_money_copper: number;
  can_repair: boolean;
};

export type Leaderboard = {
  type: "level";
  items: Array<{
    rank: number;
    character_id: number;
    character_name: string;
    class: {
      key: string;
      name: string;
    };
    level: number;
    avatar?: MediaAssetUrls | null;
  }>;
  my_rank?: {
    rank: number;
    character_id: number;
    level: number;
  } | null;
};
