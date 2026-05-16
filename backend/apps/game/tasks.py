from config.celery import app

from .services import DungeonRunService


@app.task(name="apps.game.tasks.complete_due_dungeon_runs")
def complete_due_dungeon_runs(limit: int = 100) -> int:
    return DungeonRunService.complete_due_runs(limit=limit)

