# Browser Async RPG

Браузерная idle/async RPG про одного героя, данжи по таймеру, лут, экипировку,
прочность предметов, ремонт, прогрессию и таблицу лидеров. Проект находится в
MVP-границах: сервер считает игровые результаты и экономику, а frontend дает
игроку понятный игровой интерфейс без real-time боя.

## Что уже есть

- Регистрация, логин, refresh/logout и двухфакторная защита через TOTP.
- Один аккаунт - один герой, создание героя из классов персонажей.
- Данжи, запуск похода, ожидание завершения, claim награды.
- Автоматический расчет успеха, опыта, валюты, прочности и шанса лута.
- Инвентарь, экипировка, ремонт, bulk repair/destroy preview.
- Leaderboard по уровню.
- RU/EN интерфейс, аватар из backend media assets.
- Django Admin как MVP-инструмент для администрирования и баланса.
- Celery worker/beat для фонового завершения dungeon runs.
- CSV-driven pipeline генерации webp-ассетов через Polza.ai.

## Core loop

```mermaid
flowchart LR
    A["Регистрация / логин"] --> B["Создание героя"]
    B --> C["Выбор данжа"]
    C --> D["Запуск похода"]
    D --> E["Ожидание таймера"]
    E --> F["Claim награды"]
    F --> G["XP, валюта, предмет"]
    G --> H["Экипировать, починить, заменить"]
    H --> C
```

## Архитектура

```mermaid
flowchart TB
    subgraph Client["Frontend: Next 16 + React 19"]
        UI["RpgClient shell"]
        Screens["Auth, Character, Dungeons, Inventory, Leaderboard, Settings"]
        APIClient["lib/api.ts"]
        I18N["lib/i18n.ts"]
    end

    subgraph Server["Backend: Django 5.1 + DRF"]
        Views["DRF views"]
        Services["game services and formulas"]
        Models["domain models"]
        Admin["Django Admin"]
    end

    subgraph Runtime["Runtime"]
        Postgres["PostgreSQL 17"]
        Redis["Redis 7"]
        Worker["Celery worker"]
        Beat["Celery beat"]
        Media["Filesystem or S3 media"]
    end

    UI --> Screens
    Screens --> APIClient
    Screens --> I18N
    APIClient --> Views
    Views --> Services
    Services --> Models
    Admin --> Models
    Models --> Postgres
    Services --> Redis
    Beat --> Worker
    Worker --> Services
    Models --> Media
```

## Runtime-карта

```mermaid
flowchart LR
    Browser["Browser<br/>localhost:3000"] --> Frontend["frontend<br/>Next dev server"]
    Frontend --> Backend["backend<br/>localhost:8000/api"]
    Backend --> DB["postgres<br/>5432"]
    Backend --> Cache["redis<br/>6379"]
    Beat["celery_beat<br/>every 5s"] --> Worker["celery_worker"]
    Worker --> Backend
    Backend --> Admin["Django Admin<br/>localhost:8000/admin"]
```

## Репозиторий

```text
.
├── backend/                 # Django, DRF, Celery, game domain
│   ├── apps/game/           # models, serializers, views, services, tasks
│   ├── assets/              # CSV prompt feeds for image generation
│   └── config/              # settings, urls, celery, ASGI/WSGI
├── frontend/                # Next app, screens, providers, API client
├── specs/                   # MVP design, API and tech specs
├── docs/project-memory/     # project memory and inventories
├── graphify-out/            # generated code knowledge graph
└── docker-compose.yml       # local full stack
```

## Технологии

| Слой | Стек |
| --- | --- |
| Frontend | Next 16, React 19, TypeScript, Tailwind, TanStack Query, React Hook Form, Zod, lucide-react |
| Backend | Python 3.12+, Django 5.1, Django REST Framework, SimpleJWT, Celery |
| Data | PostgreSQL 17, Redis 7, filesystem/S3 media storage |
| Security | JWT refresh rotation, token blacklist, Argon2, optional TOTP |
| Assets | Pillow, django-storages, CSV prompts, Polza.ai image generation command |
| Tooling | Docker Compose, uv, npm, pytest, Graphify |

## Быстрый запуск через Docker

Создайте локальный env-файл из шаблона и поднимите stack:

```bash
cp .env.example .env
docker compose up --build
```

Локальные адреса:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`
- Django Admin: `http://localhost:8000/admin`

Создать admin-пользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

Остановить stack:

```bash
docker compose down
```

## Локальный запуск без Docker

Backend:

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_game
uv run python manage.py seed_item_templates
uv run python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Основные API-группы

```mermaid
flowchart TB
    API["/api"]
    API --> Auth["auth<br/>register, login, TOTP, refresh, logout, avatar"]
    API --> Character["character<br/>classes, create, me"]
    API --> Dungeons["dungeons<br/>list, detail, current run, claim, history"]
    API --> Inventory["inventory<br/>items, equip, repair, destroy"]
    API --> Leaderboard["leaderboard<br/>level ranking"]
    API --> Media["media<br/>icons"]
```

Ключевые routes:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/login/totp`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET|POST /api/auth/two-factor...`
- `GET /api/character-classes`
- `POST /api/characters`
- `GET /api/characters/me`
- `GET /api/dungeons`
- `POST /api/dungeon-runs`
- `GET /api/dungeon-runs/current`
- `POST /api/dungeon-runs/<id>/claim`
- `GET /api/inventory`
- `POST /api/inventory/items/repair`
- `POST /api/inventory/items/destroy`
- `POST /api/inventory/items/<id>/equip`
- `GET /api/leaderboard?type=level`
- `GET /api/media/icons`

## Gameplay constraints

```mermaid
mindmap
  root((MVP))
    One account
      One hero
    Dungeon runs
      One active run
      Server-side result
      Timer-based completion
    Inventory
      Equipment slots
      Durability
      Repair and destroy
    Excluded
      PvP
      Market
      Crafting
      Clans
      Party system
      Real-time combat
      Stamina
```

## Проверки

Frontend:

```bash
cd frontend
npm run build
```

Backend:

```bash
cd backend
uv run pytest
```

После изменений кода обновите локальный knowledge graph:

```bash
graphify update .
```

## Project memory

Для быстрой навигации по проектным решениям см. `docs/project-memory/INDEX.md`.
Если документация, Graphify и код расходятся, источником истины считается
текущий код, затем тесты/миграции/конфиги, затем свежий Graphify-отчет.

## Спецификации

- `specs/01_game_design.md` - игровые правила, классы, формулы, прогрессия.
- `specs/02_backend_models.md` - модели БД и связи.
- `specs/03_api_spec.md` - API endpoints MVP.
- `specs/04_frontend_spec.md` - экраны и frontend-flow.
- `specs/05_admin_and_balance.md` - Django Admin, баланс и игровые конфиги.
- `specs/06_tech_stack.md` - технический стек и инфраструктура.
