from django.db import migrations, models


START_INTELLECT_BY_CLASS = {
    "warrior": 4,
    "mage": 18,
    "archer": 8,
    "assassin": 10,
}


def _intellect_for_character(character) -> int:
    """Считает интеллект героя от класса и уровня для бэкфилла."""

    character_class = character.character_class
    profile = character_class.growth_profile or {}
    levels_gained = max(character.level - 1, 0)
    intellect = float(character_class.start_intellect or 0)
    intellect += float(profile.get("intellect_per_level", 1)) * levels_gained
    every = int(profile.get("special_bonus_every", 5) or 0)
    if every > 0:
        special_count = character.level // every
        intellect += float((profile.get("special_growth") or {}).get("intellect", 0)) * special_count
    return int(round(intellect))


def forwards(apps, schema_editor):
    CharacterClass = apps.get_model("game", "CharacterClass")
    Character = apps.get_model("game", "Character")
    UserItem = apps.get_model("game", "UserItem")

    for character_class in CharacterClass.objects.all():
        profile = dict(character_class.growth_profile or {})
        if "health_per_level" in profile and "max_hp_per_level" not in profile:
            profile["max_hp_per_level"] = profile.pop("health_per_level")
        profile.setdefault("intellect_per_level", 1)
        character_class.growth_profile = profile
        character_class.start_intellect = START_INTELLECT_BY_CLASS.get(character_class.key, character_class.start_intellect or 0)
        character_class.save(update_fields=["growth_profile", "start_intellect"])

    for character in Character.objects.select_related("character_class").all():
        character.current_hp = character.max_hp
        character.intellect = _intellect_for_character(character)
        character.save(update_fields=["current_hp", "intellect", "updated_at"])

    for item in UserItem.objects.all():
        stats = item.stats or {}
        if isinstance(stats, dict) and "health" in stats and "max_hp" not in stats:
            stats["max_hp"] = stats.pop("health")
            item.stats = stats
            item.save(update_fields=["stats", "updated_at"])


def backwards(apps, schema_editor):
    """Обратный rename ключей предметов и профиля роста (best-effort)."""

    CharacterClass = apps.get_model("game", "CharacterClass")
    UserItem = apps.get_model("game", "UserItem")

    for character_class in CharacterClass.objects.all():
        profile = dict(character_class.growth_profile or {})
        if "max_hp_per_level" in profile and "health_per_level" not in profile:
            profile["health_per_level"] = profile.pop("max_hp_per_level")
        profile.pop("intellect_per_level", None)
        character_class.growth_profile = profile
        character_class.save(update_fields=["growth_profile"])

    for item in UserItem.objects.all():
        stats = item.stats or {}
        if isinstance(stats, dict) and "max_hp" in stats and "health" not in stats:
            stats["health"] = stats.pop("max_hp")
            item.stats = stats
            item.save(update_fields=["stats", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0016_character_intrinsic_stats"),
    ]

    operations = [
        migrations.RenameField(
            model_name="character",
            old_name="health",
            new_name="max_hp",
        ),
        migrations.AlterField(
            model_name="character",
            name="max_hp",
            field=models.PositiveIntegerField(verbose_name="Максимальное HP"),
        ),
        migrations.RenameField(
            model_name="characterclass",
            old_name="start_health",
            new_name="start_max_hp",
        ),
        migrations.AlterField(
            model_name="characterclass",
            name="start_max_hp",
            field=models.PositiveIntegerField(verbose_name="Стартовое максимальное HP"),
        ),
        migrations.AddField(
            model_name="character",
            name="current_hp",
            field=models.PositiveIntegerField(default=0, verbose_name="Текущее HP"),
        ),
        migrations.AddField(
            model_name="character",
            name="intellect",
            field=models.PositiveIntegerField(default=0, verbose_name="Интеллект"),
        ),
        migrations.AddField(
            model_name="characterclass",
            name="start_intellect",
            field=models.PositiveIntegerField(default=0, verbose_name="Стартовый интеллект"),
        ),
        migrations.RunPython(forwards, backwards),
    ]
