# Verification Inventory

Updated from code inspection on 2026-05-22.

Use the smallest useful checks for the touched area.

## Backend

- `cd backend && uv run python manage.py check` - Django config/system check.
- `cd backend && uv run python manage.py test apps.game` - game app tests.

## Frontend

- `cd frontend && npm run build` - Next production build/type integration.

## Docker and smoke

- `docker compose config --quiet` - compose syntax/config validation.
- `docker compose up --build` - full local stack.
- `docker compose up --build -d` - detached full stack.
- `docker compose ps` - service status.
- `docker compose logs --tail=80 backend frontend celery_worker celery_beat` -
  focused service logs.
- `curl http://127.0.0.1:8000/api/character-classes` - backend API smoke.
- `curl -I http://127.0.0.1:3000` - frontend HTTP smoke.

Docker daemon and local network checks may need elevated permissions in the
Codex sandbox.

## Documentation-only changes

For docs-only project memory updates:

- inspect changed markdown files;
- confirm links/paths match the repo;
- confirm no `.env` or `.env.*` content was read or copied;
- no backend/frontend build is required.

