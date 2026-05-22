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
  - frontend/app/page.tsx
  - frontend/components/rpg-client.tsx
last_verified: 2026-05-22
verified_from:
  - AGENTS.md
  - README.md
  - specs/
  - backend/config/settings.py
  - backend/config/urls.py
  - backend/apps/game/urls.py
  - backend/apps/game/tasks.py
  - frontend/lib/api.ts
  - frontend/components/rpg-client.tsx
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
4. Если память расходится с кодом, доверяй коду и обновляй память.

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
- Нужен список публичных API routes:
  [inventories/api-routes.md](inventories/api-routes.md)
- Нужна карта backend modules, models, services, serializers, views и tasks:
  [inventories/backend-inventory.md](inventories/backend-inventory.md)
- Нужна карта frontend entrypoints, providers, screens, libs и package scripts:
  [inventories/frontend-inventory.md](inventories/frontend-inventory.md)
- Нужны runtime, Docker Compose, settings, Celery и dependency facts:
  [inventories/runtime-and-config.md](inventories/runtime-and-config.md)
- Нужны команды проверки и smoke checks:
  [inventories/verification.md](inventories/verification.md)

## Как понимать достоверность

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
- Секреты и `.env` / `.env.*` файлы не читаются, не индексируются и не
  пересказываются.

