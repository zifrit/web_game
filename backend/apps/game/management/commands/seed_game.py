from django.core.management.base import BaseCommand

from apps.game.models import (
    CharacterClass,
    DungeonLocation,
    DungeonLocationItemTemplate,
    EquipmentSlotConfig,
    GameConfig,
    RarityConfig,
)
from apps.game.ranks import MAX_RANK_LEVEL, RANKS
from apps.game.seed_data import seed_ranked_item_templates
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
        configs = {**DEFAULT_CONFIGS, "experience_curve_config": {**DEFAULT_CONFIGS["experience_curve_config"], "max_level": MAX_RANK_LEVEL}}
        for key, value in configs.items():
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

        rank_keys = [rank.key for rank in RANKS]
        RarityConfig.objects.exclude(key__in=rank_keys).update(is_active=False)
        for index, rank in enumerate(RANKS):
            RarityConfig.objects.update_or_create(
                key=rank.key,
                defaults={
                    "name": rank.label,
                    "name_i18n": {"en": rank.label, "ru": rank.label},
                    "stat_multiplier": rank.stat_multiplier,
                    "economy_multiplier": rank.economy_multiplier,
                    "min_item_level": rank.min_level,
                    "max_item_level": rank.max_level,
                    "min_stats_count": rank.min_stats_count,
                    "max_stats_count": rank.max_stats_count,
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

        item_templates = seed_ranked_item_templates()
        templates_by_rank = {}
        for template in item_templates:
            templates_by_rank.setdefault(template.rarity_key, []).append(template)

        dungeons = [
            ({"en": "Old Forest", "ru": "Старый лес"}, {"en": "A safe starting location.", "ru": "Безопасная стартовая локация."}, 15, 50, 5, 8, 30, 60, 10, {"f": 90, "e": 10}),
            ({"en": "Abandoned Trail", "ru": "Заброшенная тропа"}, {"en": "Light risk and quick farming.", "ru": "Легкий риск и быстрый фарм."}, 30, 70, 8, 14, 45, 90, 15, {"f": 70, "e": 25, "d": 5}),
            ({"en": "Damp Cave", "ru": "Сырая пещера"}, {"en": "A risky early dungeon.", "ru": "Рискованный early dungeon."}, 300, 100, 18, 35, 120, 220, 25, {"f": 45, "e": 35, "d": 15, "c": 4, "b": 1}),
        ]
        for index, data in enumerate(dungeons):
            names, descriptions, duration, power, exp_min, exp_max, money_min, money_max, drop, template_chances = data
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
                    "is_active": True,
                    "sort_order": index,
                },
            )
            active_template_ids = []
            for rarity_key, chance in template_chances.items():
                for template in templates_by_rank.get(rarity_key, []):
                    DungeonLocationItemTemplate.objects.update_or_create(
                        location=dungeon,
                        item_template=template,
                        defaults={"chance": chance},
                    )
                    active_template_ids.append(template.id)
            DungeonLocationItemTemplate.objects.filter(location=dungeon).exclude(item_template_id__in=active_template_ids).delete()

        self.stdout.write(self.style.SUCCESS("Seeded MVP game data."))
