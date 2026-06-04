# Gotchas

- `.env` и `.env.*` не читать и не переносить в память.
- `docker-compose.yml` может ссылаться на env files; фиксировать можно только
  факт ссылки, но не читать содержимое этих файлов.
- Project Memory и Graphify могут устаревать; при конфликте доверять текущему
  коду, затем обновлять память.
- Для codebase-вопросов и больших изменений сначала использовать scoped Graphify
  commands, а `GRAPH_REPORT.md` читать только для широкой архитектурной картины.
- Рабочее дерево может быть грязным; не откатывать чужие изменения.
- `frontend/next-env.d.ts` может переписываться Next в dev/build mode.
- `frontend/components/screens/settings-screen.tsx` может быть user-added;
  не удалять без явной просьбы.
- Historical migrations импортируют `apps.game.models.UserManager`; держать
  `UserManager` exported из `backend/apps/game/models/__init__.py`.
- Celery Beat configured через `CELERY_BEAT_SCHEDULE` в settings, не через
  `django-celery-beat`; Beat models не должны ожидаться в Django Admin.
- `backend/celerybeat-schedule`, `.venv`, `.next`, `node_modules`, sqlite db,
  media/cache/runtime outputs не коммитить.
- `backend/generated_assets/` - output генератора изображений и игнорируется
  git; не считать его обязательным source для приложения.
- `.DS_Store` часто встречается в asset folders; не переносить в память как
  полезный файл и не коммитить.
- Docker и curl/local network checks могут требовать elevated permissions в
  sandbox.
- `docker-compose.yml` использует `postgres:17.9`; при изменении verify cold
  start.
- В старой локальной dev-БД `game.0011_dungeon_mini_games` мог быть применён до
  появления `DungeonMiniGameAttempt.matched_card_ids`; `0012_ensure_mini_game_matched_card_ids`
  держит такую БД совместимой с текущим кодом.
- Мини-игра держит live-стейт в Redis (`caches["default"]`, db 1): если Redis
  недоступен/ключ потерян, активная партия закрывается как `SUCCESS` с
  `system_error=true`. SVG-лица карт — в БД (`MiniGameCardFace`); сиды и
  data-миграция читают `backend/apps/game/data/memory_faces/` (фронтовый
  `public/memory-faces/` бэкенду в контейнере недоступен).
