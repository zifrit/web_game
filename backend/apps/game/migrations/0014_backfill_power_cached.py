from django.db import migrations


def backfill_power_cached(apps, schema_editor):
    """Пересчитывает кэш силы у всех существующих героев по текущей формуле."""

    from django.utils import timezone

    Character = apps.get_model("game", "Character")
    weights = {"attack": 2, "defense": 1.7, "health": 0.25, "critical_chance": 1, "evasion": 1}

    for character in Character.objects.select_related("character_class").prefetch_related("equipped_items").all():
        stats = {
            "health": float(character.base_health),
            "attack": float(character.base_attack),
            "defense": float(character.base_defense),
            "critical_chance": float(character.base_critical_chance),
            "evasion": float(character.base_evasion),
        }
        profile = character.character_class.growth_profile or {}
        levels_gained = max(character.level - 1, 0)
        stats["health"] += float(profile.get("health_per_level", 5)) * levels_gained
        stats["attack"] += float(profile.get("attack_per_level", 1)) * levels_gained
        stats["defense"] += float(profile.get("defense_per_level", 1)) * levels_gained
        every = int(profile.get("special_bonus_every", 5) or 0)
        if every > 0:
            special_count = character.level // every
            for key, value in (profile.get("special_growth") or {}).items():
                if key in stats:
                    stats[key] += float(value) * special_count

        for item in character.equipped_items.all():
            if item.durability_current <= 0:
                continue
            for key, value in (item.stats or {}).items():
                if key in stats:
                    stats[key] += float(value)

        stats["critical_chance"] = min(stats["critical_chance"], 60.0)
        stats["evasion"] = min(stats["evasion"], 50.0)
        character.power_cached = round(sum(stats[key] * weights[key] for key in weights), 2)
        character.power_updated_at = timezone.now()
        character.save(update_fields=["power_cached", "power_updated_at", "updated_at"])


def noop(apps, schema_editor):
    """Откат не требуется: кэш силы — производное поле."""


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0013_seed_mini_game_card_faces"),
    ]

    operations = [
        migrations.RunPython(backfill_power_cached, noop),
    ]
