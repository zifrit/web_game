from config.celery import app

from apps.game.services import AutoDungeonRunService, DungeonRunService

from .utils import update_task_log


@app.task(name="apps.game.tasks.complete_due_dungeon_runs", bind=True)
def complete_due_dungeon_runs(self, limit: int = 100, log_id: int | None = None) -> int:
    """Завершает просроченные активные забеги в подземелья."""

    try:
        count = DungeonRunService.complete_due_runs(limit=limit)
        update_task_log(log_id, status="success", result=f"Завершено забегов: {count}")
        return count
    except Exception as exc:
        update_task_log(log_id, status="failure", result=str(exc))
        raise


@app.task(name="apps.game.tasks.process_due_auto_dungeon_runs", bind=True)
def process_due_auto_dungeon_runs(self, limit: int = 100, log_id: int | None = None) -> int:
    """Обрабатывает готовые автозапуски: claim текущего забега и старт следующего."""

    try:
        count = AutoDungeonRunService.process_due_auto_runs(limit=limit)
        update_task_log(log_id, status="success", result=f"Обработано автозапусков: {count}")
        return count
    except Exception as exc:
        update_task_log(log_id, status="failure", result=str(exc))
        raise
