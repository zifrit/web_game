from django.db import migrations


def backfill_power_cached(apps, schema_editor):
    """Пересчитывает кэш силы у всех существующих героев по текущей формуле."""

    # Бэкофилл использует реальный сервис: формула силы зависит от конфигов,
    # роста класса и экипировки, которые недоступны через historical models.
    from apps.game.models import Character
    from apps.game.services.formulas import GameFormulaService

    for character in Character.objects.select_related("character_class").all():
        GameFormulaService.refresh_power_cache(character)


def noop(apps, schema_editor):
    """Откат не требуется: кэш силы — производное поле."""


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0013_seed_mini_game_card_faces"),
    ]

    operations = [
        migrations.RunPython(backfill_power_cached, noop),
    ]
