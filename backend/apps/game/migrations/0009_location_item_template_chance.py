from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def backfill_location_item_template_chances(apps, schema_editor):
    DungeonLocationItemTemplate = apps.get_model("game", "DungeonLocationItemTemplate")

    links = DungeonLocationItemTemplate.objects.select_related("location", "item_template")
    for link in links:
        rarity_chances = link.location.rarity_chances or {}
        chance = int(rarity_chances.get(link.item_template.rarity_key, 0) or 0)
        if chance <= 0:
            link.delete()
            continue
        link.chance = min(chance, 100)
        link.save(update_fields=["chance", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0008_itemtemplate_rarity_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="dungeonlocationitemtemplate",
            name="chance",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[MinValueValidator(1), MaxValueValidator(100)],
                verbose_name="Вес выпадения",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="dungeonlocationitemtemplate",
            constraint=models.CheckConstraint(
                condition=models.Q(chance__gte=1, chance__lte=100),
                name="dungeon_location_item_template_chance_1_100",
            ),
        ),
        migrations.RunPython(backfill_location_item_template_chances, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="dungeonlocation",
            name="rarity_chances",
        ),
    ]
