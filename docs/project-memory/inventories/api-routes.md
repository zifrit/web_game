# API Routes Inventory

Updated from code inspection on 2026-05-25.

Source: `backend/config/urls.py`, `backend/apps/game/urls.py`.

Root routes:

- `admin/` -> Django Admin.
- `api/` -> `apps.game.urls`.
- In `DEBUG`, media files are served from `MEDIA_URL`.

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `PATCH /api/auth/me/avatar`
- `POST /api/auth/logout`

Character:

- `GET /api/character-classes`
- `POST /api/characters`
- `GET /api/characters/me`

Dungeons:

- `GET /api/dungeons`
- `GET /api/dungeons/<id>`
- `POST /api/dungeon-runs`
- `GET /api/dungeon-runs/current`
- `POST /api/dungeon-runs/<id>/claim`
- `GET /api/dungeon-runs/history`

Inventory:

- `GET /api/inventory`
- `GET /api/inventory/items/<item_id>`
- `GET /api/inventory/items/<item_id>/repair-preview`
- `POST /api/inventory/items/<item_id>/repair`
- `POST /api/inventory/items/<item_id>/equip`
- `POST /api/inventory/items/<item_id>/unequip`

Leaderboard:

- `GET /api/leaderboard?type=level`

Media:

- `GET /api/media/icons`
