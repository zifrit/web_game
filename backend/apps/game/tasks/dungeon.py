from config.celery import app

from apps.game.services import DungeonRunService


@app.task(name="apps.game.tasks.complete_due_dungeon_runs", bind=True)
def complete_due_dungeon_runs(self, limit: int = 100, log_id: int | None = None) -> int:
    """Завершает просроченные активные забеги в подземелья."""

    try:
        count = DungeonRunService.complete_due_runs(limit=limit)
        _update_log(log_id, status="success", result=f"Завершено забегов: {count}")
        return count
    except Exception as exc:
        _update_log(log_id, status="failure", result=str(exc))
        raise


def _update_log(log_id: int | None, *, status: str, result: str) -> None:
    if log_id is None:
        return
    from apps.game.models import CeleryTaskLog

    CeleryTaskLog.objects.filter(pk=log_id).update(status=status, result=result)
