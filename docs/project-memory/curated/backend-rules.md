# Backend Rules

## Domain boundaries

- Нет активного `accounts` app. Auth endpoints живут в `apps.game`.
- Все публичные API endpoints монтируются под `/api/`.
- `backend/apps/game/urls.py` остается единым routes-файлом, пока явно не
  попросят split.
- Не схлопывать `models/`, `serializers/`, `views/` обратно в одиночные `.py`.

## Services first

Игровые формулы и mutating economy/game operations держать в services:

- `GameConfigService`
- `GameBalanceService`
- `GameFormulaService`
- `LootGenerationService`
- `DungeonRunService`
- `InventoryService`

Views и serializers должны оставаться тонкими. Claim, repair, equip, unequip и
start dungeon run требуют явных transactional boundaries там, где меняют
экономику или состояние героя.

## Dungeon and claim rules

- У героя может быть только один активный `IN_PROGRESS` run.
- Completion гибридный: Celery Beat завершает due runs периодически, а
  `GET /api/dungeon-runs/current` и claim flow завершают due runs on demand.
- Claim должен быть idempotent.

## Inventory and durability

- `rarity` now means F/E/D/C/B/A/S/EX rank. Hero and item level rank ranges are
  centralized in `apps.game.services.ranks`: 1-10 F through 71-80 EX.
- Dungeon loot uses `DungeonLocation.item_drop_chance` as the first item roll,
  then weighted `DungeonLocationItemTemplate.chance` links to choose the
  concrete `ItemTemplate`; rarity comes from `ItemTemplate.rarity_key`.
- Ranked item templates are command-seeded, not data-migrated:
  `seed_item_templates` creates 176 active templates via
  `apps.game.services.seed_data`, and `seed_game` calls the same helper.
- Inventory capacity в MVP unlimited.
- `slots_limit` и `free_slots` равны `null`, когда capacity unlimited.
- 24 visible pack cells - только page/window size, не лимит вместимости.
- Broken equipped items остаются equipped, не дают stats, блокируют start new
  dungeon runs и не могут быть equipped again до ремонта.
- Ремонт и уничтожение предметов считаются в `InventoryService` через массовые
  методы; одиночные сценарии передают один id в ту же bulk-логику.
- Формула ремонта:
  `rarity.economy_multiplier * ((durability_max - durability_current) * 2.5)`,
  банковское округление до целого.
- Формула уничтожения:
  `rarity.economy_multiplier * (durability_current * 2)`, банковское
  округление до целого. Уничтожение физически удаляет `UserItem`.

## Media assets

- `MediaAsset` хранит `original`, `large`, `medium`, `small`; старые `icon` и
  `thumbnail` удалены из активной модели.
- Публичный media payload возвращает только `large_url`, `medium_url`,
  `small_url`; `original_url` остается внутренним/админским URL.
- Краткие предметы inventory/equipment возвращают `media`, а не `icon_url`.
- `asset_type=icons` используется для picker аватара пользователя:
  `GET /api/media/icons` возвращает только ICONS-ассеты, а
  `PATCH /api/auth/me/avatar` принимает `avatar_media_id` и отклоняет не-icons.
- Генератор ассетов не пишет в БД: он читает CSV prompts, вызывает Polza.ai,
  сохраняет `original.webp`, `512x512.webp`, `256x256.webp`, `128x128.webp`
  в локальный output.
