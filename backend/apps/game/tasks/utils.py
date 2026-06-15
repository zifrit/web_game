from __future__ import annotations


def update_task_log(log_id: int | None, *, status: str, result: str) -> None:
    if log_id is None:
        return
    from apps.game.models import CeleryTaskLog

    CeleryTaskLog.objects.filter(pk=log_id).update(status=status, result=result)
