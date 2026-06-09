from django.core.management.base import BaseCommand

from apps.game.models import (
    CharacterClass,
    CraftRecipe,
    CraftRecipeIngredient,
    DungeonIngredientDrop,
    DungeonLocation,
    DungeonLocationItemTemplate,
    DungeonMiniGameConfig,
    EquipmentSlotConfig,
    GameConfig,
    IngredientTemplate,
    LocationType,
    MiniGameCardFace,
    PotionTemplate,
    RarityConfig,
    ShopOffer,
    ShopOfferIngredient,
    ShopOfferItem,
    ShopOfferPotion,
)
from apps.billing.models import CurrencyExchangeOffer
from apps.game.services import DEFAULT_CONFIGS
from apps.game.services.mini_game_faces import load_seed_card_faces
from apps.game.services.ranks import MAX_RANK_LEVEL, RANKS
from apps.game.services.seed_data import seed_ranked_item_templates


GROWTH = {
    "max_hp_per_level": 5,
    "intellect_per_level": 1,
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

        # (key, names, max_hp, intellect, attack, defense, crit, evasion, special_growth)
        classes = [
            ("warrior", {"en": "Warrior", "ru": "Воин"}, 120, 4, 10, 8, 5, 3, {"critical_chance": 0.5, "evasion": 0}),
            ("mage", {"en": "Mage", "ru": "Маг"}, 80, 18, 16, 3, 8, 4, {"critical_chance": 0.8, "evasion": 0}),
            ("archer", {"en": "Archer", "ru": "Лучник"}, 95, 8, 12, 5, 12, 8, {"critical_chance": 0.5, "evasion": 0.5}),
            ("assassin", {"en": "Assassin", "ru": "Ассассин"}, 75, 10, 14, 3, 20, 15, {"critical_chance": 1, "evasion": 0.8}),
        ]
        for index, (key, names, max_hp, intellect, attack, defense, crit, evasion, special) in enumerate(classes):
            CharacterClass.objects.update_or_create(
                key=key,
                defaults={
                    "name": names["ru"],
                    "name_i18n": names,
                    "start_max_hp": max_hp,
                    "start_intellect": intellect,
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

        card_face_codes = []
        for face in load_seed_card_faces():
            MiniGameCardFace.objects.update_or_create(
                code=face["code"],
                defaults={
                    "name": face["name"],
                    "svg_markup": face["svg_markup"],
                    "is_active": True,
                    "sort_order": face["sort_order"],
                },
            )
            card_face_codes.append(face["code"])

        # (difficulty, name, pairs, time_limit, reduction_percent, max_reduction_seconds)
        mini_games = [
            ("6", "Memory 6/6", 6, 45, 10, 120),
            ("8", "Memory 8/8", 8, 60, 20, 240),
            ("10", "Memory 10/10", 10, 75, 30, 360),
            ("12", "Memory 12/12", 12, 90, 40, 600),
        ]
        for index, (difficulty, name, pairs_count, time_limit_seconds, reduction_percent, max_reduction_seconds) in enumerate(mini_games):
            DungeonMiniGameConfig.objects.update_or_create(
                difficulty=difficulty,
                defaults={
                    "name": name,
                    "pairs_count": pairs_count,
                    "time_limit_seconds": time_limit_seconds,
                    "reward_duration_reduction_percent": reduction_percent,
                    "max_reduction_seconds": max_reduction_seconds,
                    "card_face_codes": card_face_codes,
                    "is_active": True,
                    "sort_order": index,
                },
            )

        # (..., money_min, money_max, hp_loss_success%, hp_loss_fail%, drop, has_mini_game, mini_diff, template_chances)
        dungeons = [
            ({"en": "Old Forest", "ru": "Старый лес"}, {"en": "A safe starting location.", "ru": "Безопасная стартовая локация."}, 15, 50, 5, 8, 30, 60, 4, 9, 10, True, "6", {"f": 90, "e": 10}),
            ({"en": "Abandoned Trail", "ru": "Заброшенная тропа"}, {"en": "Light risk and quick farming.", "ru": "Легкий риск и быстрый фарм."}, 30, 70, 8, 14, 45, 90, 7, 15, 15, True, "8", {"f": 70, "e": 25, "d": 5}),
            ({"en": "Damp Cave", "ru": "Сырая пещера"}, {"en": "A risky early dungeon.", "ru": "Рискованный early dungeon."}, 300, 100, 18, 35, 120, 220, 12, 25, 25, True, "12", {"f": 45, "e": 35, "d": 15, "c": 4, "b": 1}),
        ]
        for index, data in enumerate(dungeons):
            names, descriptions, duration, power, exp_min, exp_max, money_min, money_max, hp_loss_success, hp_loss_fail, drop, has_mini_game, _mini_game_difficulty, template_chances = data
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
                    "hp_loss_success_percent": hp_loss_success,
                    "hp_loss_fail_percent": hp_loss_fail,
                    "item_drop_chance": drop,
                    "has_mini_game": has_mini_game,
                    "location_type": LocationType.DUNGEON,
                    "daily_limit": 0,
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

        # Ресурсная локация: гарантированный успех, только базовые ингредиенты, дневной лимит.
        DungeonLocation.objects.update_or_create(
            name="Лес трав",
            defaults={
                "description": "Спокойный сбор базовых ингредиентов.",
                "name_i18n": {"en": "Herb Forest", "ru": "Лес трав"},
                "description_i18n": {
                    "en": "A calm spot to gather basic ingredients.",
                    "ru": "Спокойный сбор базовых ингредиентов.",
                },
                "duration_seconds": 30,
                "required_power": 0,
                "experience_min": 0,
                "experience_max": 0,
                "money_min_copper": 0,
                "money_max_copper": 0,
                "hp_loss_success_percent": 0,
                "hp_loss_fail_percent": 0,
                "item_drop_chance": 0,
                "has_mini_game": False,
                "location_type": LocationType.RESOURCE,
                "daily_limit": 3,
                "is_active": True,
                "sort_order": 100,
            },
        )

        # (code, names, descriptions, heal_percent)
        potions = [
            (
                "small_healing_potion",
                {"en": "Small healing potion", "ru": "Малое зелье лечения"},
                {"en": "Restores a small amount of HP.", "ru": "Восстанавливает немного HP."},
                20,
            ),
            (
                "medium_healing_potion",
                {"en": "Medium healing potion", "ru": "Среднее зелье лечения"},
                {"en": "Restores a moderate amount of HP.", "ru": "Восстанавливает умеренное количество HP."},
                40,
            ),
            (
                "large_healing_potion",
                {"en": "Large healing potion", "ru": "Большое зелье лечения"},
                {"en": "Restores a large amount of HP.", "ru": "Восстанавливает большое количество HP."},
                70,
            ),
        ]
        potion_by_code = {}
        for index, (code, names, descriptions, heal_percent) in enumerate(potions):
            potion, _ = PotionTemplate.objects.update_or_create(
                code=code,
                defaults={
                    "name": names["ru"],
                    "name_i18n": names,
                    "description": descriptions["ru"],
                    "description_i18n": descriptions,
                    "heal_percent": heal_percent,
                    "is_active": True,
                    "sort_order": index,
                },
            )
            potion_by_code[code] = potion

        # (code, names, descriptions, category)
        ingredients = [
            (
                "forest_herb",
                {"en": "Forest herb", "ru": "Лесная трава"},
                {"en": "A common herb gathered in forests.", "ru": "Обычная трава, собираемая в лесах."},
                IngredientTemplate.Category.BASIC,
            ),
            (
                "clean_water",
                {"en": "Clean water", "ru": "Чистая вода"},
                {"en": "Fresh water for simple recipes.", "ru": "Свежая вода для простых рецептов."},
                IngredientTemplate.Category.BASIC,
            ),
            (
                "bitter_root",
                {"en": "Bitter root", "ru": "Горький корень"},
                {"en": "A bitter root with alchemical uses.", "ru": "Горький корень для алхимии."},
                IngredientTemplate.Category.BASIC,
            ),
            (
                "cave_moss",
                {"en": "Cave moss", "ru": "Пещерный мох"},
                {"en": "Moss that grows in damp caves.", "ru": "Мох, растущий в сырых пещерах."},
                IngredientTemplate.Category.REGIONAL,
            ),
            (
                "crystal_dust",
                {"en": "Crystal dust", "ru": "Кристальная пыль"},
                {"en": "Rare shimmering crystal dust.", "ru": "Редкая мерцающая кристальная пыль."},
                IngredientTemplate.Category.RARE,
            ),
        ]
        ingredient_by_code = {}
        for index, (code, names, descriptions, category) in enumerate(ingredients):
            ingredient, _ = IngredientTemplate.objects.update_or_create(
                code=code,
                defaults={
                    "name": names["ru"],
                    "name_i18n": names,
                    "description": descriptions["ru"],
                    "description_i18n": descriptions,
                    "category": category,
                    "is_active": True,
                    "sort_order": index,
                },
            )
            ingredient_by_code[code] = ingredient

        # location name -> {ingredient code: (chance_percent, min_quantity, max_quantity)}
        ingredient_drops = {
            "Старый лес": {
                "forest_herb": (75, 1, 3),
                "clean_water": (45, 1, 1),
            },
            "Заброшенная тропа": {
                "forest_herb": (60, 1, 2),
                "bitter_root": (35, 1, 1),
                "cave_moss": (15, 1, 1),
            },
            "Сырая пещера": {
                "cave_moss": (50, 1, 2),
                "bitter_root": (30, 1, 1),
                "crystal_dust": (8, 1, 1),
            },
            "Лес трав": {
                "forest_herb": (100, 1, 5),
                "clean_water": (50, 1, 2),
            },
        }
        for location_name, drops in ingredient_drops.items():
            location = DungeonLocation.objects.get(name=location_name)
            for code, (chance_percent, min_quantity, max_quantity) in drops.items():
                DungeonIngredientDrop.objects.update_or_create(
                    location=location,
                    ingredient=ingredient_by_code[code],
                    defaults={
                        "chance_percent": chance_percent,
                        "min_quantity": min_quantity,
                        "max_quantity": max_quantity,
                    },
                )

        # (code, difficulty, potion_code, required_hero_level, {ingredient_code: quantity per potion})
        recipes = [
            (
                "small_healing_recipe",
                CraftRecipe.Difficulty.SMALL,
                "small_healing_potion",
                1,
                {"forest_herb": 3, "clean_water": 1, "bitter_root": 1},
            ),
            (
                "medium_healing_recipe",
                CraftRecipe.Difficulty.MEDIUM,
                "medium_healing_potion",
                1,
                {"forest_herb": 4, "clean_water": 2, "bitter_root": 2, "cave_moss": 1},
            ),
            (
                "large_healing_recipe",
                CraftRecipe.Difficulty.LARGE,
                "large_healing_potion",
                5,
                {"forest_herb": 5, "clean_water": 2, "bitter_root": 2, "cave_moss": 2, "crystal_dust": 1},
            ),
        ]
        for index, (code, difficulty, potion_code, required_level, slots) in enumerate(recipes):
            recipe, _ = CraftRecipe.objects.update_or_create(
                code=code,
                defaults={
                    "difficulty": difficulty,
                    "potion": potion_by_code[potion_code],
                    "required_hero_level": required_level,
                    "is_active": True,
                    "sort_order": index,
                },
            )
            for ingredient_code, quantity in slots.items():
                CraftRecipeIngredient.objects.update_or_create(
                    recipe=recipe,
                    ingredient=ingredient_by_code[ingredient_code],
                    defaults={"quantity": quantity},
                )

        self._seed_shop(ingredient_by_code, potion_by_code, templates_by_rank)
        self._seed_exchange_offers()

        self.stdout.write(self.style.SUCCESS("Seeded MVP game data."))

    def _seed_shop(self, ingredient_by_code, potion_by_code, templates_by_rank):
        """Создаёт демонстрационные предложения магазина (идемпотентно по name)."""

        # Одиночный ингредиент за монеты.
        herb = ingredient_by_code.get("forest_herb")
        if herb is not None:
            offer, _ = ShopOffer.objects.update_or_create(
                name_i18n={"en": "Forest Herb", "ru": "Лесная трава"},
                defaults={
                    "reward_kind": ShopOffer.RewardKind.INGREDIENT,
                    "delivery_mode": ShopOffer.DeliveryMode.SINGLE,
                    "description_i18n": {"en": "A bundle of fresh forest herbs.", "ru": "Связка свежих лесных трав."},
                    "quantity": 1,
                    "price_money_copper": 500,
                    "is_active": True,
                    "sort_order": 1,
                },
            )
            offer.ingredient_entries.all().delete()
            ShopOfferIngredient.objects.create(offer=offer, ingredient_template=herb, chance=1)

        # Сундук ингредиентов за монеты или премиум.
        chest_ingredients = [ingredient_by_code.get(code) for code in ("forest_herb", "bitter_root", "cave_moss")]
        chest_ingredients = [item for item in chest_ingredients if item is not None]
        if chest_ingredients:
            offer, _ = ShopOffer.objects.update_or_create(
                name_i18n={"en": "Herbalist's Chest", "ru": "Сундук травника"},
                defaults={
                    "reward_kind": ShopOffer.RewardKind.INGREDIENT,
                    "delivery_mode": ShopOffer.DeliveryMode.CHEST,
                    "description_i18n": {"en": "5 random herbs.", "ru": "5 случайных трав."},
                    "quantity": 5,
                    "price_money_copper": 2000,
                    "price_premium_currency": 3,
                    "is_active": True,
                    "sort_order": 2,
                },
            )
            offer.ingredient_entries.all().delete()
            chances = [70, 25, 5]
            for ingredient, chance in zip(chest_ingredients, chances):
                ShopOfferIngredient.objects.create(offer=offer, ingredient_template=ingredient, chance=chance)

        # Одиночное зелье за монеты.
        potion = potion_by_code.get("small_healing_potion")
        if potion is not None:
            offer, _ = ShopOffer.objects.update_or_create(
                name_i18n={"en": "Small Healing Potion", "ru": "Малое зелье лечения"},
                defaults={
                    "reward_kind": ShopOffer.RewardKind.POTION,
                    "delivery_mode": ShopOffer.DeliveryMode.SINGLE,
                    "description_i18n": {"en": "Restores a bit of HP.", "ru": "Восстанавливает немного HP."},
                    "quantity": 1,
                    "price_money_copper": 800,
                    "is_active": True,
                    "sort_order": 3,
                },
            )
            offer.potion_entries.all().delete()
            ShopOfferPotion.objects.create(offer=offer, potion_template=potion, chance=1)

        # Сундук предметов ранга C за премиум или монеты.
        c_items = templates_by_rank.get("c") or templates_by_rank.get("C") or []
        if c_items:
            offer, _ = ShopOffer.objects.update_or_create(
                name_i18n={"en": "Rank C Gear Chest", "ru": "Сундук снаряжения ранга C"},
                defaults={
                    "reward_kind": ShopOffer.RewardKind.ITEM,
                    "delivery_mode": ShopOffer.DeliveryMode.CHEST,
                    "description_i18n": {"en": "Contains 3 random items.", "ru": "Содержит 3 случайных предмета."},
                    "quantity": 3,
                    "price_money_copper": 5000,
                    "price_premium_currency": 5,
                    "is_active": True,
                    "sort_order": 4,
                },
            )
            offer.item_entries.all().delete()
            for index, template in enumerate(c_items[:4]):
                ShopOfferItem.objects.create(offer=offer, item_template=template, chance=max(50 - index * 10, 10))

    def _seed_exchange_offers(self):
        """Создаёт демонстрационные предложения обмена премиума на монеты."""

        offers = [
            (10, 10_000, 1),
            (50, 60_000, 2),
            (100, 130_000, 3),
        ]
        for premium_cost, money_copper_reward, sort_order in offers:
            CurrencyExchangeOffer.objects.update_or_create(
                premium_cost=premium_cost,
                defaults={
                    "money_copper_reward": money_copper_reward,
                    "is_active": True,
                    "sort_order": sort_order,
                },
            )
