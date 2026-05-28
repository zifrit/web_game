from __future__ import annotations

from dataclasses import dataclass

from apps.game.models import ItemTemplate
from apps.game.ranks import RANKS, RankConfig


@dataclass(frozen=True)
class EquipmentKind:
    key: str
    slot: str
    item_type: str
    allowed_classes: list[str] | None
    stats: dict[str, dict[str, int]]


EQUIPMENT_KINDS: tuple[EquipmentKind, ...] = (
    EquipmentKind(
        "sword",
        "weapon",
        "sword",
        ["warrior"],
        {"attack": {"min": 4, "max": 8}, "defense": {"min": 1, "max": 3}},
    ),
    EquipmentKind(
        "dagger",
        "weapon",
        "dagger",
        ["assassin"],
        {"attack": {"min": 4, "max": 8}, "critical_chance": {"min": 1, "max": 4}},
    ),
    EquipmentKind(
        "staff",
        "weapon",
        "staff",
        ["mage"],
        {"attack": {"min": 5, "max": 9}, "critical_chance": {"min": 1, "max": 3}},
    ),
    EquipmentKind(
        "bow",
        "weapon",
        "bow",
        ["archer"],
        {"attack": {"min": 4, "max": 8}, "evasion": {"min": 1, "max": 3}},
    ),
    EquipmentKind(
        "ring",
        "ring",
        "ring",
        None,
        {"critical_chance": {"min": 1, "max": 3}, "health": {"min": 4, "max": 10}},
    ),
    EquipmentKind(
        "armor",
        "armor",
        "armor",
        None,
        {"health": {"min": 10, "max": 22}, "defense": {"min": 2, "max": 6}},
    ),
    EquipmentKind(
        "boots",
        "boots",
        "boots",
        None,
        {"evasion": {"min": 1, "max": 4}, "defense": {"min": 1, "max": 3}},
    ),
    EquipmentKind(
        "helmet",
        "helmet",
        "helmet",
        None,
        {"health": {"min": 6, "max": 14}, "defense": {"min": 1, "max": 4}},
    ),
)

ITEM_NOUNS = {
    "sword": {"en": "Sword", "ru": "Меч"},
    "dagger": {"en": "Dagger", "ru": "Кинжал"},
    "staff": {"en": "Staff", "ru": "Посох"},
    "bow": {"en": "Bow", "ru": "Лук"},
    "ring": {"en": "Ring", "ru": "Кольцо"},
    "armor": {"en": "Armor", "ru": "Броня"},
    "boots": {"en": "Boots", "ru": "Ботинки"},
    "helmet": {"en": "Helmet", "ru": "Шлем"},
}

RANK_VARIANTS = {
    "f": (
        {"en": "Recruit", "ru": "новичка"},
        {"en": "Traveler", "ru": "странника"},
        {"en": "Militia", "ru": "ополченца"},
    ),
    "e": (
        {"en": "Scout", "ru": "разведчика"},
        {"en": "Guard", "ru": "стража"},
        {"en": "Ironbound", "ru": "железной клятвы"},
    ),
    "d": (
        {"en": "Veteran", "ru": "ветерана"},
        {"en": "Tempered", "ru": "закалки"},
        {"en": "Runemarked", "ru": "рунного знака"},
    ),
    "c": (
        {"en": "Knight", "ru": "рыцаря"},
        {"en": "Astral", "ru": "астрала"},
        {"en": "Obsidian", "ru": "обсидиана"},
    ),
    "b": (
        {"en": "Royal", "ru": "короны"},
        {"en": "Stormforged", "ru": "грозовой ковки"},
        {"en": "Dragonbone", "ru": "драконьей кости"},
    ),
    "a": (
        {"en": "Mythic", "ru": "мифа"},
        {"en": "Celestial", "ru": "небес"},
        {"en": "Phoenix", "ru": "феникса"},
    ),
    "s": (
        {"en": "Divine", "ru": "божества"},
        {"en": "Eternal", "ru": "вечности"},
        {"en": "Abyssal", "ru": "бездны"},
    ),
}

EX_NAMES = {
    "sword": {"en": "Worldbreaker Sword", "ru": "Меч крушителя миров"},
    "dagger": {"en": "Voidpiercer Dagger", "ru": "Кинжал пронзателя пустоты"},
    "staff": {"en": "Eclipse Staff", "ru": "Посох затмения"},
    "bow": {"en": "Starfall Bow", "ru": "Лук звездопада"},
    "ring": {"en": "Eternity Ring", "ru": "Кольцо вечности"},
    "armor": {"en": "Aegis Armor", "ru": "Броня эгиды"},
    "boots": {"en": "Horizon Boots", "ru": "Ботинки горизонта"},
    "helmet": {"en": "Ascendant Helmet", "ru": "Шлем восхождения"},
}


def _durability_for_rank(rank: RankConfig) -> tuple[int, int]:
    base = 12 + (rank.min_level - 1) // 10 * 4
    return base, base + 12


def seed_ranked_item_templates(*, deactivate_legacy: bool = True) -> list[ItemTemplate]:
    """Create or update every ranked equipment template used by loot generation."""

    rank_keys = [rank.key for rank in RANKS]
    ItemTemplate.objects.filter(rarity_key__in=rank_keys, is_active=True).update(is_active=False)
    if deactivate_legacy:
        ItemTemplate.objects.filter(rarity_key__isnull=True, is_active=True).update(is_active=False)

    templates: list[ItemTemplate] = []
    for rank in RANKS:
        variants = 1 if rank.key == "ex" else 3
        min_durability, max_durability = _durability_for_rank(rank)
        for kind in EQUIPMENT_KINDS:
            for index in range(variants):
                if rank.key == "ex":
                    names = EX_NAMES[kind.key]
                    en_name = f"{names['en']}"
                    ru_name = f"{names['ru']}"
                else:
                    variant = RANK_VARIANTS[rank.key][index]
                    noun = ITEM_NOUNS[kind.key]
                    en_name = f"{variant['en']} {noun['en']}"
                    ru_name = f"{noun['ru']} {variant['ru']}"

                template, _ = ItemTemplate.objects.update_or_create(
                    name=ru_name,
                    defaults={
                        "name_i18n": {"en": en_name, "ru": ru_name},
                        "slot": kind.slot,
                        "item_type": kind.item_type,
                        "rarity_key": rank.key,
                        "allowed_classes": kind.allowed_classes,
                        "possible_stats": kind.stats,
                        "min_durability": min_durability,
                        "max_durability": max_durability,
                        "is_active": True,
                    },
                )
                templates.append(template)
    return templates
