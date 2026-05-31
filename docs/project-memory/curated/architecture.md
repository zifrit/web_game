# Architecture

Проект - monorepo с backend, frontend и Docker stack.

## Backend

- `backend/config/` - Django settings, root urls, Celery app, WSGI/ASGI.
- `backend/apps/game/` - активный backend-домен MVP.
- `backend/apps/game/urls.py` - единый файл API routes под `/api/`.
- `backend/apps/game/models/` - доменные модели, разбитые по файлам.
- `backend/apps/game/serializers/` - DRF serializers/renderers по доменам.
- `backend/apps/game/views/` - DRF API views по доменам.
- `backend/apps/game/services/` - package для формул, транзакций,
  game-domain operations, рангов и seed helpers; `__init__.py` сохраняет
  compatibility imports из `apps.game.services`.
- `backend/apps/game/tasks.py` - Celery tasks.
- `backend/apps/game/management/commands/seed_game.py` - seed data.
- `backend/apps/game/image_generation.py` и
  `backend/apps/game/management/commands/generate_game_images.py` - CSV-driven
  pipeline генерации webp-ассетов через Polza.ai.
- `backend/assets/*_prompts.csv` - prompt feeds для heroes/items/dungeons.
- `backend/generated_assets/` - локальный output генерации; он игнорируется
  git и не является source-of-truth для кода.

`apps.game.models`, `apps.game.serializers`, `apps.game.views` и
`apps.game.services` являются package-директориями. Их `__init__.py`
реэкспортируют публичные классы для compatibility imports.

## Frontend

- `frontend/app/page.tsx` - Next entry для основного приложения.
- `frontend/components/rpg-client.tsx` - главный клиентский shell, nav и выбор
  экранов.
- `frontend/components/screens/` - игровые экраны.
- `frontend/components/providers.tsx` - session и locale providers.
- `frontend/lib/api.ts` - API client, token storage, compatibility facade.
- `frontend/lib/types.ts` - shared API types.
- `frontend/lib/i18n.ts` - dictionaries и formatting helpers.
- `frontend/lib/media.ts` - helper выбора `large_url`/`medium_url`/`small_url`.

UI должен оставаться настоящим игровым интерфейсом, не landing page.
Settings screen включает смену языка, аккаунт/активного героя и picker аватара
из backend `MediaAsset` с типом `icons`.

## Runtime

`docker-compose.yml` поднимает PostgreSQL, Redis, backend, frontend,
Celery worker и Celery beat. Public URLs локально: frontend `localhost:3000`,
backend API `localhost:8000/api`, admin `localhost:8000/admin`.
