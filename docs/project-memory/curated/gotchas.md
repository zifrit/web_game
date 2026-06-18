# Gotchas

- Do not read `.env` or `.env.*`, and do not copy their contents into memory.
- `docker-compose.yml` may reference env files; record only the fact of the
  reference, not the contents of those files.
- Project Memory and Graphify may become stale; when conflicts appear, trust
  current code first and then update memory.
- For codebase questions and large changes, first use scoped Graphify commands;
  read `GRAPH_REPORT.md` only for broad architecture context.
- The working tree may be dirty; do not revert user changes.
- `frontend/next-env.d.ts` may be rewritten by Next in dev/build mode.
- `frontend/components/screens/settings-screen.tsx` may be user-added; do not
  remove it without an explicit request.
- Historical migrations import `apps.game.models.UserManager`; keep
  `UserManager` exported from `backend/apps/game/models/__init__.py`.
- Celery Beat uses `django-celery-beat`'s database scheduler. Periodic task
  rows are part of runtime configuration and may be managed from Django Admin.
- Do not commit `backend/celerybeat-schedule`, `.venv`, `.next`,
  `node_modules`, sqlite db, media/cache/runtime outputs.
- `backend/generated_assets/` is image generator output and is ignored by git;
  do not treat it as a required source for the application.
- `.DS_Store` often appears in asset folders; do not record it as a useful file
  and do not commit it.
- Docker and curl/local network checks may require elevated permissions in the
  sandbox.
- `docker-compose.yml` uses `postgres:17.9`; verify cold start when changing it.
- In an old local dev DB, `game.0011_dungeon_mini_games` may have been applied
  before `DungeonMiniGameAttempt.matched_card_ids` existed;
  `0012_ensure_mini_game_matched_card_ids` keeps that DB compatible with the
  current code.
- The mini-game keeps live state in Redis (`caches["default"]`, db 1): if Redis
  is unavailable or the key is lost, an active attempt closes as `SUCCESS` with
  `system_error=true`. Card SVG faces are in the DB (`MiniGameCardFace`); seeds
  and the data migration read `backend/apps/game/data/memory_faces/` (frontend
  `public/memory-faces/` is unavailable to the backend in the container).
- Potion crafting is current MVP scope, but only for consumables. Do not infer
  market, equipment crafting, crafting stations, or generic item recipes from
  the existence of `CraftRecipe`.
