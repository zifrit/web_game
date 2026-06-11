export type StatKey =
  | "max_hp"
  | "current_hp"
  | "hp_percent"
  | "intellect"
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
  premium_currency?: number;
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

export type Potion = {
  id: number;
  code: string;
  name: string;
  heal_percent: number;
  count: number;
  media?: MediaAssetUrls | null;
};

export type Ingredient = {
  id: number;
  code: string;
  name: string;
  category: string;
  count: number;
  media?: MediaAssetUrls | null;
};

export type UsePotionResponse = {
  potion_id: number;
  used: number;
  healed: number;
  current_hp: number;
  max_hp: number;
  remaining: number;
};

export type CraftRecipeIngredient = {
  ingredient_id: number;
  code: string;
  name: string;
  quantity: number;
  media?: MediaAssetUrls | null;
};

export type CraftRecipePotion = {
  id: number;
  code: string;
  name: string;
  heal_percent: number;
  media?: MediaAssetUrls | null;
};

export type CraftRecipe = {
  id: number;
  code: string;
  difficulty: "small" | "medium" | "large";
  required_hero_level: number;
  potion: CraftRecipePotion;
  ingredients: CraftRecipeIngredient[];
};

export type CraftResponse = {
  recipe_id: number;
  potion_id: number;
  potion_code: string;
  crafted: number;
  potion_count: number;
};

export type CharacterClass = {
  key: string;
  name: string;
  start_stats: StatBlock;
  media?: MediaAssetUrls | null;
  male_media?: MediaAssetUrls | null;
  female_media?: MediaAssetUrls | null;
};

export type EquipmentSlot = "weapon" | "helmet" | "armor" | "boots" | "ring";

export type Character = {
  id: number;
  name: string;
  gender?: "male" | "female";
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
  hp_loss_success_percent: number;
  hp_loss_fail_percent: number;
  item_drop_chance: number;
  has_mini_game: boolean;
  location_type: "dungeon" | "resource";
  daily_limit: number;
  daily_remaining: number | null;
  limit_category: {
    id: number;
    code: string;
    name: string;
    limit_count: number;
    period_count: number;
    period_unit: "hour" | "day" | "week" | "month";
    used: number;
    remaining: number | null;
    is_exhausted: boolean;
  };
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

export type DungeonLootItem = {
  name: string;
  slot: string;
  item_type: string;
  rarity: string | null;
  allowed_classes: string[];
  possible_stats: Record<string, RangeValue>;
  min_durability: number;
  max_durability: number;
  chance: number;
};

export type DungeonResourceDrop = {
  id: number;
  code: string;
  name: string;
  description: string;
  category: "basic" | "regional" | "rare";
  media?: MediaAssetUrls | null;
  chance_percent: number;
  min_quantity: number;
  max_quantity: number;
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
    has_mini_game?: boolean;
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
    ingredients_count: number;
    durability_loss: number;
    hp_loss: number;
  };
  mini_game?: DungeonMiniGameState | null;
};

export type CurrentRunResponse = DungeonRun | null;

export type DungeonMiniGameConfig = {
  id: number;
  difficulty: string;
  pairs_count: number;
  time_limit_seconds: number;
  reward_duration_reduction_percent: number;
  max_reduction_seconds: number;
};

export type DungeonMiniGameCard = {
  id: string;
  position: number;
  state: "hidden" | "open" | "temporary_open" | "matched";
  code?: string | null;
};

export type MiniGameCardFace = {
  code: string;
  name: string;
  svg: string;
};

export type MiniGameCardFaceCatalog = {
  version: number;
  faces: MiniGameCardFace[];
};

export type DungeonMiniGameAttemptStatus =
  | "IN_PROGRESS"
  | "SUCCESS"
  | "FAILED";

export type DungeonMiniGameAttempt = {
  id: number;
  status: DungeonMiniGameAttemptStatus;
  config: DungeonMiniGameConfig;
  started_at: string;
  expires_at: string;
  completed_at?: string | null;
  board?: DungeonMiniGameCard[];
  moves_count: number;
  matched_pairs_count: number;
  duration_reduction_seconds: number;
  system_error?: boolean;
};

export type DungeonMiniGameMoveAttempt = {
  id: number;
  status: DungeonMiniGameAttemptStatus;
  moves_count: number;
  matched_pairs_count: number;
};

export type DungeonMiniGameReward = {
  type: "dungeon_time_boost_seconds";
  value: number;
} | null;

export type DungeonMiniGameFinishedResponse = {
  finished: true;
  matched: boolean | null;
  attempt: DungeonMiniGameAttempt;
  opened_cards: DungeonMiniGameCard[];
  reward_granted: boolean;
  reward?: DungeonMiniGameReward;
};

export type DungeonMiniGameMoveResponse =
  | {
      finished: false;
      matched: boolean;
      attempt: DungeonMiniGameMoveAttempt;
      opened_cards: DungeonMiniGameCard[];
      reward_granted: false;
      reward: null;
    }
  | DungeonMiniGameFinishedResponse;

export type DungeonMiniGameRevealResponse =
  | { finished: false; card: DungeonMiniGameCard }
  | DungeonMiniGameFinishedResponse;

export type DungeonMiniGameState = {
  available: boolean;
  started: boolean;
  status?: DungeonMiniGameAttemptStatus | null;
  attempt_id?: number | null;
};

export type DungeonMiniGameHistoryItem = {
  id: number;
  dungeon_run_id: number;
  location_name: string;
  status: DungeonMiniGameAttemptStatus;
  difficulty: string;
  pairs_count: number;
  reward_duration_reduction_percent: number;
  started_at: string;
  expires_at: string;
  completed_at?: string | null;
  moves_count: number;
  matched_pairs_count: number;
  duration_reduction_seconds: number;
  system_error?: boolean;
};

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
    durability_changes: Array<{
      name: string;
      slot: EquipmentSlot;
      durability: {
        current: number;
        max: number;
      };
      removed: number;
    }>;
    hp_loss: number;
    ingredients: Array<{
      id: number;
      code: string;
      name: string;
      quantity: number;
      media?: MediaAssetUrls | null;
    }>;
  };
  hp?: {
    current: number;
    max: number;
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

export type LeaderboardMetric = "level" | "power";

export type Leaderboard = {
  type: LeaderboardMetric;
  items: Array<{
    rank: number;
    character_id: number;
    character_name: string;
    class: {
      key: string;
      name: string;
    };
    level: number;
    power: number;
    avatar?: MediaAssetUrls | null;
  }>;
  my_rank?: {
    rank: number;
    character_id: number;
    level?: number;
    power?: number;
  } | null;
};

export type ShopRewardKind = "ingredient" | "potion" | "item";
export type ShopDeliveryMode = "single" | "chest";
export type PaymentCurrency = "money_copper" | "premium_currency";

export type ShopPrices = {
  money_copper?: number;
  premium_currency?: number;
};

export type ShopOffer = {
  id: number;
  reward_kind: ShopRewardKind;
  delivery_mode: ShopDeliveryMode;
  name: string;
  description: string;
  quantity: number;
  prices: ShopPrices;
  media?: MediaAssetUrls | null;
};

export type ShopPossibleReward = {
  type: ShopRewardKind;
  template_id: number;
  name: string;
  rarity_key?: string;
  chance: number;
  chance_percent: number;
  media?: MediaAssetUrls | null;
};

export type ShopOfferDetail = ShopOffer & {
  possible_rewards: ShopPossibleReward[];
};

export type ShopPurchaseResult = {
  ingredients?: Array<{ template_id: number; quantity: number }>;
  potions?: Array<{ template_id: number; quantity: number }>;
  items?: Array<{ user_item_id: number; template_id: number; rarity_key: string }>;
};

export type ShopPurchase = {
  id: number;
  offer_id: number;
  offer_name?: string;
  purchase_count: number;
  payment_currency: PaymentCurrency;
  unit_price: number;
  total_price: number;
  reward_kind: ShopRewardKind;
  delivery_mode: ShopDeliveryMode;
  quantity: number;
  result: ShopPurchaseResult;
  created_at?: string;
};

export type BuyShopOfferResponse = {
  purchase: ShopPurchase;
  balances: { money_copper: number; premium_currency: number };
};

export type ExchangeOffer = {
  id: number;
  premium_cost: number;
  money_copper_reward: number;
  is_active?: boolean;
};

export type ExchangeTransaction = {
  id: number;
  premium_spent: number;
  money_copper_received: number;
  created_at?: string;
};

export type ExchangeResponse = {
  transaction: ExchangeTransaction;
  balances: { premium_currency: number; money_copper: number };
};

export type PremiumTransaction = {
  id: number;
  amount: number;
  reason: string;
  balance_after: number;
  metadata: Record<string, unknown>;
  created_at?: string;
};
