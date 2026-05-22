# Backend Inventory

Updated from code inspection on 2026-05-22.

## Entrypoints

- `backend/manage.py` - Django CLI.
- `backend/config/settings.py` - installed apps, REST/JWT, DB, CORS, Celery,
  storage settings.
- `backend/config/urls.py` - `admin/` and `/api/`.
- `backend/config/celery.py` - Celery app setup.
- `backend/apps/game/urls.py` - public API routes.

## Models

- `base.py` - `TimestampedModel`, `MediaAsset`.
- `users.py` - `UserManager`, custom `User`.
- `characters.py` - `CharacterClass`, `Character`.
- `config.py` - `RarityConfig`, `EquipmentSlotConfig`, `GameConfig`.
- `items.py` - `ItemTemplate`, `UserItem`, `RepairTransaction`.
- `dungeons.py` - `DungeonLocation`, `DungeonLocationItemTemplate`,
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

## Serializers and views

Serializer domains:

- `auth.py`
- `characters.py`
- `dungeons.py`
- `inventory.py`
- `leaderboard.py`
- `common.py`

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
- `backend/apps/game/management/commands/generate_game_images.py` exists for
  game image generation.
- Tests currently include `test_mvp_api.py`, `test_services.py`,
  `test_image_generation.py`.

## Celery

- Task: `apps.game.tasks.complete_due_dungeon_runs`.
- Implementation delegates to `DungeonRunService.complete_due_runs(limit=100)`.

