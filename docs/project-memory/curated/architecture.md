# Architecture

The project is a monorepo with a backend, frontend, and Docker stack.

## Backend

- `backend/config/` - Django settings, root URLs, Celery app, WSGI/ASGI.
- `backend/apps/game/` - active backend domain for the MVP.
- `backend/apps/game/urls.py` - single API routes file under `/api/`.
- `backend/apps/game/models/` - domain models split by file.
- `backend/apps/game/serializers/` - DRF serializers/renderers by domain.
- `backend/apps/game/views/` - DRF API views by domain.
- `backend/apps/game/services/` - package for formulas, transactions,
  game-domain operations, ranks, and seed helpers; `__init__.py` preserves
  compatibility imports from `apps.game.services`.
- `backend/apps/game/tasks.py` - Celery tasks.
- `backend/apps/game/management/commands/seed_game.py` - seed data.
- `backend/apps/game/image_generation.py` and
  `backend/apps/game/management/commands/generate_game_images.py` - CSV-driven
  pipeline for generating webp assets through Polza.ai.
- The consumables domain lives next to inventory: ingredients
  (`ingredients.py`), potions (`consumables.py`), and brewing recipes
  (`crafting.py`) are represented as models, serializers, views, and services.
- `backend/assets/*_prompts.csv` - prompt feeds for heroes/items/dungeons.
- `backend/generated_assets/` - local generation output; ignored by git and not
  a source of truth for code.

`apps.game.models`, `apps.game.serializers`, `apps.game.views`, and
`apps.game.services` are package directories. Their `__init__.py` files
re-export public classes for compatibility imports.

## Frontend

- `frontend/app/page.tsx` - Next entry for the main application.
- `frontend/components/rpg-client.tsx` - main client shell, navigation, and
  screen selection.
- `frontend/components/screens/` - game screens.
- `frontend/components/providers.tsx` - session and locale providers.
- `frontend/lib/api.ts` - API client, token storage, compatibility facade.
- `frontend/lib/types.ts` - shared API types.
- `frontend/lib/i18n.ts` - dictionaries and formatting helpers.
- `frontend/lib/media.ts` - helper for choosing
  `large_url`/`medium_url`/`small_url`.

The UI should remain a real game interface, not a landing page. The settings
screen includes language switching, account/active-hero information, and an
avatar picker backed by `MediaAsset` rows with type `icons`. The inventory
screen has equipment and consumables sections; consumables shows ingredients,
potions, and the potion brewing panel.

## Runtime

`docker-compose.yml` starts PostgreSQL, Redis, backend, frontend, Celery worker,
and Celery beat. Local public URLs: frontend `localhost:3000`, backend API
`localhost:8000/api`, admin `localhost:8000/admin`.
