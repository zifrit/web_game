from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_mini_game_configs(apps, schema_editor):
    DungeonLocation = apps.get_model("game", "DungeonLocation")
    DungeonMiniGameConfig = apps.get_model("game", "DungeonMiniGameConfig")

    configs = {}
    for index, (difficulty, name, pairs_count, time_limit_seconds, reduction_seconds) in enumerate(
        [
            ("6", "Memory 6/6", 6, 45, 60),
            ("8", "Memory 8/8", 8, 60, 120),
            ("10", "Memory 10/10", 10, 75, 180),
            ("12", "Memory 12/12", 12, 90, 240),
        ]
    ):
        config, _ = DungeonMiniGameConfig.objects.update_or_create(
            difficulty=difficulty,
            defaults={
                "name": name,
                "pairs_count": pairs_count,
                "time_limit_seconds": time_limit_seconds,
                "reward_duration_reduction_seconds": reduction_seconds,
                "is_active": True,
                "sort_order": index,
            },
        )
        configs[difficulty] = config

    location_difficulties = {
        "Старый лес": "6",
        "Заброшенная тропа": "8",
        "Сырая пещера": "12",
    }
    for name, difficulty in location_difficulties.items():
        DungeonLocation.objects.filter(name=name).update(has_mini_game=True, mini_game_config=configs[difficulty])


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0010_usertwofactor"),
    ]

    operations = [
        migrations.AddField(
            model_name="dungeonlocation",
            name="has_mini_game",
            field=models.BooleanField(default=False, verbose_name="Доступна мини-игра"),
        ),
        migrations.CreateModel(
            name="DungeonMiniGameConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("name", models.CharField(max_length=120, verbose_name="Название")),
                (
                    "difficulty",
                    models.CharField(
                        choices=[("6", "6/6"), ("8", "8/8"), ("10", "10/10"), ("12", "12/12")],
                        max_length=8,
                        unique=True,
                        verbose_name="Сложность",
                    ),
                ),
                ("pairs_count", models.PositiveSmallIntegerField(verbose_name="Количество пар")),
                ("time_limit_seconds", models.PositiveIntegerField(verbose_name="Лимит времени в секундах")),
                ("reward_duration_reduction_seconds", models.PositiveIntegerField(default=30, verbose_name="Фиксированное сокращение времени в секундах")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")),
            ],
            options={
                "verbose_name": "Настройка мини-игры данжа",
                "verbose_name_plural": "Настройки мини-игр данжей",
                "ordering": ["sort_order", "pairs_count"],
            },
        ),
        migrations.AddField(
            model_name="dungeonlocation",
            name="mini_game_config",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="locations",
                to="game.dungeonminigameconfig",
                verbose_name="Настройка мини-игры",
            ),
        ),
        migrations.CreateModel(
            name="DungeonMiniGameAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                (
                    "status",
                    models.CharField(
                        choices=[("IN_PROGRESS", "In progress"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
                        default="IN_PROGRESS",
                        max_length=32,
                        verbose_name="Статус",
                    ),
                ),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата старта")),
                ("expires_at", models.DateTimeField(verbose_name="Дата истечения таймера")),
                ("completed_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата завершения")),
                ("board", models.JSONField(verbose_name="Карточки поля")),
                ("matched_card_ids", models.JSONField(blank=True, default=list, verbose_name="Открытые совпавшие карточки")),
                ("open_card_id", models.CharField(blank=True, default="", max_length=64, verbose_name="Текущая открытая карточка")),
                ("moves_count", models.PositiveIntegerField(default=0, verbose_name="Количество ходов")),
                ("matched_pairs_count", models.PositiveSmallIntegerField(default=0, verbose_name="Найдено пар")),
                ("duration_reduction_seconds", models.PositiveIntegerField(default=0, verbose_name="Сокращение времени в секундах")),
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dungeon_mini_game_attempts",
                        to="game.character",
                        verbose_name="Герой",
                    ),
                ),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="attempts",
                        to="game.dungeonminigameconfig",
                        verbose_name="Настройка",
                    ),
                ),
                (
                    "dungeon_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mini_game_attempts",
                        to="game.dungeonrun",
                        verbose_name="Забег",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dungeon_mini_game_attempts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Попытка мини-игры данжа",
                "verbose_name_plural": "Попытки мини-игр данжей",
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="dungeonminigameconfig",
            constraint=models.CheckConstraint(condition=models.Q(pairs_count__in=[6, 8, 10, 12]), name="dungeon_mini_game_pairs_count_allowed"),
        ),
        migrations.AddConstraint(
            model_name="dungeonminigameattempt",
            constraint=models.UniqueConstraint(fields=("dungeon_run",), name="unique_mini_game_attempt_per_dungeon_run"),
        ),
        migrations.RunPython(seed_mini_game_configs, migrations.RunPython.noop),
    ]
