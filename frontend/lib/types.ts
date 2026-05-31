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
  two_factor?: TwoFactorStatus;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  user: User;
};

export type TwoFactorRequiredResponse = {
  two_factor_required: true;
  challenge_token: string;
};

export type LoginResponse = AuthResponse | TwoFactorRequiredResponse;

export type TwoFactorStatus = {
  totp_protection: boolean;
  setup_pending?: boolean;
};

export type TwoFactorSetup = {
  secret: string;
  otpauth_uri: string;
  qr_data_url: string;
};

export type MediaAssetUrls = {
  large_url?: string;
  medium_url?: string;
  small_url?: string;
};

export type IconAsset = MediaAssetUrls & {
  id: number;
  name: string;
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
  rank?: string;
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
  success_chance?: number;
  rewards: {
    experience: number;
    money_copper: number;
    items: Array<{
      id: number;
      name: string;
      rarity: string;
      item_level: number;
      stats: StatBlock;
      durability: {
        current: number;
        max: number;
      };
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
  media?: MediaAssetUrls | null;
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

export type InventoryMutationResponse = {
  success: boolean;
  item: InventoryCard;
  equipped_slot: EquipmentSlot;
  item_id: number;
  replaced_item: InventoryCard | null;
  equipment: Record<EquipmentSlot, InventoryCard | null>;
  stats: StatBlock;
  equipment_summary: StatBlock;
  new_power: number;
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
  item_ids: number[];
  items_count: number;
  durability_missing: number;
  repair_cost_copper: number;
  user_money_copper: number;
  can_repair: boolean;
};

export type RepairResponse = {
  success: boolean;
  item_ids: number[];
  items_count: number;
  repair_cost_copper: number;
  remaining_money_copper: number;
  durability?: {
    current: number;
    max: number;
  };
};

export type DestroyPreview = {
  item_ids: number[];
  items_count: number;
  refund_copper: number;
  user_money_copper: number;
  can_destroy: boolean;
};

export type DestroyResponse = {
  success: boolean;
  item_ids: number[];
  items_count: number;
  refund_copper: number;
  remaining_money_copper: number;
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
