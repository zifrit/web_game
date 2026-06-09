# API Routes Inventory

Updated from code inspection on 2026-06-08.

Source: `backend/config/urls.py`, `backend/apps/game/urls.py`.

Root routes:

- `admin/` -> Django Admin.
- `api/` -> `apps.game.urls`.
- In `DEBUG`, media files are served from `MEDIA_URL`.

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/login/totp`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/auth/two-factor`
- `POST /api/auth/two-factor/setup`
- `POST /api/auth/two-factor/confirm`
- `POST /api/auth/two-factor/disable`
- `PATCH /api/auth/me/avatar`
- `POST /api/auth/logout`

Character:

- `GET /api/character-classes`
- `POST /api/characters`
- `GET /api/characters/me`

Dungeons:

- `GET /api/dungeons`
- `GET /api/dungeons/<id>`
- `GET /api/dungeons/<id>/loot`
- `POST /api/dungeon-runs`
- `GET /api/dungeon-runs/current`
- `POST /api/dungeon-runs/<id>/claim`
- `POST /api/dungeon-runs/<id>/mini-game/start` (body `config_id` - selected difficulty)
- `POST /api/dungeon-mini-games/<id>/reveal`
- `POST /api/dungeon-mini-games/<id>/move`
- `GET /api/dungeon-mini-games/history`
- `GET /api/mini-game/configs` (difficulty catalog with acceleration percent)
- `GET /api/mini-game/card-faces` (SVG face catalog, ETag/version)
- `GET /api/dungeon-runs/history`

Inventory:

- `GET /api/inventory`
- `POST /api/inventory/items/repair-preview`
- `POST /api/inventory/items/repair`
- `POST /api/inventory/items/destroy-preview`
- `POST /api/inventory/items/destroy`
- `GET /api/inventory/items/<item_id>`
- `GET /api/inventory/items/<item_id>/repair-preview`
- `POST /api/inventory/items/<item_id>/repair`
- `POST /api/inventory/items/<item_id>/equip`
- `POST /api/inventory/items/<item_id>/unequip`

Consumables and crafting:

- `GET /api/ingredients`
- `GET /api/potions`
- `POST /api/potions/use`
- `GET /api/craft/recipes`
- `POST /api/craft/potions`

Leaderboard:

- `GET /api/leaderboard?type=level`

Media:

- `GET /api/media/icons`
