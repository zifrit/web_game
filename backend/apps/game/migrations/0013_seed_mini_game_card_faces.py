from pathlib import Path

from django.db import migrations

FACES_DIR = Path(__file__).resolve().parent.parent / "data" / "memory_faces"

# Дефолтные проценты/потолки ускорения по сложности для уже существующих конфигов.
DEFAULTS_BY_DIFFICULTY = {
    "6": (10, 120),
    "8": (20, 240),
    "10": (30, 360),
    "12": (40, 600),
}


def seed_faces(apps, schema_editor):
    """Создаёт стартовые лица карт и привязывает их коды к конфигам мини-игр."""

    MiniGameCardFace = apps.get_model("game", "MiniGameCardFace")
    DungeonMiniGameConfig = apps.get_model("game", "DungeonMiniGameConfig")

    codes = []
    for index, path in enumerate(sorted(FACES_DIR.glob("*.svg"))):
        code = path.stem
        MiniGameCardFace.objects.update_or_create(
            code=code,
            defaults={
                "name": code.capitalize(),
                "svg_markup": path.read_text(encoding="utf-8").strip(),
                "is_active": True,
                "sort_order": index,
            },
        )
        codes.append(code)

    for config in DungeonMiniGameConfig.objects.all():
        percent, max_seconds = DEFAULTS_BY_DIFFICULTY.get(config.difficulty, (10, 600))
        config.card_face_codes = codes
        config.reward_duration_reduction_percent = percent
        config.max_reduction_seconds = max_seconds
        config.save(update_fields=["card_face_codes", "reward_duration_reduction_percent", "max_reduction_seconds"])


def unseed_faces(apps, schema_editor):
    """Откат: чистит лица карт и обнуляет привязанные коды у конфигов."""

    MiniGameCardFace = apps.get_model("game", "MiniGameCardFace")
    DungeonMiniGameConfig = apps.get_model("game", "DungeonMiniGameConfig")
    DungeonMiniGameConfig.objects.all().update(card_face_codes=list())
    MiniGameCardFace.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0012_minigamecardface_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_faces, unseed_faces),
    ]
