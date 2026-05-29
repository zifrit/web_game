# Backend Inventory

Updated from code inspection on 2026-05-28.

## Entrypoints

- `backend/manage.py` - Django CLI.
- `backend/config/settings.py` - installed apps, REST/JWT, DB, CORS, Celery,
  storage settings.
- `backend/config/urls.py` - `admin/` and `/api/`.
- `backend/config/celery.py` - Celery app setup.
- `backend/apps/game/urls.py` - public API routes.
- `backend/apps/game/image_generation.py` - parsing/resizing/saving helpers for
  generated image assets.

## Models

- `base.py` - `TimestampedModel`, `MediaAsset` with nullable `asset_type` and
  `original`/`large`/`medium`/`small` files.
- `users.py` - `UserManager`, custom `User`.
- `characters.py` - `CharacterClass`, `Character`.
- `config.py` - `RarityConfig` with stat/economy multipliers,
  `EquipmentSlotConfig`, `GameConfig`.
- `items.py` - `ItemTemplate` with `rarity_key`, `UserItem`,
  `RepairTransaction`.
- `dungeons.py` - `DungeonLocation`, `DungeonLocationItemTemplate` with
  per-location item `chance` weights,
  `DungeonRunStatus`, `DungeonRun`, `DungeonRunClaim`, `DungeonRunClaimItem`.

`models/__init__.py` exports public model classes and `UserManager`.

## Services

`backend/apps/game/services.py` contains:

- `GameConfigService`
- `GameBalanceService`
- `GameFormulaService`
- `LootGenerationService`
- `DungeonRunService`
- `InventoryService`
- `ClaimResult`
- `item_allowed_for_character`

Inventory economy notes:

- `apps.game.ranks` maps level ranges to F/E/D/C/B/A/S/EX for both hero level
  and item level; current hero max level is 80.
- `LootGenerationService` first rolls `DungeonLocation.item_drop_chance`, then
  chooses a linked `DungeonLocationItemTemplate` by `chance`; generated item
  level and template rank stay aligned through `ItemTemplate.rarity_key`.
- Repair and destroy prices use `RarityConfig.economy_multiplier`.
- Bulk inventory endpoints are the source of truth for repair/destroy; single
  item repair endpoints delegate to the bulk service with one id.
- Destroy physically deletes `UserItem` rows and does not create a deletion log.

## Serializers and views

Serializer domains:

- `auth.py`
- `characters.py`
- `dungeons.py`
- `inventory.py`
- `leaderboard.py`
- `common.py`

Media API payloads are built in `common.py` and expose only `large_url`,
`medium_url`, `small_url`. Inventory item summaries expose `media` instead of
legacy `icon_url`.

Auth views also include avatar media endpoints: `IconAssetsView` lists
`asset_type=icons` assets and `UserAvatarUpdateView` updates `User.avatar_media`
only to an icon asset.

View domains:

- `auth.py`
- `characters.py`
- `dungeons.py`
- `inventory.py`
- `leaderboard.py`

`serializers/__init__.py` and `views/__init__.py` re-export public classes.

## Admin, commands, tests

- `backend/apps/game/admin.py` registers game/balance/admin models.
- `backend/apps/game/management/commands/seed_game.py` seeds MVP data.
- `backend/apps/game/management/commands/seed_item_templates.py` idempotently
  creates 176 ranked F-EX item templates; `seed_game` calls the same helper.
- `backend/apps/game/management/commands/generate_game_images.py` generates
  local webp image variants from CSV prompts through Polza.ai; it has dry-run,
  limit, max-images and retry behavior.
- `backend/assets/heroes_prompts.csv`, `items_prompts.csv`,
  `dungeons_prompts.csv` are current prompt feeds; `backend/assets/old/`
  contains older prompt feeds.
- `backend/generated_assets/` is ignored local output, not DB seed data.
- Tests currently include `test_mvp_api.py`, `test_services.py`,
  `test_image_generation.py`.

## Celery

- Task: `apps.game.tasks.complete_due_dungeon_runs`.
- Implementation delegates to `DungeonRunService.complete_due_runs(limit=100)`.
