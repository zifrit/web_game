# Gotchas

- `.env` и `.env.*` не читать и не переносить в память.
- `docker-compose.yml` может ссылаться на env files; фиксировать можно только
  факт ссылки, но не читать содержимое этих файлов.
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
