# Backend Inventory

Updated from code inspection on 2026-06-08.

## Entrypoints

- `backend/manage.py` - Django CLI.
- `backend/config/settings.py` - installed apps, REST/JWT, DB, CORS, Celery,
  storage settings.
- `backend/config/urls.py` - `admin/` and `/api/`.
- `backend/config/celery.py` - Celery app setup.
- `backend/apps/game/urls.py` - public API routes.
- `backend/apps/game/permissions.py` - shared DRF owner/superuser permission
  used as the default private API permission.
- `backend/apps/game/two_factor.py` - encrypted TOTP secret helpers, QR data
  URL generation, login challenge signing and replay-aware TOTP verification.
- `backend/apps/game/image_generation.py` - parsing/resizing/saving helpers for
  generated image assets.

## Models

- `base.py` - `TimestampedModel`, `MediaAsset` with nullable `asset_type` and
  `original`/`large`/`medium`/`small` files.
- `users.py` - `UserManager`, custom `User`, `UserTwoFactor` for opt-in TOTP
  protection.
- `characters.py` - `CharacterClass` with gendered class media,
  `Character` with `gender`, hero avatar media, and level-scaled intrinsic
  stats stored on the hero; equipment stats are still added dynamically.
- `config.py` - `RarityConfig` with stat/economy multipliers,
  `EquipmentSlotConfig`, `GameConfig`.
- `items.py` - `ItemTemplate` with `rarity_key`, `UserItem`,
  `RepairTransaction`.
- `ingredients.py` - `IngredientTemplate`, per-hero `HeroIngredientStorage`,
  and `DungeonIngredientDrop` with independent per-location drop rolls.
- `consumables.py` - `PotionTemplate` and per-hero `HeroPotionStorage`.
- `crafting.py` - `CraftRecipe` and `CraftRecipeIngredient` for recipe-driven
  potion crafting.
- `dungeons.py` - `DungeonLimitCategory` for shared run limits,
  `DungeonLocation` with `has_mini_game` (gates availability; no FK to a config
  anymore),
  `DungeonLocationItemTemplate` with per-location item `chance` weights,
  `DungeonMiniGameConfig` (percent reward + `max_reduction_seconds` +
  `card_face_codes`), `MiniGameCardFace` (inline-SVG catalog),
  `DungeonMiniGameAttempt` (with `system_error`), `DungeonRunStatus`,
  `DungeonRun`, `DungeonRunClaim`, `DungeonRunClaimItem`.

`models/__init__.py` exports public model classes and `UserManager`.

Billing models live in `backend/apps/billing/models.py`:

- `UserPremiumBalance` stores one premium currency balance per user.
- `PremiumCurrencyTransaction` is the immutable premium currency ledger.
- `PremiumTopUpOffer`, `PremiumTopUp`, and `PremiumTopUpEvent` model real-money
  premium top-up packages, payment lifecycle records, and future webhook events.
- `CurrencyExchangeOffer` and `CurrencyExchangeTransaction` model premium to
  copper exchange offers and successful exchanges.

## Services

`backend/apps/game/services/` contains a compatibility facade in `__init__.py`
and domain modules:

- `config.py` - `DEFAULT_CONFIGS`, `DEFAULT_RARITIES`, config/rarity caches and
  `GameConfigService`
- `balance.py` - `GameBalanceService`
- `formulas.py` - `GameFormulaService`
- `loot.py` - `LootGenerationService` and `item_allowed_for_character`
- `dungeon_runs.py` - `DungeonRunService`, `ClaimResult`
- `auto_runs.py` - `AutoDungeonRunService` start/stop/summary state plus worker
  claim accounting and next-run processing.
- `mini_games.py` - `DungeonMiniGameService`; live memory-pairs state lives in
  Redis during play, with a single DB flush on finish (server-authoritative
  scoring, percent run-time reduction capped by `max_reduction_seconds`)
- `mini_game_store.py` - `MiniGameStore` (Redis state + per-run lock)
- `mini_game_faces.py` - loads seed SVG faces from `apps/game/data/memory_faces/`
- `inventory.py` - `InventoryService`
- `ingredients.py` - `IngredientService` and `IngredientDropService`
- `consumables.py` - `PotionService`
- `crafting.py` - `CraftService`
- `ranks.py` - F/E/D/C/B/A/S/EX rank ranges and helpers
- `reference_cache.py` - shared reference/leaderboard cache helpers and cache
  version bumping.
- `seed_data.py` - ranked item template seed helpers

The `apps.game.services` facade exports:

- `GameConfigService`
- `GameBalanceService`
- `GameFormulaService`
- `LootGenerationService`
- `DungeonRunService`
- `DungeonMiniGameService`
- `InventoryService`
- `IngredientDropService`
- `IngredientService`
- `ClaimResult`
- `CraftService`
- `PotionService`
- `item_allowed_for_character`

Billing services live in `backend/apps/billing/services.py`:

- `PremiumCurrencyService` is the premium wallet and the only writer of
  `UserPremiumBalance.amount`.
- `PremiumTopUpService` creates pending top-ups and idempotently marks them
  succeeded by granting premium currency through the wallet ledger.
- `CurrencyExchangeService` exchanges premium currency for `money_copper`.

Inventory economy notes:

- `apps.game.services.ranks` maps level ranges to F/E/D/C/B/A/S/EX for both
  hero level and item level; current hero max level is 80.
- `LootGenerationService` first rolls `DungeonLocation.item_drop_chance`, then
  chooses a linked `DungeonLocationItemTemplate` by `chance`; generated item
  level and template rank stay aligned through `ItemTemplate.rarity_key`.
- Repair and destroy prices use `RarityConfig.economy_multiplier`.
- Bulk inventory endpoints are the source of truth for repair/destroy; single
  item repair endpoints delegate to the bulk service with one id.
- Destroy physically deletes `UserItem` rows and does not create a deletion log.

Consumables and crafting notes:

- Ingredient rewards are stored in `HeroIngredientStorage`; they are not
  `UserItem` rows and do not consume inventory capacity.
- `IngredientDropService.roll_drops` rolls each configured
  `DungeonIngredientDrop` independently.
- `PotionService.use_potion` locks the character and potion storage, heals by
  `GameFormulaService.potion_heal`, and returns current/max HP plus remaining
  potion count.
- `CraftService.craft_potions` locks the hero and ingredient storages, validates
  active recipe, hero level and counts, then decrements ingredients and
  increments `HeroPotionStorage`.

## Serializers and views

Serializer domains:

- `auth.py`
- `characters.py`
- `dungeons.py`
- `inventory.py`
- `ingredients.py`
- `consumables.py`
- `crafting.py`
- `leaderboard.py`
- `common.py`

Media API payloads are built in `common.py` and expose only `large_url`,
`medium_url`, `small_url`. Character classes expose `male_media` and
`female_media`, with `media` retained as a male-media compatibility alias.
Inventory item summaries expose `media` instead of legacy `icon_url`.

Auth views also include avatar media endpoints: `IconAssetsView` lists
`asset_type=icons` assets and `UserAvatarUpdateView` updates `User.avatar_media`
only to an icon asset.

Auth views include TOTP endpoints. Protected password login returns a short-lived
`challenge_token`; `POST /api/auth/login/totp` verifies the code before issuing
JWT tokens. Settings-driven setup uses pending secrets and only flips
`totp_protection=true` after confirmation; disable requires password + TOTP.

View domains:

- `auth.py`
- `characters.py`
- `dungeons.py`
- `inventory.py`
- `ingredients.py`
- `consumables.py`
- `crafting.py`
- `leaderboard.py`

`apps.billing` has its own serializers, views, urls, admin, and tests for
premium balance, top-ups, exchange offers, exchange transactions, and premium
ledger history. Billing routes are mounted separately at `/api/billing/`.

`serializers/__init__.py` and `views/__init__.py` re-export public classes.

DRF private endpoints use `apps.game.permissions.IsSuperuserOrOwner` by
default. Existing `AllowAny` views remain public; user-scoped endpoints still
query through `request.user`, so superuser bypass does not add impersonation.

## Admin, commands, tests

- `backend/apps/game/admin.py` registers game/balance/admin models.
- `backend/apps/game/management/commands/seed_game.py` seeds MVP data.
- `backend/apps/game/management/commands/seed_item_templates.py` idempotently
  creates 176 ranked F-EX item templates; `seed_game` calls the same helper.
- `seed_game.py` also seeds active ingredients, healing potions, dungeon
  ingredient drops, and small/medium/large healing recipes.
- `backend/apps/game/management/commands/generate_game_images.py` generates
  local webp image variants from CSV prompts through Polza.ai; it has dry-run,
  limit, max-images and retry behavior.
- `backend/assets/heroes_prompts.csv`, `items_prompts.csv`,
  `dungeons_prompts.csv` are current prompt feeds; `backend/assets/old/`
  contains older prompt feeds.
- `backend/generated_assets/` is ignored local output, not DB seed data.
- Tests currently include `test_mvp_api.py`, `test_services.py`,
  `test_auto_runs.py`, `test_image_generation.py`.

## Celery

- Task: `apps.game.tasks.complete_due_dungeon_runs`.
- Implementation delegates to `DungeonRunService.complete_due_runs(limit=100)`.
- Task: `apps.game.tasks.process_due_auto_dungeon_runs`.
- Implementation delegates to
  `AutoDungeonRunService.process_due_auto_runs(limit=100)`.
