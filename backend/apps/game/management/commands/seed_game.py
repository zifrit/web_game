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
            ("warrior", "Воин", 120, 10, 8, 5, 3, {"critical_chance": 0.5, "evasion": 0}),
            ("mage", "Маг", 80, 16, 3, 8, 4, {"critical_chance": 0.8, "evasion": 0}),
            ("archer", "Лучник", 95, 12, 5, 12, 8, {"critical_chance": 0.5, "evasion": 0.5}),
            ("assassin", "Ассассин", 75, 14, 3, 20, 15, {"critical_chance": 1, "evasion": 0.8}),
        ]
        for index, (key, name, hp, attack, defense, crit, evasion, special) in enumerate(classes):
            CharacterClass.objects.update_or_create(
                key=key,
                defaults={
                    "name": name,
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
            ("common", "Обычный", 1.0, 1, 3, 1, 1),
            ("uncommon", "Необычный", 1.25, 2, 5, 1, 2),
            ("rare", "Редкий", 1.6, 4, 8, 2, 3),
            ("epic", "Эпический", 2.2, 7, 10, 3, 3),
        ]
        for index, rarity in enumerate(rarities):
            key, name, mult, min_level, max_level, min_stats, max_stats = rarity
            RarityConfig.objects.update_or_create(
                key=key,
                defaults={
                    "name": name,
                    "stat_multiplier": mult,
                    "min_item_level": min_level,
                    "max_item_level": max_level,
                    "min_stats_count": min_stats,
                    "max_stats_count": max_stats,
                    "sort_order": index,
                    "is_active": True,
                },
            )

        for index, (key, name) in enumerate(
            [("weapon", "Оружие"), ("helmet", "Шлем"), ("armor", "Броня"), ("boots", "Ботинки"), ("ring", "Кольцо")]
        ):
            EquipmentSlotConfig.objects.update_or_create(key=key, defaults={"name": name, "sort_order": index, "is_active": True})

        templates = [
            ("Ржавый меч", "weapon", "sword", ["warrior"], {"attack": {"min": 3, "max": 6}, "defense": {"min": 1, "max": 2}}),
            ("Треснувший посох", "weapon", "staff", ["mage"], {"attack": {"min": 4, "max": 8}, "critical_chance": {"min": 1, "max": 3}}),
            ("Короткий лук", "weapon", "bow", ["archer"], {"attack": {"min": 3, "max": 7}, "evasion": {"min": 1, "max": 2}}),
            ("Старый кинжал", "weapon", "dagger", ["assassin"], {"attack": {"min": 3, "max": 7}, "critical_chance": {"min": 1, "max": 4}}),
            ("Потертый шлем", "helmet", "helmet", None, {"health": {"min": 5, "max": 12}, "defense": {"min": 1, "max": 3}}),
            ("Кожаная броня", "armor", "armor", None, {"health": {"min": 8, "max": 18}, "defense": {"min": 2, "max": 5}}),
            ("Дорожные ботинки", "boots", "boots", None, {"evasion": {"min": 1, "max": 3}, "defense": {"min": 1, "max": 2}}),
            ("Медное кольцо", "ring", "ring", None, {"critical_chance": {"min": 1, "max": 3}, "health": {"min": 3, "max": 8}}),
        ]
        item_templates = []
        for name, slot, item_type, allowed, stats in templates:
            template, _ = ItemTemplate.objects.update_or_create(
                name=name,
                defaults={
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
            ("Старый лес", "Безопасная стартовая локация.", 15, 50, 5, 8, 30, 60, 10, {"common": 90, "uncommon": 10, "rare": 0, "epic": 0}),
            ("Заброшенная тропа", "Легкий риск и быстрый фарм.", 30, 70, 8, 14, 45, 90, 15, {"common": 70, "uncommon": 28, "rare": 2, "epic": 0}),
            ("Сырая пещера", "Рискованный early dungeon.", 300, 100, 18, 35, 120, 220, 25, {"common": 45, "uncommon": 45, "rare": 9, "epic": 1}),
        ]
        for index, data in enumerate(dungeons):
            name, description, duration, power, exp_min, exp_max, money_min, money_max, drop, rarity = data
            dungeon, _ = DungeonLocation.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
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
