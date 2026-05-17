from django.core.management.base import BaseCommand

from apps.game.models import (
    CharacterClass,
    DungeonLocation,
    DungeonLocationItemTemplate,
    EquipmentSlotConfig,
    GameConfig,
    ItemTemplate,
    RarityConfig,
)
from apps.game.services import DEFAULT_CONFIGS


GROWTH = {
    "health_per_level": 5,
    "attack_per_level": 1,
    "defense_per_level": 1,
    "special_bonus_every": 5,
}


class Command(BaseCommand):
    help = "Seed MVP balance data for Browser Async RPG."

    def handle(self, *args, **options):
        for key, value in DEFAULT_CONFIGS.items():
            GameConfig.objects.update_or_create(
                key=key,
                defaults={"value": value, "description": "MVP central balance config", "is_active": True},
            )

        classes = [
            ("warrior", {"en": "Warrior", "ru": "Воин"}, 120, 10, 8, 5, 3, {"critical_chance": 0.5, "evasion": 0}),
            ("mage", {"en": "Mage", "ru": "Маг"}, 80, 16, 3, 8, 4, {"critical_chance": 0.8, "evasion": 0}),
            ("archer", {"en": "Archer", "ru": "Лучник"}, 95, 12, 5, 12, 8, {"critical_chance": 0.5, "evasion": 0.5}),
            ("assassin", {"en": "Assassin", "ru": "Ассассин"}, 75, 14, 3, 20, 15, {"critical_chance": 1, "evasion": 0.8}),
        ]
        for index, (key, names, hp, attack, defense, crit, evasion, special) in enumerate(classes):
            CharacterClass.objects.update_or_create(
                key=key,
                defaults={
                    "name": names["ru"],
                    "name_i18n": names,
                    "start_health": hp,
                    "start_attack": attack,
                    "start_defense": defense,
                    "start_critical_chance": crit,
                    "start_evasion": evasion,
                    "growth_profile": {**GROWTH, "special_growth": special},
                    "is_active": True,
                    "sort_order": index,
                },
            )

        rarities = [
            ("common", {"en": "Common", "ru": "Обычный"}, 1.0, 1, 3, 1, 1),
            ("uncommon", {"en": "Uncommon", "ru": "Необычный"}, 1.25, 2, 5, 1, 2),
            ("rare", {"en": "Rare", "ru": "Редкий"}, 1.6, 4, 8, 2, 3),
            ("epic", {"en": "Epic", "ru": "Эпический"}, 2.2, 7, 10, 3, 3),
        ]
        for index, rarity in enumerate(rarities):
            key, names, mult, min_level, max_level, min_stats, max_stats = rarity
            RarityConfig.objects.update_or_create(
                key=key,
                defaults={
                    "name": names["ru"],
                    "name_i18n": names,
                    "stat_multiplier": mult,
                    "min_item_level": min_level,
                    "max_item_level": max_level,
                    "min_stats_count": min_stats,
                    "max_stats_count": max_stats,
                    "sort_order": index,
                    "is_active": True,
                },
            )

        for index, (key, names) in enumerate(
            [
                ("weapon", {"en": "Weapon", "ru": "Оружие"}),
                ("helmet", {"en": "Helmet", "ru": "Шлем"}),
                ("armor", {"en": "Armor", "ru": "Броня"}),
                ("boots", {"en": "Boots", "ru": "Ботинки"}),
                ("ring", {"en": "Ring", "ru": "Кольцо"}),
            ]
        ):
            EquipmentSlotConfig.objects.update_or_create(
                key=key,
                defaults={"name": names["ru"], "name_i18n": names, "sort_order": index, "is_active": True},
            )

        templates = [
            ({"en": "Rusty Sword", "ru": "Ржавый меч"}, "weapon", "sword", ["warrior"], {"attack": {"min": 3, "max": 6}, "defense": {"min": 1, "max": 2}}),
            ({"en": "Cracked Staff", "ru": "Треснувший посох"}, "weapon", "staff", ["mage"], {"attack": {"min": 4, "max": 8}, "critical_chance": {"min": 1, "max": 3}}),
            ({"en": "Short Bow", "ru": "Короткий лук"}, "weapon", "bow", ["archer"], {"attack": {"min": 3, "max": 7}, "evasion": {"min": 1, "max": 2}}),
            ({"en": "Old Dagger", "ru": "Старый кинжал"}, "weapon", "dagger", ["assassin"], {"attack": {"min": 3, "max": 7}, "critical_chance": {"min": 1, "max": 4}}),
            ({"en": "Worn Helmet", "ru": "Потертый шлем"}, "helmet", "helmet", None, {"health": {"min": 5, "max": 12}, "defense": {"min": 1, "max": 3}}),
            ({"en": "Leather Armor", "ru": "Кожаная броня"}, "armor", "armor", None, {"health": {"min": 8, "max": 18}, "defense": {"min": 2, "max": 5}}),
            ({"en": "Travel Boots", "ru": "Дорожные ботинки"}, "boots", "boots", None, {"evasion": {"min": 1, "max": 3}, "defense": {"min": 1, "max": 2}}),
            ({"en": "Copper Ring", "ru": "Медное кольцо"}, "ring", "ring", None, {"critical_chance": {"min": 1, "max": 3}, "health": {"min": 3, "max": 8}}),
        ]
        item_templates = []
        for names, slot, item_type, allowed, stats in templates:
            template, _ = ItemTemplate.objects.update_or_create(
                name=names["ru"],
                defaults={
                    "name_i18n": names,
                    "slot": slot,
                    "item_type": item_type,
                    "allowed_classes": allowed,
                    "possible_stats": stats,
                    "min_durability": 12,
                    "max_durability": 24,
                    "is_active": True,
                },
            )
            item_templates.append(template)

        dungeons = [
            ({"en": "Old Forest", "ru": "Старый лес"}, {"en": "A safe starting location.", "ru": "Безопасная стартовая локация."}, 15, 50, 5, 8, 30, 60, 10, {"common": 90, "uncommon": 10, "rare": 0, "epic": 0}),
            ({"en": "Abandoned Trail", "ru": "Заброшенная тропа"}, {"en": "Light risk and quick farming.", "ru": "Легкий риск и быстрый фарм."}, 30, 70, 8, 14, 45, 90, 15, {"common": 70, "uncommon": 28, "rare": 2, "epic": 0}),
            ({"en": "Damp Cave", "ru": "Сырая пещера"}, {"en": "A risky early dungeon.", "ru": "Рискованный early dungeon."}, 300, 100, 18, 35, 120, 220, 25, {"common": 45, "uncommon": 45, "rare": 9, "epic": 1}),
        ]
        for index, data in enumerate(dungeons):
            names, descriptions, duration, power, exp_min, exp_max, money_min, money_max, drop, rarity = data
            dungeon, _ = DungeonLocation.objects.update_or_create(
                name=names["ru"],
                defaults={
                    "description": descriptions["ru"],
                    "name_i18n": names,
                    "description_i18n": descriptions,
                    "duration_seconds": duration,
                    "required_power": power,
                    "experience_min": exp_min,
                    "experience_max": exp_max,
                    "money_min_copper": money_min,
                    "money_max_copper": money_max,
                    "item_drop_chance": drop,
                    "rarity_chances": rarity,
                    "is_active": True,
                    "sort_order": index,
                },
            )
            for template in item_templates:
                DungeonLocationItemTemplate.objects.get_or_create(location=dungeon, item_template=template)

        self.stdout.write(self.style.SUCCESS("Seeded MVP game data."))
