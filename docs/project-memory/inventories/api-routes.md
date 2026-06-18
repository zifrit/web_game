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
- `POST /api/dungeon-auto-runs/current/stop`
- `POST /api/dungeon-auto-runs/current/summary/read`
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

Shop (system shop, `apps.game`):

- `GET /api/shop/offers` — lightweight active offers (no `possible_rewards`)
- `GET /api/shop/offers/<id>` — detail with `possible_rewards` (`chance` + `chance_percent`)
- `POST /api/shop/offers/<id>/buy` — body `{purchase_count, payment_currency}`; backend ignores any client price
- `GET /api/shop/purchases` — user-scoped history `{results: [...]}`
- `GET /api/auth/me` now also returns `premium_currency` (0 if no balance row)

Billing (premium currency, `apps.billing`, mounted at `/api/billing/`):

- `GET /api/billing/top-up-offers` — active real-money premium top-up packages
- `POST /api/billing/top-up-offers/<id>/top-ups` — creates a pending top-up; uses `Idempotency-Key`
- `GET /api/billing/top-ups` — user-scoped top-up attempts `{results: [...]}`
- `GET /api/billing/exchange-offers`
- `GET /api/billing/exchange-offers/<id>`
- `POST /api/billing/exchange-offers/<id>/exchange` — empty body; premium → `User.money_copper`
- `GET /api/billing/exchange-transactions` — user-scoped `{results: [...]}`
- `GET /api/billing/premium-transactions` — user-scoped `{results: [...]}`

Note: `money_copper` lives on `User`, not `Character` (spec said Character; code is source of truth). Premium balance/ledger live in `apps.billing`; all premium mutations go through `PremiumCurrencyService`. Premium top-ups track payment lifecycle separately from the premium ledger.
