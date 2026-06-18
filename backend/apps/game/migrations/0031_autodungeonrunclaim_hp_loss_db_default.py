from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0030_autodungeonrunclaim_hp_loss"),
    ]

    operations = [
        migrations.AlterField(
            model_name="autodungeonrunclaim",
            name="hp_loss",
            field=models.PositiveIntegerField(db_default=0, default=0, verbose_name="Потеря HP"),
        ),
    ]
