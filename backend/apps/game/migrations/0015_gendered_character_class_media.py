import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0014_backfill_power_cached"),
    ]

    operations = [
        migrations.RenameField(
            model_name="characterclass",
            old_name="media",
            new_name="male_media",
        ),
        migrations.AlterField(
            model_name="characterclass",
            name="male_media",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="male_character_classes",
                to="game.mediaasset",
                verbose_name="Мужчина",
            ),
        ),
        migrations.AddField(
            model_name="characterclass",
            name="female_media",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="female_character_classes",
                to="game.mediaasset",
                verbose_name="Женщина",
            ),
        ),
        migrations.AddField(
            model_name="character",
            name="gender",
            field=models.CharField(
                choices=[("male", "Мужчина"), ("female", "Женщина")],
                default="male",
                max_length=10,
                verbose_name="Пол",
            ),
        ),
    ]
