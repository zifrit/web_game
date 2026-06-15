from __future__ import annotations

from django.db import transaction

from config.celery import app

from .utils import update_task_log


SMALL_POTION_CODE = "small_healing_potion"
DAILY_POTION_GIFT = 2


@app.task(name="apps.game.tasks.daily_gift", bind=True)
def daily_gift(self, log_id: int | None = None) -> dict:
    """Начисляет каждому герою 2 малых зелья и восстанавливает HP до максимума."""

    potion_count, heal_count = _run()
    result = f"Зелий выдано: {potion_count * DAILY_POTION_GIFT}, героев вылечено: {heal_count}"
    update_task_log(log_id, status="success", result=result)
    return {"potions_given": potion_count * DAILY_POTION_GIFT, "heroes_healed": heal_count}


def _run() -> tuple[int, int]:
    from apps.game.models import Character, HeroPotionStorage, PotionTemplate

    try:
        potion = PotionTemplate.objects.get(code=SMALL_POTION_CODE)
    except PotionTemplate.DoesNotExist:
        return 0, 0

    characters = list(
        Character.objects.filter(character_class__isnull=False)
        .only("id", "max_hp", "current_hp")
    )
    if not characters:
        return 0, 0

    char_ids = [c.id for c in characters]

    with transaction.atomic():
        existing = {
            s.character_id: s
            for s in HeroPotionStorage.objects.select_for_update()
            .filter(character_id__in=char_ids, potion=potion)
        }
        to_create = []
        to_update = []
        for c in characters:
            if c.id in existing:
                entry = existing[c.id]
                entry.count += DAILY_POTION_GIFT
                to_update.append(entry)
            else:
                to_create.append(HeroPotionStorage(
                    character_id=c.id,
                    potion=potion,
                    count=DAILY_POTION_GIFT,
                ))
        if to_create:
            HeroPotionStorage.objects.bulk_create(to_create)
        if to_update:
            HeroPotionStorage.objects.bulk_update(to_update, ["count", "updated_at"])

    healed = 0
    with transaction.atomic():
        to_heal = [c for c in characters if c.current_hp < c.max_hp]
        for c in to_heal:
            c.current_hp = c.max_hp
        if to_heal:
            Character.objects.bulk_update(to_heal, ["current_hp", "updated_at"])
            healed = len(to_heal)

    return len(characters), healed
