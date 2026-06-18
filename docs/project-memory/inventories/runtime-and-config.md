# Runtime And Config Inventory

Updated from code inspection on 2026-05-30.

## Docker Compose services

Source: `docker-compose.yml`, `docker-compose.prod.yml`.

- `postgres` - `postgres:17.9`, port `5432`, healthcheck via `pg_isready`.
- `redis` - `redis:7-alpine`, port `6379`, healthcheck via `redis-cli ping`.
- `backend` - builds `./backend`, migrates, seeds, runs Django on `8000`.
- `celery_worker` - builds `./backend`, runs `celery -A config worker -l info`.
- `celery_beat` - builds `./backend`, runs `celery -A config beat -l info`.
- `frontend` - builds `./frontend`, runs `npm run dev -- --hostname 0.0.0.0`
  on `3000`.
- Production `frontend` uses `frontend/Dockerfile.prod`, passes
  `NEXT_PUBLIC_API_BASE_URL` at build time, and allows overriding the npm
  registry with `NPM_REGISTRY` while defaulting to `https://registry.npmjs.org/`.

Compose references env files, but project memory must not read or reproduce
`.env` or `.env.*` contents. Current compose uses `.env` for backend and an env
example file for Celery services; only this reference fact is recorded.

## Backend settings

Source: `backend/config/settings.py`.

- Django 5.1, DRF, SimpleJWT, token blacklist, CORS, storages, `apps.game`.
- `AUTH_USER_MODEL = "game.User"`.
- DRF uses JWT authentication and `apps.game.permissions.IsSuperuserOrOwner`
  as the default permission class; views with `AllowAny` stay public.
- Default DB fallback is sqlite when `DATABASE_URL` is absent.
- Celery broker/result backend use `REDIS_URL`.
- TOTP secret encryption uses `TOTP_ENCRYPTION_KEY`, which must be a valid
  Fernet key generated with `Fernet.generate_key().decode()`.
- `POLZA_AI_API_KEY` / optional `POLZA_AI_BASE_URL` are read by the image
  generation command, not by normal app request flow.
- Beat schedule `complete-dungeon-runs` runs task
  `apps.game.tasks.complete_due_dungeon_runs` every `5.0` seconds.
- Default storage uses S3 when `AWS_STORAGE_BUCKET_NAME` is present, otherwise
  filesystem storage.

## Dependencies

Backend source: `backend/pyproject.toml`.

- Django, DRF, SimpleJWT, Celery, Redis, PostgreSQL driver, django-storages,
  CORS headers, Pillow, requests, Argon2, pyotp, qrcode, cryptography,
  pytest tooling.

Frontend source: `frontend/package.json`.

- Next 16, React 19, TypeScript, Tailwind, TanStack Query, React Hook Form,
  Zod, lucide-react, Zustand.
