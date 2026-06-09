---
type: curated
status: current
source_of_truth:
  - AGENTS.md
  - README.md
  - specs/
  - backend/config/settings.py
  - backend/config/urls.py
  - backend/config/celery.py
  - backend/apps/game/urls.py
  - backend/apps/game/services/ranks.py
  - backend/apps/game/services/seed_data.py
  - backend/apps/game/services/ingredients.py
  - backend/apps/game/services/consumables.py
  - backend/apps/game/services/crafting.py
  - backend/apps/game/views/auth.py
  - backend/apps/game/views/ingredients.py
  - backend/apps/game/views/consumables.py
  - backend/apps/game/views/crafting.py
  - backend/apps/game/image_generation.py
  - backend/apps/game/management/commands/seed_game.py
  - backend/apps/game/management/commands/seed_item_templates.py
  - backend/apps/game/management/commands/generate_game_images.py
  - frontend/app/page.tsx
  - frontend/lib/api.ts
  - frontend/lib/i18n.ts
  - frontend/lib/media.ts
  - frontend/lib/types.ts
  - frontend/components/rpg-client.tsx
  - frontend/components/screens/settings-screen.tsx
  - frontend/components/screens/inventory-screen.tsx
  - frontend/package.json
  - docker-compose.yml
last_verified: 2026-06-08
verified_from:
  - backend/apps/game/services/mini_games.py
  - backend/apps/game/services/mini_game_store.py
  - backend/apps/game/services/mini_game_faces.py
  - backend/apps/game/models/dungeons.py
  - backend/apps/game/views/dungeons.py
  - AGENTS.md
  - README.md
  - specs/
  - backend/config/settings.py
  - backend/config/urls.py
  - backend/apps/game/urls.py
  - backend/apps/game/tasks.py
  - backend/apps/game/models/base.py
  - backend/apps/game/models/ingredients.py
  - backend/apps/game/models/consumables.py
  - backend/apps/game/models/crafting.py
  - backend/apps/game/services/ranks.py
  - backend/apps/game/services/seed_data.py
  - backend/apps/game/services/ingredients.py
  - backend/apps/game/services/consumables.py
  - backend/apps/game/services/crafting.py
  - backend/apps/game/serializers/common.py
  - backend/apps/game/serializers/inventory.py
  - backend/apps/game/serializers/ingredients.py
  - backend/apps/game/serializers/consumables.py
  - backend/apps/game/serializers/crafting.py
  - backend/apps/game/views/auth.py
  - backend/apps/game/views/ingredients.py
  - backend/apps/game/views/consumables.py
  - backend/apps/game/views/crafting.py
  - backend/apps/game/image_generation.py
  - backend/apps/game/management/commands/generate_game_images.py
  - backend/apps/game/management/commands/seed_item_templates.py
  - backend/apps/game/management/commands/seed_game.py
  - frontend/lib/api.ts
  - frontend/lib/i18n.ts
  - frontend/lib/media.ts
  - frontend/lib/types.ts
  - frontend/components/rpg-client.tsx
  - frontend/components/screens/inventory-screen.tsx
  - frontend/components/screens/settings-screen.tsx
  - frontend/package.json
  - docker-compose.yml
---

# Project Memory Index

`docs/project-memory/` is the entry point for Browser Async RPG MVP context.
First open this index, then the relevant curated file, and use inventories for
exact lists.

## How To Use

1. Start with `INDEX.md`.
2. Read `curated/` for broad project understanding.
3. Open `inventories/` for exact lists of APIs, modules, screens, runtime
   services, and checks.
4. For codebase questions, use Graphify when `graphify-out/graph.json` exists;
   for broad navigation prefer `graphify-out/wiki/index.md` if it exists.
5. If memory, Graphify, or documentation disagrees with code, trust the code and
   update memory.

## What To Read By Request Type

- What the game is and which MVP boundaries matter:
  [curated/overview.md](curated/overview.md)
- Where backend, frontend, runtime, and main entrypoints live:
  [curated/architecture.md](curated/architecture.md)
- Backend rules for services, dungeon runs, claim, and inventory:
  [curated/backend-rules.md](curated/backend-rules.md)
- Frontend rules for the API client, state, screens, and UI intent:
  [curated/frontend-rules.md](curated/frontend-rules.md)
- Gotchas to check before changes:
  [curated/gotchas.md](curated/gotchas.md)
- Git hygiene, security, and handoff rules:
  [curated/working-rules.md](curated/working-rules.md)
- Graphify rules for codebase questions and large changes:
  [curated/working-rules.md](curated/working-rules.md)
- Public API routes:
  [inventories/api-routes.md](inventories/api-routes.md)
- Backend modules, models, services, serializers, views, and tasks:
  [inventories/backend-inventory.md](inventories/backend-inventory.md)
- Frontend entrypoints, providers, screens, libraries, and package scripts:
  [inventories/frontend-inventory.md](inventories/frontend-inventory.md)
- Runtime, Docker Compose, settings, Celery, and dependency facts:
  [inventories/runtime-and-config.md](inventories/runtime-and-config.md)
- Local run commands and prior smoke facts:
  [inventories/local-run.md](inventories/local-run.md)
- Verification commands and smoke checks:
  [inventories/verification.md](inventories/verification.md)

## How To Interpret Reliability

- Trust priority: current code; tests, migrations, schemas, configs, and
  runtime; fresh Graphify analysis; project documentation; Project Memory;
  previous discussions.
- `curated/*` is hand-written human memory: meaning, rules, navigation, and
  places where mistakes are easy.
- `inventories/*` are generated-style markdown snapshots: lists manually
  collected and confirmed against code. There is no generator in this project.
- `source_of_truth` and `verified_from` in frontmatter show where information
  came from and how it was confirmed.

## Freshness Contract

- Curated files are updated manually when architecture, product scope, domain
  rules, or local working rules change.
- Inventories are updated manually after changes to API routes, models,
  services, frontend screens, runtime config, or verification commands.
- To quickly estimate staleness risk, first check
  [curated/gotchas.md](curated/gotchas.md), then the relevant inventory.

## Principles Of This Memory Layer

- Memory does not replace code, `README.md`, or `specs/`.
- Memory should help find the source of truth quickly, not duplicate it
  wholesale.
- Graphify helps understand structure, but current code remains the source of
  truth.
- Secrets and `.env` / `.env.*` files are not read, indexed, or summarized.
