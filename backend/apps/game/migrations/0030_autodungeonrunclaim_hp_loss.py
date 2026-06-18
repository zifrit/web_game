from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0029_seed_dungeon_periodic_tasks"),
    ]

    operations = [
        migrations.AddField(
            model_name="autodungeonrunclaim",
            name="hp_loss",
            field=models.PositiveIntegerField(default=0, verbose_name="Потеря HP"),
        ),
    ]
