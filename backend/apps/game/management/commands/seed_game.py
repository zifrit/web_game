from django.core.management.base import BaseCommand

from apps.game.models import (
    CharacterClass,
    CraftRecipe,
    CraftRecipeIngredient,
    DungeonIngredientDrop,
    DungeonLimitCategory,
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
        # Стартовые статы подобраны так, чтобы мощь каждого класса = 71
        # (power = int*1.5 + atk*2.0 + def*1.7 + crit*1.5 + eva*1.5; max_hp в мощь не входит).
        classes = [
            ("warrior", {"en": "Warrior", "ru": "Воин"}, 130, 5, 13, 15, 5, 3, {"critical_chance": 0.5, "evasion": 0}),
            ("mage", {"en": "Mage", "ru": "Маг"}, 80, 20, 11, 5, 5, 2, {"critical_chance": 0.8, "evasion": 0}),
            ("archer", {"en": "Archer", "ru": "Лучник"}, 100, 6, 12, 10, 8, 6, {"critical_chance": 0.5, "evasion": 0.5}),
            ("assassin", {"en": "Assassin", "ru": "Ассассин"}, 78, 4, 14, 5, 12, 7, {"critical_chance": 1, "evasion": 0.8}),
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
        templates_by_rank_slot = {}
        for template in item_templates:
            templates_by_rank.setdefault(template.rarity_key, []).append(template)
            templates_by_rank_slot.setdefault((template.rarity_key, template.slot), []).append(template)
        dungeon_limit_category, _ = DungeonLimitCategory.objects.update_or_create(
            code="dungeons",
            defaults={
                "name": "Данжи",
                "name_i18n": {"en": "Dungeons", "ru": "Данжи"},
                "limit_count": 0,
                "limit_period_count": 1,
                "limit_period_unit": DungeonLimitCategory.PeriodUnit.DAY,
                "sort_order": 0,
            },
        )
        resource_limit_category, _ = DungeonLimitCategory.objects.update_or_create(
            code="resources",
            defaults={
                "name": "Ресурсы",
                "name_i18n": {"en": "Resources", "ru": "Ресурсы"},
                "limit_count": 0,
                "limit_period_count": 1,
                "limit_period_unit": DungeonLimitCategory.PeriodUnit.DAY,
                "sort_order": 10,
            },
        )

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

        # Боевые локации сгруппированы в 4 тира. Внутри группы все боевые параметры
        # совпадают, между группами растут. required_power подобран так, чтобы шанс
        # прохождения на ОЖИДАЕМОЙ мощи игрока (база 71 + сжатый комплект группы) был
        # 55/15/10/2% (см. success_chance_config: base 75, multiplier 0.6).
        #
        # Лут: rarity_weights — вес поля DungeonLocationItemTemplate.chance на каждый
        # шаблон ранга; slot_plan — какие слоты роняет каждая локация группы по порядку
        # (3 локации => 1+2+2 слота, вся группа покрывает все 5; одиночная гр.4 => все 5).
        # has_mini_game берётся пер-локационно, чтобы не сбрасывать текущие мини-игры.
        dungeon_groups = [
            {
                "params": {"duration": 60, "required_power": 104, "exp": (6, 10), "money": (25, 50), "hp_loss": (4, 8), "drop_chance": 40},
                "rarity_weights": {"f": 100},
                "slot_plan": [["weapon"], ["helmet", "armor"], ["boots", "ring"]],
                "locations": [
                    ({"en": "Old Forest", "ru": "Старый лес"}, {"en": "A forgotten forest on the edge of the kingdom. Weak beasts, bandits, and the first traces of ancient magic hide among the old trees.", "ru": "Забытый лес у окраины королевства. Среди старых деревьев прячутся слабые звери, разбойники и первые следы древней магии."}, True),
                    ({"en": "Misty Ravine", "ru": "Туманный овраг"}, {"en": "A low ravine covered in cold mist. Visibility is poor, and every step may lead to an unexpected encounter.", "ru": "Низкий овраг, постоянно укрытый холодным туманом. Видимость здесь плохая, а каждый шаг может привести к неожиданной встрече."}, False),
                    ({"en": "Abandoned Trail", "ru": "Заброшенная тропа"}, {"en": "An old road once used by traders. Now it is home to wild beasts and lesser creatures waiting in ambush.", "ru": "Старая дорога, по которой давно перестали ходить торговцы. Теперь здесь встречаются дикие звери и мелкие твари, нападающие из засады."}, True),
                ],
            },
            {
                "params": {"duration": 180, "required_power": 184, "exp": (14, 22), "money": (60, 110), "hp_loss": (7, 14), "drop_chance": 50},
                "rarity_weights": {"f": 60, "e": 40},
                "slot_plan": [["weapon"], ["helmet", "armor"], ["boots", "ring"]],
                "locations": [
                    ({"en": "Damp Cave", "ru": "Сырая пещера"}, {"en": "A dark, damp cave with moss-covered walls and strange sounds echoing from below. Danger here no longer feels accidental.", "ru": "Темная влажная пещера, где стены покрыты мхом, а из глубины доносятся странные звуки. Здесь опасность уже не кажется случайной."}, True),
                    ({"en": "Wolf Trail", "ru": "Волчья тропа"}, {"en": "A narrow forest path marked by claw prints and the bones of prey. The pack watches everyone who dares to go deeper.", "ru": "Узкая лесная дорога, отмеченная следами когтей и костями добычи. Стая наблюдает за каждым, кто решится пройти дальше."}, False),
                    ({"en": "Flooded Ruins", "ru": "Затопленные руины"}, {"en": "The remains of an ancient settlement, half-hidden beneath murky water. Guardians of the past still wander among the broken walls.", "ru": "Остатки древнего поселения, наполовину скрытые под мутной водой. Среди разрушенных стен всё ещё блуждают стражи прошлого."}, False),
                ],
            },
            {
                "params": {"duration": 420, "required_power": 204, "exp": (30, 45), "money": (140, 230), "hp_loss": (11, 20), "drop_chance": 60},
                "rarity_weights": {"f": 39, "e": 60, "d": 1},
                "slot_plan": [["weapon"], ["helmet", "armor"], ["boots", "ring"]],
                "locations": [
                    ({"en": "Cursed Grove", "ru": "Проклятая роща"}, {"en": "A grim grove where the trees are twisted by dark power. The very ground seems to resist the living.", "ru": "Мрачная роща, где деревья искривлены темной силой. Здесь сама земля будто сопротивляется живым существам."}, False),
                    ({"en": "Rotten Crypt", "ru": "Гнилой склеп"}, {"en": "An underground crypt filled with the smell of dampness and decay. The dead do not rest peacefully here, and any intruder quickly awakens them.", "ru": "Подземный склеп, пропитанный запахом сырости и разложения. Мертвые здесь лежат неспокойно, а чужое присутствие быстро пробуждает их."}, False),
                    ({"en": "Silent Mine", "ru": "Безмолвная шахта"}, {"en": "An old mine where the sound of pickaxes has long faded. Deep in the tunnels remain not only rusty tools, but also those who never escaped.", "ru": "Старая шахта, в которой давно не слышно ударов кирок. В глубине туннелей остались не только ржавые инструменты, но и те, кто не смог выбраться."}, False),
                ],
            },
            {
                "params": {"duration": 900, "required_power": 239, "exp": (70, 100), "money": (300, 460), "hp_loss": (16, 28), "drop_chance": 75},
                "rarity_weights": {"f": 10, "e": 80, "d": 10},
                "slot_plan": [["weapon", "helmet", "armor", "boots", "ring"]],
                "locations": [
                    ({"en": "Ashen Pass", "ru": "Пепельный перевал"}, {"en": "A dangerous mountain pass covered in gray ash and traces of old battles. Only those ready for a true trial survive here.", "ru": "Опасный горный проход, покрытый серым пеплом и следами старых битв. Здесь выживают только те, кто готов к настоящему испытанию."}, False),
                ],
            },
        ]
        sort_index = 0
        for group in dungeon_groups:
            params = group["params"]
            for loc_index, (names, descriptions, has_mini_game) in enumerate(group["locations"]):
                dungeon, _ = DungeonLocation.objects.update_or_create(
                    name=names["ru"],
                    defaults={
                        "description": descriptions["ru"],
                        "name_i18n": names,
                        "description_i18n": descriptions,
                        "duration_seconds": params["duration"],
                        "required_power": params["required_power"],
                        "experience_min": params["exp"][0],
                        "experience_max": params["exp"][1],
                        "money_min_copper": params["money"][0],
                        "money_max_copper": params["money"][1],
                        "hp_loss_success_percent": params["hp_loss"][0],
                        "hp_loss_fail_percent": params["hp_loss"][1],
                        "item_drop_chance": params["drop_chance"],
                        "has_mini_game": has_mini_game,
                        "location_type": LocationType.DUNGEON,
                        "limit_category": dungeon_limit_category,
                        "daily_limit": 0,
                        "is_active": True,
                        "sort_order": sort_index,
                    },
                )
                sort_index += 1

                slots = group["slot_plan"][loc_index]
                active_template_ids = []
                for slot in slots:
                    for rarity_key, chance in group["rarity_weights"].items():
                        for template in templates_by_rank_slot.get((rarity_key, slot), []):
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
                "limit_category": resource_limit_category,
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
        # Боевые локации: ресурсы равны внутри группы, растут между группами.
        group1_drops = {"forest_herb": (70, 1, 3), "clean_water": (45, 1, 2)}
        group2_drops = {"cave_moss": (60, 1, 2), "bitter_root": (40, 1, 2)}
        group3_drops = {"cave_moss": (50, 1, 3), "bitter_root": (35, 1, 2), "crystal_dust": (20, 1, 1)}
        group4_drops = {"crystal_dust": (40, 1, 2), "cave_moss": (50, 1, 3), "bitter_root": (40, 1, 2)}
        ingredient_drops = {
            # Группа 1
            "Старый лес": group1_drops,
            "Туманный овраг": group1_drops,
            "Заброшенная тропа": group1_drops,
            # Группа 2
            "Сырая пещера": group2_drops,
            "Волчья тропа": group2_drops,
            "Затопленные руины": group2_drops,
            # Группа 3
            "Проклятая роща": group3_drops,
            "Гнилой склеп": group3_drops,
            "Безмолвная шахта": group3_drops,
            # Группа 4
            "Пепельный перевал": group4_drops,
            # Ресурсная локация
            "Лес трав": {
                "forest_herb": (100, 1, 5),
                "clean_water": (50, 1, 2),
            },
        }
        for location_name, drops in ingredient_drops.items():
            location = DungeonLocation.objects.get(name=location_name)
            active_ingredient_ids = []
            for code, (chance_percent, min_quantity, max_quantity) in drops.items():
                ingredient = ingredient_by_code[code]
                DungeonIngredientDrop.objects.update_or_create(
                    location=location,
                    ingredient=ingredient,
                    defaults={
                        "chance_percent": chance_percent,
                        "min_quantity": min_quantity,
                        "max_quantity": max_quantity,
                    },
                )
                active_ingredient_ids.append(ingredient.id)
            DungeonIngredientDrop.objects.filter(location=location).exclude(ingredient_id__in=active_ingredient_ids).delete()

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
