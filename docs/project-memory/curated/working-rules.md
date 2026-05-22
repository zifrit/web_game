# Working Rules

## Git hygiene

- Рабочее дерево может быть грязным; не откатывать и не перезаписывать чужие
  изменения без явной просьбы.
- Если новые generated/local runtime files появляются во время работы, не
  коммитить их; при необходимости добавить pattern в `.gitignore`.
- `frontend/next-env.d.ts` может переписываться Next в dev/build mode, поэтому
  перед коммитом его нужно внимательно проверить.

## Generated and local files

Не коммитить:

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

## Security

- Никогда не открывать, не читать и не анализировать `.env` и `.env.*`.
- Не выполнять команды, которые выводят содержимое `.env` файлов.
- Если задаче нужны секреты, попросить у пользователя замаскированные значения.

## Before handoff

- Backend-only change: `uv run python manage.py check` и targeted Django tests.
- API/game-flow change: добавить или обновить tests в `backend/apps/game/tests/`.
- Frontend change: `npm run build`.
- Docker/config change: `docker compose config --quiet`; если возможно,
  поднять compose и smoke-check `3000`/`8000`.
- В финальном ответе указать проверки, которые не удалось запустить, и почему.

