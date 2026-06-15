from config.celery import app

from apps.game.services import DungeonRunService

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
