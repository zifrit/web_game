from django.db import migrations, models


def _level_growth_stats(character):
    profile = character.character_class.growth_profile or {}
    levels_gained = max(character.level - 1, 0)
    stats = {
        "health": float(profile.get("health_per_level", 5)) * levels_gained,
        "attack": float(profile.get("attack_per_level", 1)) * levels_gained,
        "defense": float(profile.get("defense_per_level", 1)) * levels_gained,
        "critical_chance": 0.0,
        "evasion": 0.0,
    }
    every = int(profile.get("special_bonus_every", 5) or 0)
    if every > 0:
        special_count = character.level // every
        for key, value in (profile.get("special_growth") or {}).items():
            if key in stats:
                stats[key] += float(value) * special_count
    return stats


def backfill_intrinsic_stats(apps, schema_editor):
    Character = apps.get_model("game", "Character")

    for character in Character.objects.select_related("character_class").all():
        character_class = character.character_class
        stats = {
            "health": float(character_class.start_health),
            "attack": float(character_class.start_attack),
            "defense": float(character_class.start_defense),
            "critical_chance": float(character_class.start_critical_chance),
            "evasion": float(character_class.start_evasion),
        }
        for key, value in _level_growth_stats(character).items():
            stats[key] += value

        character.health = int(round(stats["health"]))
        character.attack = int(round(stats["attack"]))
        character.defense = int(round(stats["defense"]))
        character.critical_chance = stats["critical_chance"]
        character.evasion = stats["evasion"]
        character.save(
            update_fields=[
                "health",
                "attack",
                "defense",
                "critical_chance",
                "evasion",
                "updated_at",
            ]
        )


def noop(apps, schema_editor):
    """Reverse rename keeps the persisted stat values as-is."""


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0015_gendered_character_class_media"),
    ]

    operations = [
        migrations.RenameField(
            model_name="character",
            old_name="base_health",
            new_name="health",
        ),
        migrations.AlterField(
            model_name="character",
            name="health",
            field=models.PositiveIntegerField(verbose_name="Здоровье"),
        ),
        migrations.RenameField(
            model_name="character",
            old_name="base_attack",
            new_name="attack",
        ),
        migrations.AlterField(
            model_name="character",
            name="attack",
            field=models.PositiveIntegerField(verbose_name="Атака"),
        ),
        migrations.RenameField(
            model_name="character",
            old_name="base_defense",
            new_name="defense",
        ),
        migrations.AlterField(
            model_name="character",
            name="defense",
            field=models.PositiveIntegerField(verbose_name="Защита"),
        ),
        migrations.RenameField(
            model_name="character",
            old_name="base_critical_chance",
            new_name="critical_chance",
        ),
        migrations.AlterField(
            model_name="character",
            name="critical_chance",
            field=models.FloatField(verbose_name="Шанс критического удара"),
        ),
        migrations.RenameField(
            model_name="character",
            old_name="base_evasion",
            new_name="evasion",
        ),
        migrations.AlterField(
            model_name="character",
            name="evasion",
            field=models.FloatField(verbose_name="Уклонение"),
        ),
        migrations.RunPython(backfill_intrinsic_stats, noop),
    ]
