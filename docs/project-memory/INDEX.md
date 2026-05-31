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
  - backend/apps/game/views/auth.py
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
  - frontend/package.json
  - docker-compose.yml
last_verified: 2026-05-31
verified_from:
  - AGENTS.md
  - README.md
  - specs/
  - backend/config/settings.py
  - backend/config/urls.py
  - backend/apps/game/urls.py
  - backend/apps/game/tasks.py
  - backend/apps/game/models/base.py
  - backend/apps/game/services/ranks.py
  - backend/apps/game/services/seed_data.py
  - backend/apps/game/serializers/common.py
  - backend/apps/game/serializers/inventory.py
  - backend/apps/game/views/auth.py
  - backend/apps/game/image_generation.py
  - backend/apps/game/management/commands/generate_game_images.py
  - backend/apps/game/management/commands/seed_item_templates.py
  - frontend/lib/api.ts
  - frontend/lib/i18n.ts
  - frontend/lib/media.ts
  - frontend/lib/types.ts
  - frontend/components/rpg-client.tsx
  - frontend/components/screens/settings-screen.tsx
  - frontend/package.json
  - docker-compose.yml
---

# Project Memory Index

`docs/project-memory/` - точка входа в контекст Browser Async RPG MVP. Сначала
открывай этот индекс, затем нужный curated-файл, а за точными списками переходи
в inventories.

## Как пользоваться

1. Начинай с `INDEX.md`.
2. Для общего понимания проекта читай `curated/`.
3. Для точных списков API, модулей, экранов, runtime-сервисов и проверок
   открывай `inventories/`.
4. Для codebase-вопросов используй Graphify, если есть `graphify-out/graph.json`;
   для широкой навигации предпочитай `graphify-out/wiki/index.md`, если он
   существует.
5. Если память, Graphify или документация расходятся с кодом, доверяй коду и
   обновляй память.

## Что читать по типу запроса

- Что это за игра и какие MVP-границы важны:
  [curated/overview.md](curated/overview.md)
- Где находятся backend, frontend, runtime и основные entrypoints:
  [curated/architecture.md](curated/architecture.md)
- Какие backend-правила важны для services, dungeon runs, claim и inventory:
  [curated/backend-rules.md](curated/backend-rules.md)
- Какие frontend-правила важны для API client, state, screens и UI intent:
  [curated/frontend-rules.md](curated/frontend-rules.md)
- Какие gotchas нужно проверить перед изменениями:
  [curated/gotchas.md](curated/gotchas.md)
- Какие правила git hygiene, security и handoff важны:
  [curated/working-rules.md](curated/working-rules.md)
- Какие правила Graphify важны для вопросов по кодовой базе и больших
  изменений:
  [curated/working-rules.md](curated/working-rules.md)
- Нужен список публичных API routes:
  [inventories/api-routes.md](inventories/api-routes.md)
- Нужна карта backend modules, models, services, serializers, views и tasks:
  [inventories/backend-inventory.md](inventories/backend-inventory.md)
- Нужна карта frontend entrypoints, providers, screens, libs и package scripts:
  [inventories/frontend-inventory.md](inventories/frontend-inventory.md)
- Нужны runtime, Docker Compose, settings, Celery и dependency facts:
  [inventories/runtime-and-config.md](inventories/runtime-and-config.md)
- Нужны команды локального запуска и prior smoke facts:
  [inventories/local-run.md](inventories/local-run.md)
- Нужны команды проверки и smoke checks:
  [inventories/verification.md](inventories/verification.md)

## Как понимать достоверность

- Приоритет доверия: текущий код; тесты, миграции, схемы, конфиги и runtime;
  свежий Graphify-анализ; документация проекта; Project Memory; предыдущие
  обсуждения.
- `curated/*` - ручная память для человека: смысл, правила, навигация и места,
  где легко ошибиться.
- `inventories/*` - generated-style markdown snapshots: списки, вручную
  собранные и подтвержденные кодом. Генератора в этом проекте нет.
- `source_of_truth` и `verified_from` в frontmatter показывают, откуда взята и
  чем подтверждена информация.

## Контракт актуальности

- Curated-файлы обновляются вручную, когда меняется архитектура, product scope,
  domain rules или локальные правила работы.
- Inventories обновляются вручную после изменений API routes, моделей,
  services, frontend screens, runtime config или verification-команд.
- Если нужно быстро понять риск устаревания, сначала смотри
  [curated/gotchas.md](curated/gotchas.md), затем relevant inventory.

## Принципы этого слоя памяти

- Память не заменяет код, `README.md` или `specs/`.
- Память должна помогать быстро найти source-of-truth, а не дублировать его
  целиком.
- Graphify помогает понять структуру, но текущий код остается источником истины.
- Секреты и `.env` / `.env.*` файлы не читаются, не индексируются и не
  пересказываются.
