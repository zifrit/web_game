# AGENTS.md

## Project Memory

This repository is the Browser Async RPG MVP: a browser idle/async RPG where one account owns one hero, sends that hero into timed dungeon runs, claims rewards, manages loot/equipment durability, repairs items, and progresses on a level leaderboard.

The original product documentation lives in `README.md` and `specs/`. Treat those files as the source of product intent unless the user explicitly changes the scope.

## Current Architecture

- Monorepo layout:
  - `backend/` — Django 5.1, Django REST Framework, SimpleJWT, Celery, Redis, PostgreSQL.
  - `frontend/` — Next.js, React, TypeScript, Tailwind, TanStack Query, React Hook Form, Zod.
  - `docker-compose.yml` — local stack: backend, frontend, postgres, redis, celery worker, celery beat.
- Backend code is concentrated in `backend/apps/game/`.
- `apps.game.models`, `apps.game.serializers`, and `apps.game.views` are package directories split by domain. Their `__init__.py` files intentionally re-export public classes/functions so compatibility imports such as `from apps.game.models import Character`, `from apps.game.serializers import InventorySerializer`, and `from apps.game.views import InventoryView` continue to work.
- There is no active `accounts` Django app. Auth endpoints are implemented inside `apps.game`.
- All public API endpoints are mounted under `/api/`.
- Django Admin is the MVP admin/balance CMS.
- Celery Beat is configured from `CELERY_BEAT_SCHEDULE` in Django settings, not from `django-celery-beat`; therefore Celery Beat models do not appear in Django Admin.

## Important Backend Files

- `backend/config/settings.py` — Django settings, REST framework, JWT, Celery schedule, env parsing.
- `backend/config/urls.py` — only includes `admin/` and `api/ -> apps.game.urls`.
- `backend/config/celery.py` — Celery app setup.
- `backend/apps/game/models/` — custom `User`, character, dungeon, item, claim, config, repair models split by domain:
  - `base.py` — `TimestampedModel`, `MediaAsset`.
  - `users.py` — `UserManager`, custom `User`.
  - `characters.py` — `CharacterClass`, `Character`.
  - `config.py` — rarity, equipment slot, and game config models.
  - `items.py` — item templates, user items, repair transactions.
  - `dungeons.py` — dungeon locations, run status/runs, claims, claim items.
- `backend/apps/game/services.py` — game domain logic; keep formulas and transactions here.
- `backend/apps/game/serializers/` — DRF serializers/renderers split by domain: `common.py`, `auth.py`, `characters.py`, `dungeons.py`, `inventory.py`, `leaderboard.py`.
- `backend/apps/game/views/` — DRF API views split by domain: `auth.py`, `characters.py`, `dungeons.py`, `inventory.py`, `leaderboard.py`.
- `backend/apps/game/urls.py` — single API routes file; keep it as a file for now, not a `urls/` package.
- `backend/apps/game/management/commands/seed_game.py` — seed data for classes, dungeons, rarities, slots, item templates, configs.
- `backend/apps/game/tests/` — backend/API tests.

## Important Frontend Files

- `frontend/app/page.tsx` — main client app entry currently used by Next.
- `frontend/app/globals.css` — global styling.
- `frontend/lib/api.ts` — API client, token storage, compatibility facade.
- `frontend/lib/types.ts` — shared frontend API types.
- `frontend/components/` — componentized UI screens and shared providers.
- `frontend/components/screens/settings-screen.tsx` may exist as an uncommitted/user-added screen; do not remove it unless asked.

## MVP Rules

- One account has one hero.
- One hero can have only one active `IN_PROGRESS` dungeon run.
- No PvP, market, crafting, clans, stamina, party system, or real-time combat in MVP.
- The client must not calculate critical game formulas; server returns calculated values.
- Mutating game/economy operations should go through services and be transactional where relevant.
- Broken equipped items:
  - remain equipped,
  - do not contribute stats,
  - block starting new dungeon runs,
  - cannot be equipped again until repaired.
- Inventory capacity is currently unlimited. Do not treat the 24 visible pack cells as a capacity limit; they are only the page/window size for display and pagination.
- Claim must be idempotent.
- Dungeon completion is hybrid:
  - Celery Beat periodically completes due runs,
  - `GET /api/dungeon-runs/current` and claim flow also complete due runs on demand.

## API Memory

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Core game:

- `GET /api/character-classes`
- `POST /api/characters`
- `GET /api/characters/me`
- `GET /api/dungeons`
- `GET /api/dungeons/{id}`
- `POST /api/dungeon-runs`
- `GET /api/dungeon-runs/current`
- `POST /api/dungeon-runs/{id}/claim`
- `GET /api/dungeon-runs/history`
- `GET /api/inventory?page=1&page_size=24`
- `GET /api/inventory/items/{id}`
- `GET /api/inventory/items/{id}/repair-preview`
- `POST /api/inventory/items/{id}/repair`
- `POST /api/inventory/items/{id}/equip`
- `POST /api/inventory/items/{id}/unequip`
- `GET /api/leaderboard?type=level`

Inventory response memory:

- `slots_limit` is `null` in MVP, meaning unlimited capacity.
- `items_count` is the total number of user items across all pages.
- `free_slots` is `null` when capacity is unlimited.
- `pagination` includes `page`, `page_size`, `total_items`, `total_pages`, `has_next`, and `has_previous`.
- Backend caps `page_size` at 24.
- Frontend should render at least 24 visible cells, but load further pages when scrolling if `pagination.has_next` is true.

## Local Run

Copy env first:

```bash
cp .env.example .env
```

Preferred local stack:

```bash
docker compose up --build
```

Detached:

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=80 backend frontend celery_worker celery_beat
```

URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`
- Django Admin: `http://localhost:8000/admin`

Create admin user:

```bash
docker compose exec backend python manage.py createsuperuser
```

Stop stack:

```bash
docker compose down
```

## Local Non-Docker Run

Backend:

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_game
uv run python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Verification Commands

Backend checks:

```bash
cd backend
uv run python manage.py check
uv run python manage.py test apps.game
```

Frontend build:

```bash
cd frontend
npm run build
```

Compose syntax:

```bash
docker compose config --quiet
```

Smoke checks after compose starts:

```bash
curl http://127.0.0.1:8000/api/character-classes
curl -I http://127.0.0.1:3000
```

Known verified behavior from prior compose run:

- Backend migrated and seeded successfully.
- Frontend served the login screen on port `3000`.
- `GET /api/character-classes` returned 4 classes.
- API smoke passed through register, auth/me, create character, dungeons, start run, current run.
- Claim smoke passed: run moved to `SUCCESS_WAITING_CLAIM`, claim returned `CLAIMED`, money was credited.
- Celery Beat sent `complete_due_dungeon_runs`; Celery worker received and completed the task.

## Generated Files And Git Hygiene

Do not commit generated/local runtime files:

- `.env`
- `.venv/`
- `backend/.venv/`
- `backend/db.sqlite3`
- `backend/celerybeat-schedule`
- `frontend/node_modules/`
- `frontend/.next/`
- `frontend/tsconfig.tsbuildinfo`
- `.DS_Store`
- `.idea/`

If new generated files appear, add them to `.gitignore` instead of committing them.

## Current Gotchas

- Do not reintroduce `apps.accounts.urls`; that app was removed from the active backend. Auth routes belong in `apps.game.urls`.
- Do not collapse `backend/apps/game/models/`, `serializers/`, or `views/` back into single `.py` files. The domain packages and their re-exporting `__init__.py` files are intentional.
- Historical migrations import `apps.game.models.UserManager`; keep `UserManager` exported from `backend/apps/game/models/__init__.py`.
- Keep `backend/apps/game/urls.py` as the single routes file until the user explicitly asks to split urls.
- `frontend/next-env.d.ts` can be rewritten by Next depending on dev/build mode. Review before committing.
- `docker-compose.yml` currently uses `postgres:17.9`; if changing it, verify cold start with Docker.
- `celerybeat-schedule` appears in `backend/` because the backend directory is bind-mounted into Celery Beat. It should stay ignored.
- Some Docker/curl checks may need elevated permissions in the Codex sandbox because Docker daemon and local network access can be blocked.
- The working tree may be dirty with user frontend changes. Never revert or overwrite those unless the user explicitly asks.

## Design And Implementation Preferences

- Keep backend game formulas centralized in `GameFormulaService`, `GameConfigService`, `GameBalanceService`, `LootGenerationService`, `DungeonRunService`, and `InventoryService`.
- Keep serializers/views thin; do not spread game math across views or frontend.
- Prefer explicit transactional boundaries for claim, repair, equip, and dungeon run start.
- Keep frontend API access through `frontend/lib/api.ts`.
- Prefer invalidating TanStack Query data after claim/equip/unequip/repair/auth changes.
- Keep the UI as the actual game interface, not a landing page.

## Before Handing Off

When making code changes, run the smallest useful checks:

- Backend-only change: `uv run python manage.py check` and targeted Django tests.
- API/game-flow change: add or update tests in `backend/apps/game/tests/`.
- Frontend change: `npm run build`.
- Docker/config change: `docker compose config --quiet`; if feasible, start compose and smoke `3000`/`8000`.

Report any checks that could not be run and why.
