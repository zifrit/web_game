from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0007_rarityconfig_economy_multiplier"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemtemplate",
            name="rarity_key",
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True, verbose_name="Ранг предмета"),
        ),
    ]
