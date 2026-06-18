import json

from django.db import migrations


INTERVAL_EVERY = 10
INTERVAL_PERIOD = "seconds"

PERIODIC_TASKS = [
    {
        "name": "Завершение готовых походов в данжи",
        "task": "apps.game.tasks.complete_due_dungeon_runs",
        "kwargs": {"limit": 100},
    },
    {
        "name": "Обработка готовых автозапусков данжей",
        "task": "apps.game.tasks.process_due_auto_dungeon_runs",
        "kwargs": {"limit": 100},
    },
]


def seed_dungeon_periodic_tasks(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    interval, _ = IntervalSchedule.objects.get_or_create(
        every=INTERVAL_EVERY,
        period=INTERVAL_PERIOD,
    )

    for periodic_task in PERIODIC_TASKS:
        PeriodicTask.objects.update_or_create(
            name=periodic_task["name"],
            defaults={
                "task": periodic_task["task"],
                "interval": interval,
                "crontab": None,
                "solar": None,
                "clocked": None,
                "args": "[]",
                "kwargs": json.dumps(periodic_task["kwargs"]),
                "headers": "{}",
                "enabled": True,
            },
        )


def unseed_dungeon_periodic_tasks(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    task_names = [periodic_task["name"] for periodic_task in PERIODIC_TASKS]
    PeriodicTask.objects.filter(name__in=task_names).delete()

    IntervalSchedule.objects.filter(
        every=INTERVAL_EVERY,
        period=INTERVAL_PERIOD,
    ).filter(periodictask__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0028_auto_dungeon_runs"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(
            seed_dungeon_periodic_tasks,
            reverse_code=unseed_dungeon_periodic_tasks,
        ),
    ]
