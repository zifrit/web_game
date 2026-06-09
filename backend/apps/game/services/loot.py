from __future__ import annotations

import random
from typing import Any

from apps.game.models import Character, DungeonLocation, DungeonLocationItemTemplate, ItemTemplate, UserItem

from .balance import GameBalanceService
from .probabilities import weighted_choice


WEAPON_CLASS_BY_TYPE = {
    "sword": "warrior",
    "dagger": "assassin",
    "staff": "mage",
    "bow": "archer",
}


class LootGenerationService:
    """Сервис генерации предметных наград за успешные подземелья."""

    @classmethod
    def generate_item_reward(cls, character: Character, location: DungeonLocation) -> dict[str, Any] | None:
        """Генерирует черновик выпавшего предмета или None, если дропа нет."""

        if random.uniform(0, 100) > location.item_drop_chance:
            return None

        links = (
            DungeonLocationItemTemplate.objects.filter(location=location, item_template__is_active=True)
            .select_related("item_template")
            .order_by("id")
        )
        weighted_links = [(link, link.chance) for link in links if item_allowed_for_character(link.item_template, character)]
        if not weighted_links:
            return None

        link = weighted_choice(weighted_links)
        return generate_item_instance(link.item_template)


def generate_item_instance(template: ItemTemplate) -> dict[str, Any]:
    """Генерирует черновик уникального предмета из шаблона с прокаткой статов.

    Общая логика для добычи из подземелий и для покупок в магазине, чтобы статы
    генерировались одинаково. Возвращает словарь с полями для UserItem.objects.create.
    """

    rarity = template.rarity_key
    rarity_config = GameBalanceService.rarity_config(rarity)
    item_level = random.randint(rarity_config["min_item_level"], rarity_config["max_item_level"])
    possible_stats = template.possible_stats or {}
    count = min(
        random.randint(rarity_config["min_stats_count"], rarity_config["max_stats_count"]),
        len(possible_stats),
    )
    selected_stats = random.sample(list(possible_stats.keys()), count) if count else []
    stats: dict[str, int] = {}
    for stat_key in selected_stats:
        stat_range = possible_stats[stat_key]
        base_value = random.randint(int(stat_range["min"]), int(stat_range["max"]))
        value = base_value * rarity_config["stat_multiplier"] * (1 + item_level * 0.08)
        stats[stat_key] = max(1, int(round(value)))

    durability_max = random.randint(template.min_durability, template.max_durability)
    item_name = template.name if template.name.lower().startswith(f"{rarity_config['name'].lower()} ") else f"{rarity_config['name']} {template.name}"
    return {
        "template_id": template.id,
        "name": item_name,
        "slot": template.slot,
        "item_type": template.item_type,
        "rarity": rarity,
        "item_level": item_level,
        "stats": stats,
        "durability_current": durability_max,
        "durability_max": durability_max,
    }


def item_allowed_for_character(item: ItemTemplate | UserItem, character: Character) -> bool:
    """Проверяет, подходит ли предмет классу героя по типу оружия и ограничениям."""

    item_type = item.item_type
    required_class = WEAPON_CLASS_BY_TYPE.get(item_type)
    if required_class and required_class != character.character_class.key:
        return False
    allowed_classes = getattr(item, "allowed_classes", None)
    if allowed_classes is None and hasattr(item, "template"):
        allowed_classes = item.template.allowed_classes
    return not allowed_classes or character.character_class_id in allowed_classes
