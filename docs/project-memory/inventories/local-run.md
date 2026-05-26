# Local Run Inventory

Updated from code inspection and project memory consolidation on 2026-05-25.

## Docker run

Create a local env file from the example before running the stack. Do not read
or copy secret values into project memory.

```bash
cp .env.example .env
docker compose up --build
```

Detached:

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=80 backend frontend celery_worker celery_beat
```

Local URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`
- Django Admin: `http://localhost:8000/admin`

Admin user:

```bash
docker compose exec backend python manage.py createsuperuser
```

Generate image assets dry-run:

```bash
docker compose exec backend python manage.py generate_game_images assets/heroes_prompts.csv --dry-run
```

Stop stack:

```bash
docker compose down
```

## Non-Docker run

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

## Prior verified smoke behavior

- Backend migrated and seeded successfully.
- Frontend served the login screen on port `3000`.
- `GET /api/character-classes` returned 4 classes.
- API smoke passed through register, auth/me, create character, dungeons, start
  run, current run.
- Claim smoke passed: run moved to `SUCCESS_WAITING_CLAIM`, claim returned
  `CLAIMED`, money was credited.
- Celery Beat sent `complete_due_dungeon_runs`; Celery worker received and
  completed the task.
