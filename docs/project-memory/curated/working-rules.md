# Working Rules

## Source priority

Project Memory помогает понять намерение, но не доказывает текущую реализацию.
Порядок доверия:

1. Текущий код репозитория.
2. Тесты, миграции, схемы, конфиги и runtime-настройки.
3. Свежий Graphify-анализ, например `graphify-out/GRAPH_REPORT.md`.
4. Документация проекта.
5. `docs/project-memory/`.
6. Предыдущие обсуждения и предположения.

Если Project Memory, Graphify или документация конфликтуют с кодом, доверять
коду и после изменения обновлять соответствующие файлы памяти.

## Before changes

- Для небольших локальных изменений: изучить целевой файл, проверить ближайшие
  тесты или места использования, затем внести минимальное безопасное изменение.
- Для глубокой, архитектурной или межмодульной работы: начать с
  `docs/project-memory/INDEX.md`, открыть релевантные `curated/` и
  `inventories/`, использовать Graphify для структуры, проверить предположения
  по текущему коду, назвать план и только потом менять файлы.
- Project Memory не использовать как доказательство точных полей моделей,
  API-поведения, сигнатур, бизнес-логики, зависимостей, схемы БД, flow фоновых
  задач или текущей структуры frontend-компонентов.

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
- Не выполнять команды, которые выводят содержимое `.env` файлов, включая `cat`,
  `less`, `more`, `grep`, `rg`, `awk` и `sed` по этим файлам.
- Если задаче нужны секреты, попросить у пользователя замаскированные значения.

## Graphify

- Для codebase-вопросов сначала запускать `graphify query "<question>"`, если
  есть `graphify-out/graph.json`.
- Для отношений использовать `graphify path "<A>" "<B>"`; для фокусного
  объяснения концепта - `graphify explain "<concept>"`.
- Если есть `graphify-out/wiki/index.md`, использовать его для широкой
  навигации вместо сырого обхода исходников.
- `graphify-out/GRAPH_REPORT.md` читать только для архитектурных вопросов,
  impact analysis, cross-module changes, onboarding explanations, refactoring
  plans или когда query/path/explain не дали достаточно контекста.
- Dirty `graphify-out/` ожидаемы после hooks или incremental updates и сами по
  себе не являются причиной пропускать Graphify.
- После изменения кода запускать `graphify update .`.

## Before handoff

- Backend-only change: `uv run python manage.py check` и targeted Django tests.
- API/game-flow change: добавить или обновить tests в `backend/apps/game/tests/`.
- Frontend change: `npm run build`.
- Docker/config change: `docker compose config --quiet`; если возможно,
  поднять compose и smoke-check `3000`/`8000`.
- Docs-only project memory change: проверить измененные markdown-файлы, ссылки и
  отсутствие переноса `.env` / `.env.*` содержимого; backend/frontend build не
  нужен.
- В финальном ответе указать проверки, которые не удалось запустить, и почему.
