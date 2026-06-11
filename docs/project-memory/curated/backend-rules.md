# Backend Rules

## Domain boundaries

- There is no active `accounts` app. Auth endpoints live in `apps.game`.
- All public API endpoints are mounted under `/api/`.
- `backend/apps/game/urls.py` remains the single routes file unless a split is
  explicitly requested.
- Do not collapse `models/`, `serializers/`, or `views/` back into single
  `.py` files.

## Services first

Keep game formulas and mutating economy/game operations in services:

- `GameConfigService`
- `GameBalanceService`
- `GameFormulaService`
- `LootGenerationService`
- `DungeonRunService`
- `DungeonMiniGameService`
- `InventoryService`
- `IngredientService`
- `PotionService`
- `CraftService`
- `MoneyService` (copper wallet)

## Currency wallets

Each currency is mutated through exactly one deep wallet module; no caller
touches a balance field directly.

- Copper (`game.User.money_copper`) goes through `MoneyService` in
  `apps.game.services.money`. Premium currency
  (`billing.UserPremiumBalance.amount`) goes through `PremiumCurrencyService` in
  `apps.billing`.
- Both wallets expose the same verbs: `grant` (add), `charge` (remove, enforces
  the non-negative invariant), and `get_amount`. `grant`/`charge` self-lock the
  balance row, write an immutable ledger row (`MoneyTransaction` /
  `PremiumCurrencyTransaction`), and return that transaction; callers read the
  resulting balance from `transaction.balance_after`.
- `charge` accepts an optional `insufficient_message` i18n key so callers keep
  context-specific errors (e.g. `not_enough_money_repair`,
  `shop_not_enough_money`).
- Because the wallet self-locks, callers no longer `select_for_update` the
  `User` row just to mutate copper. Copper-touching paths (dungeon claim, shop
  purchase, repair, destroy refund, premium→copper exchange) delegate to
  `MoneyService`.
- Multi-currency callers go through one seam: `apps.game.services.wallets`
  exposes `get_wallet(currency_key)` (keys `"money_copper"` /
  `"premium_currency"`, matching `ShopPurchase.PaymentCurrency` values) and
  `all_balances(user)` for the `balances` response payload. `ShopService` and
  `CurrencyExchangeService` charge/grant via the returned `Wallet` adapter
  instead of branching on currency. Shop has no direct `billing.services`
  import; the premium adapter imports billing lazily (billing depends on game,
  not the reverse).
- Premium top-ups are payment lifecycle records, not wallet ledger rows. A
  top-up stores the offer snapshot, provider identifiers, status, and future
  refund metadata; only `PremiumTopUpService.mark_succeeded` grants premium
  currency through `PremiumCurrencyService` and links the resulting ledger row.
  The v1 top-up API creates `pending` records without a provider checkout URL;
  no public webhook endpoint exists until a concrete provider/signature adapter
  is added.

Views and serializers should stay thin. Claim, repair, equip, unequip, and
start dungeon run require explicit transactional boundaries where they change
economy or hero state. Ingredient rewards, potion use, and potion crafting
should also go through services instead of being calculated in views.

## Dungeon and claim rules

- A hero can have only one active `IN_PROGRESS` run.
- `DungeonLocation.location_type` describes behavior (`dungeon` vs `resource`);
  `DungeonLocation.limit_category` is a separate balance group for shared run
  limits across locations. Per-location `daily_limit` and category limits are
  both spent at run start and count all run statuses by `started_at`.
- Completion is hybrid: Celery Beat periodically completes due runs, while
  `GET /api/dungeon-runs/current` and the claim flow complete due runs on
  demand. All on-demand completion goes through one self-locking seam:
  `DungeonRunService.finalize_due_run(run_id)` opens its own transaction,
  takes `select_for_update` on the run, re-checks the IN_PROGRESS/due guard
  under the lock, rolls the outcome, and returns the run. Callers never
  finalize an unlocked run — the GET path and Celery loop both go through it.
  `_finalize_locked(run)` is the inner worker for callers that already hold the
  lock (claim, batch); it returns whether the run actually transitioned. This
  closes the race where the unlocked GET path could roll a divergent outcome
  against the beat task.
- Claim must be idempotent.
- The acceleration mini-game is available for an active run when the location
  has `has_mini_game=true`; the player chooses difficulty (`config_id`) at
  start, and it is fixed on the run (one attempt per run).
- Live attempt state (board, counters) lives in Redis; a single final snapshot
  is written to the database. Scoring is server-authoritative and moves are
  idempotent.
- Success reduces run time by `reward_duration_reduction_percent` of the full
  dungeon duration, capped by `max_reduction_seconds` and clamped no earlier
  than the start time; edits to `ends_at` happen under `select_for_update(run)`
  and only while `IN_PROGRESS`.
- If the Redis key for an active attempt is lost, the attempt closes as
  `SUCCESS` with `system_error=true` and full acceleration.

## Inventory and durability

- `rarity` now means F/E/D/C/B/A/S/EX rank. Hero and item level rank ranges are
  centralized in `apps.game.services.ranks`: 1-10 F through 71-80 EX.
- `Character` stores intrinsic hero stats as `health`, `attack`, `defense`,
  `critical_chance`, and `evasion`. These are class + level stats without
  equipment; `GameFormulaService.character_stats` adds equipment dynamically.
- Dungeon loot uses `DungeonLocation.item_drop_chance` as the first item roll,
  then weighted `DungeonLocationItemTemplate.chance` links to choose the
  concrete `ItemTemplate`; rarity comes from `ItemTemplate.rarity_key`.
- Ranked item templates are command-seeded, not data-migrated:
  `seed_item_templates` creates 176 active templates via
  `apps.game.services.seed_data`, and `seed_game` calls the same helper.
- Inventory capacity is unlimited in the MVP.
- `slots_limit` and `free_slots` are `null` when capacity is unlimited.
- 24 visible pack cells are only the page/window size, not a capacity limit.
- Broken equipped items remain equipped, provide no stats, block starting new
  dungeon runs, and cannot be equipped again until repaired.
- Repair and destroy are calculated in `InventoryService` through bulk methods;
  single-item scenarios pass one id into the same bulk logic.
- Repair formula:
  `rarity.economy_multiplier * ((durability_max - durability_current) * 2.5)`,
  banker's rounding to integer.
- Destroy formula:
  `rarity.economy_multiplier * (durability_current * 2)`, banker's rounding to
  integer. Destroy physically deletes `UserItem`.

## Consumables and crafting

- Hero storage counts (ingredients, potions) are mutated through exactly one
  deep seam: `apps.game.services.storages`. One generic `HeroStorage(model,
  fk_field)` backs `INGREDIENT_STORAGE` and `POTION_STORAGE`; both expose
  `deposit` (add, get-or-creates the row) and `withdraw` (remove, self-locks,
  enforces non-negative, returns the row with the new count). No caller touches
  the `count` field directly. Verbs are `deposit`/`withdraw` — deliberately
  distinct from the wallet's `grant`/`charge`, since storages are not currencies
  and have no ledger. `craft_potions` withdraws ingredients in deterministic
  `ingredient_id` order (deadlock-safe) and deposits potions; `use_potion`
  withdraws potions; dungeon claim deposits ingredient drops.
- Ingredients are a separate hero storage, not inventory items. Dungeon
  ingredient drops are independent per-location rolls from
  `DungeonIngredientDrop`.
- Potions are a separate hero storage. `PotionService.use_potion` locks the
  character and potion storage, heals against backend `max_hp`, decrements the
  stack, and rejects use at full HP.
- Potion crafting is recipe-driven. `CraftRecipe.difficulty` maps to small,
  medium, or large recipe tabs; each recipe points to one `PotionTemplate` and
  has `CraftRecipeIngredient` slots.
- `CraftService.craft_potions` is transactional: it locks the hero and matching
  ingredient storages, checks level and ingredient counts, decrements
  ingredients, then increments `HeroPotionStorage`.
- Current seed data creates small, medium and large healing recipes; large
  healing requires hero level 5. Do not treat this as generic item/equipment
  crafting.

## Media assets

- `MediaAsset` stores `original`, `large`, `medium`, and `small`; legacy `icon`
  and `thumbnail` fields were removed from the active model.
- Public media payloads return only `large_url`, `medium_url`, and `small_url`;
  `original_url` remains an internal/admin URL.
- Short inventory/equipment items return `media`, not `icon_url`.
- `CharacterClass` stores separate `male_media`/`female_media` portraits; public
  `/api/character-classes` temporarily keeps `media` as a male-portrait
  compatibility alias. Hero creation requires `gender`, and
  `Character.avatar_media` is set from the selected class and gender media with
  fallback to the available class portrait.
- `asset_type=icons` is used for the user avatar picker: `GET /api/media/icons`
  returns only ICONS assets, and `PATCH /api/auth/me/avatar` accepts
  `avatar_media_id` while rejecting non-icon assets.
- The asset generator does not write to the database: it reads CSV prompts,
  calls Polza.ai, and saves `original.webp`, `512x512.webp`, `256x256.webp`,
  and `128x128.webp` to local output.
