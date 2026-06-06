from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, DungeonIngredientDrop, DungeonLocation, DungeonLocationItemTemplate, DungeonMiniGameAttempt, DungeonMiniGameConfig, DungeonRun, HeroIngredientStorage, HeroPotionStorage, IngredientTemplate, ItemTemplate, PotionTemplate, RarityConfig, User, UserItem
from apps.game.services import DungeonMiniGameService, DungeonRunService, GameBalanceService, GameFormulaService, IngredientDropService, IngredientService, InventoryService, LootGenerationService, PotionService
from apps.game.services.ranks import RANKS, rank_for_level


class GameFormulaTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("formula@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "Formula", CharacterClass.objects.get(key="warrior"))

    def test_power_ignores_broken_equipment(self):
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()
        UserItem.objects.create(
            owner_user=self.user,
            equipped_character=self.character,
            template=template,
            name="Broken sword",
            slot="weapon",
            item_type="sword",
            rarity="f",
            item_level=1,
            stats={"attack": 100},
            durability_current=0,
            durability_max=10,
        )

        stats = GameFormulaService.character_stats(self.character)

        self.assertEqual(stats["attack"], self.character.attack)

    def test_success_chance_is_capped(self):
        self.assertEqual(GameFormulaService.success_chance(10_000, 1), 100)
        self.assertEqual(GameFormulaService.success_chance(1, 10_000), 35)

    def test_item_economy_uses_bankers_rounding(self):
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()
        item = UserItem.objects.create(
            owner_user=self.user,
            template=template,
            name="E sword",
            slot="weapon",
            item_type="sword",
            rarity="e",
            item_level=1,
            stats={"attack": 5},
            durability_current=9,
            durability_max=10,
        )

        self.assertEqual(GameFormulaService.repair_cost(item), 3)
        self.assertEqual(GameFormulaService.destroy_refund(item), 22)


class DungeonLifecycleTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("run@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "Runner", CharacterClass.objects.get(key="warrior"))
        self.location = DungeonLocation.objects.get(name="Старый лес")

    def test_cannot_start_second_active_run(self):
        DungeonRunService.start_run(self.user, self.location.id)

        with self.assertRaises(Exception):
            DungeonRunService.start_run(self.user, self.location.id)

    def test_claim_is_idempotent(self):
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])

        first = DungeonRunService.claim_run(self.user, run.id)
        second = DungeonRunService.claim_run(self.user, run.id)

        self.assertEqual(first.claim.id, second.claim.id)
        self.assertEqual(DungeonRun.objects.get(id=run.id).status, DungeonRun.CLAIMED)

    def test_claim_level_up_updates_intrinsic_stats_and_power_cache(self):
        run = DungeonRunService.start_run(self.user, self.location.id)
        required = GameFormulaService.experience_required(self.character.level)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.experience_reward = required
        run.money_reward_copper = 0
        run.status = DungeonRun.SUCCESS_WAITING_CLAIM
        run.is_success = True
        run.save(
            update_fields=[
                "ends_at",
                "success_chance",
                "experience_reward",
                "money_reward_copper",
                "status",
                "is_success",
                "updated_at",
            ]
        )
        old_attack = self.character.attack
        old_power = self.character.power_cached

        result = DungeonRunService.claim_run(self.user, run.id)
        self.character.refresh_from_db()

        self.assertEqual(result.old_level, 1)
        self.assertEqual(result.new_level, 2)
        self.assertGreater(self.character.attack, old_attack)
        self.assertGreater(self.character.power_cached, old_power)
        self.assertEqual(self.character.power_cached, GameFormulaService.character_stats(self.character)["power"])

    def test_broken_equipped_item_blocks_start(self):
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()
        UserItem.objects.create(
            owner_user=self.user,
            equipped_character=self.character,
            template=template,
            name="Broken sword",
            slot="weapon",
            item_type="sword",
            rarity="f",
            item_level=1,
            stats={"attack": 5},
            durability_current=0,
            durability_max=10,
        )

        with self.assertRaises(Exception):
            DungeonRunService.start_run(self.user, self.location.id)

    def _config(self, difficulty="6"):
        return DungeonMiniGameConfig.objects.get(difficulty=difficulty)

    def _enable_mini_game(self, duration_seconds=120):
        self.location.has_mini_game = True
        self.location.duration_seconds = duration_seconds
        self.location.save(update_fields=["has_mini_game", "duration_seconds", "updated_at"])

    def _solve(self, attempt):
        """Доводит партию до победы честными ходами через reveal/make_move."""

        pairs = {}
        for card in attempt.board:
            pairs.setdefault(card["pair_key"], []).append(card["id"])
        last = None
        for first_id, second_id in pairs.values():
            DungeonMiniGameService.reveal_card(self.user, attempt.id, card_id=first_id)
            last = DungeonMiniGameService.make_move(
                self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
            )
        return last

    def test_mini_game_success_reduces_remaining_run_time(self):
        self._enable_mini_game(duration_seconds=120)
        config = self._config("6")  # percent=10 -> round(120*0.1)=12s
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() + timezone.timedelta(seconds=100)
        run.save(update_fields=["ends_at", "updated_at"])

        attempt = DungeonMiniGameService.start_attempt(self.user, run.id, config_id=config.id)
        self.assertEqual(len(attempt.board), config.pairs_count * 2)

        before = run.ends_at
        result = self._solve(attempt)
        attempt.refresh_from_db()
        run.refresh_from_db()

        self.assertTrue(result["finished"])
        self.assertEqual(attempt.status, DungeonMiniGameAttempt.SUCCESS)
        self.assertEqual(attempt.duration_reduction_seconds, 12)
        self.assertEqual(run.ends_at, before - timezone.timedelta(seconds=12))

    def test_mini_game_success_does_not_reduce_before_run_start(self):
        self._enable_mini_game(duration_seconds=120)
        config = self._config("6")  # raw reduction 12s exceeds the 5s run window
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.started_at = timezone.now()
        run.ends_at = run.started_at + timezone.timedelta(seconds=5)
        run.save(update_fields=["started_at", "ends_at", "updated_at"])

        attempt = DungeonMiniGameService.start_attempt(self.user, run.id, config_id=config.id)
        self._solve(attempt)
        attempt.refresh_from_db()
        run.refresh_from_db()

        self.assertEqual(attempt.status, DungeonMiniGameAttempt.SUCCESS)
        self.assertEqual(attempt.duration_reduction_seconds, 5)
        self.assertEqual(run.ends_at, run.started_at)

    def test_mini_game_timer_failure_does_not_reduce_run_time(self):
        self._enable_mini_game(duration_seconds=120)
        config = self._config("6")
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() + timezone.timedelta(seconds=100)
        run.save(update_fields=["ends_at", "updated_at"])
        attempt = DungeonMiniGameService.start_attempt(self.user, run.id, config_id=config.id)
        attempt.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        attempt.save(update_fields=["expires_at", "updated_at"])

        before = run.ends_at
        first_id, second_id = attempt.board[0]["id"], attempt.board[1]["id"]
        result = DungeonMiniGameService.make_move(
            self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
        )
        attempt.refresh_from_db()
        run.refresh_from_db()

        self.assertTrue(result["finished"])
        self.assertEqual(attempt.status, DungeonMiniGameAttempt.FAILED)
        self.assertEqual(attempt.duration_reduction_seconds, 0)
        self.assertEqual(run.ends_at, before)


class InventoryTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("inventory@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "Gear", CharacterClass.objects.get(key="warrior"))
        self.template = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()

    def create_item(self, **overrides):
        data = {
            "owner_user": self.user,
            "template": self.template,
            "name": "Sword",
            "slot": "weapon",
            "item_type": "sword",
            "rarity": "f",
            "item_level": 1,
            "stats": {"attack": 5},
            "durability_current": 5,
            "durability_max": 10,
        }
        data.update(overrides)
        return UserItem.objects.create(**data)

    def test_equip_replaces_existing_slot(self):
        old_item = self.create_item(name="Old sword")
        new_item = self.create_item(name="New sword")

        InventoryService.equip(self.user, old_item.id)
        InventoryService.equip(self.user, new_item.id)

        old_item.refresh_from_db()
        new_item.refresh_from_db()
        self.assertIsNone(old_item.equipped_character_id)
        self.assertEqual(new_item.equipped_character_id, self.character.id)

    def test_repair_requires_money_and_restores_durability(self):
        item = self.create_item(durability_current=1, durability_max=5)
        self.user.money_copper = 100
        self.user.save(update_fields=["money_copper"])

        result = InventoryService.repair_items(self.user, [item.id])
        item.refresh_from_db()

        self.assertEqual(item.durability_current, 5)
        self.assertEqual(result["repair_cost_copper"], 10)
        self.assertEqual(result["remaining_money_copper"], 90)

    def test_destroy_equipped_item_deletes_record_and_refunds_money(self):
        item = self.create_item(equipped_character=self.character, durability_current=5, durability_max=10)
        self.user.money_copper = 20
        self.user.save(update_fields=["money_copper"])

        result = InventoryService.destroy_items(self.user, [item.id])
        self.user.refresh_from_db()

        self.assertEqual(result["refund_copper"], 10)
        self.assertEqual(self.user.money_copper, 30)
        self.assertFalse(UserItem.objects.filter(pk=item.id).exists())

    def test_bulk_preview_ignores_foreign_items(self):
        foreign = User.objects.create_user("foreign@example.com", "strongpass123")
        foreign_item = self.create_item(owner_user=foreign)
        own_item = self.create_item(durability_current=6, durability_max=10)

        preview = InventoryService.repair_preview(self.user, [foreign_item.id, own_item.id])

        self.assertEqual(preview["item_ids"], [own_item.id])
        self.assertEqual(preview["repair_cost_copper"], 10)


class RankedSeedTests(TestCase):
    def setUp(self):
        SeedCommand().handle()

    def test_level_boundaries_map_to_letter_ranks(self):
        expected = {
            1: "F",
            10: "F",
            11: "E",
            20: "E",
            21: "D",
            30: "D",
            31: "C",
            40: "C",
            41: "B",
            50: "B",
            51: "A",
            60: "A",
            61: "S",
            70: "S",
            71: "EX",
            80: "EX",
        }

        for level, label in expected.items():
            self.assertEqual(rank_for_level(level).label, label)

    def test_seed_creates_rank_configs_and_ranked_templates(self):
        self.assertEqual(list(RarityConfig.objects.order_by("sort_order").values_list("key", flat=True)), [rank.key for rank in RANKS])
        for rank in RANKS:
            config = RarityConfig.objects.get(key=rank.key)
            self.assertEqual(config.min_item_level, rank.min_level)
            self.assertEqual(config.max_item_level, rank.max_level)

        self.assertEqual(ItemTemplate.objects.filter(is_active=True, rarity_key__in=[rank.key for rank in RANKS]).count(), 176)
        for rank in RANKS:
            expected_count = 1 if rank.key == "ex" else 3
            for item_type in ("sword", "dagger", "staff", "bow", "ring", "armor", "boots", "helmet"):
                self.assertEqual(ItemTemplate.objects.filter(rarity_key=rank.key, item_type=item_type, is_active=True).count(), expected_count)

    def test_seed_item_templates_command_is_idempotent(self):
        call_command("seed_item_templates", verbosity=0)
        call_command("seed_item_templates", verbosity=0)

        self.assertEqual(ItemTemplate.objects.filter(is_active=True, rarity_key__in=[rank.key for rank in RANKS]).count(), 176)

    def test_rank_template_names_stay_clean_and_rank_is_separate(self):
        f_swords = set(ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True).values_list("name", flat=True))
        e_swords = set(ItemTemplate.objects.filter(rarity_key="e", item_type="sword", is_active=True).values_list("name", flat=True))

        self.assertEqual(f_swords, {"Меч новичка", "Меч странника", "Меч ополченца"})
        self.assertEqual(e_swords, {"Меч разведчика", "Меч стража", "Меч железной клятвы"})
        self.assertTrue(f_swords.isdisjoint(e_swords))

    def test_seed_item_templates_deactivates_previous_ranked_names(self):
        ItemTemplate.objects.create(
            name="F Training Sword 1",
            name_i18n={"en": "F Training Sword 1", "ru": "F Training Sword 1"},
            slot="weapon",
            item_type="sword",
            rarity_key="f",
            allowed_classes=["warrior"],
            possible_stats={"attack": {"min": 1, "max": 2}},
            is_active=True,
        )

        call_command("seed_item_templates", verbosity=0)

        self.assertFalse(ItemTemplate.objects.get(name="F Training Sword 1").is_active)

    def test_seed_game_deactivates_legacy_rarity_configs(self):
        RarityConfig.objects.update_or_create(
            key="common",
            defaults={
                "name": "Common",
                "stat_multiplier": 1,
                "economy_multiplier": 1,
                "min_item_level": 1,
                "max_item_level": 3,
                "min_stats_count": 1,
                "max_stats_count": 1,
                "sort_order": 99,
                "is_active": True,
            },
        )

        SeedCommand().handle()

        self.assertFalse(RarityConfig.objects.get(key="common").is_active)

    def test_loot_item_level_matches_selected_rank(self):
        user = User.objects.create_user("loot@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "Loot", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        location.item_drop_chance = 100

        for rank in RANKS:
            DungeonLocationItemTemplate.objects.filter(location=location).delete()
            template = ItemTemplate.objects.filter(rarity_key=rank.key, item_type="sword", is_active=True).first()
            DungeonLocationItemTemplate.objects.create(location=location, item_template=template, chance=100)
            draft = LootGenerationService.generate_item_reward(character, location)
            self.assertIsNotNone(draft)
            self.assertEqual(draft["rarity"], rank.key)
            self.assertGreaterEqual(draft["item_level"], rank.min_level)
            self.assertLessEqual(draft["item_level"], rank.max_level)

    def test_seed_game_links_only_nonzero_rank_templates_to_locations(self):
        old_forest = DungeonLocation.objects.get(name="Старый лес")
        ranks = set(old_forest.location_item_templates.values_list("item_template__rarity_key", flat=True))

        self.assertEqual(ranks, {"f", "e"})
        self.assertFalse(old_forest.location_item_templates.filter(chance=0).exists())

    def test_location_item_template_chance_must_be_between_one_and_one_hundred(self):
        location = DungeonLocation.objects.get(name="Старый лес")
        template = ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True).first()

        with self.assertRaises(ValidationError):
            DungeonLocationItemTemplate(location=location, item_template=template, chance=0).full_clean()

        with self.assertRaises(ValidationError):
            DungeonLocationItemTemplate(location=location, item_template=template, chance=101).full_clean()

    def test_active_drop_location_requires_active_templates(self):
        location = DungeonLocation.objects.get(name="Старый лес")
        DungeonLocationItemTemplate.objects.filter(location=location).delete()
        location.item_drop_chance = 100

        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_item_drop_chance_zero_prevents_loot(self):
        user = User.objects.create_user("no-drop@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "NoDrop", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        location.item_drop_chance = 0

        self.assertIsNone(LootGenerationService.generate_item_reward(character, location))

    def test_loot_uses_only_templates_linked_to_location(self):
        user = User.objects.create_user("linked@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "Linked", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        template = ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True).first()
        unlinked = ItemTemplate.objects.filter(rarity_key="e", item_type="sword", is_active=True).first()
        DungeonLocationItemTemplate.objects.filter(location=location).delete()
        DungeonLocationItemTemplate.objects.create(location=location, item_template=template, chance=100)
        location.item_drop_chance = 100

        for _ in range(5):
            draft = LootGenerationService.generate_item_reward(character, location)
            self.assertEqual(draft["template_id"], template.id)
            self.assertNotEqual(draft["template_id"], unlinked.id)

    def test_loot_filters_templates_disallowed_for_character(self):
        user = User.objects.create_user("filtered@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "Filtered", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        staff = ItemTemplate.objects.filter(rarity_key="f", item_type="staff", is_active=True).first()
        DungeonLocationItemTemplate.objects.filter(location=location).delete()
        DungeonLocationItemTemplate.objects.create(location=location, item_template=staff, chance=100)
        location.item_drop_chance = 100

        self.assertIsNone(LootGenerationService.generate_item_reward(character, location))

    def test_link_chance_weights_template_selection(self):
        user = User.objects.create_user("weighted@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "Weighted", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        low = ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True).first()
        high = ItemTemplate.objects.filter(rarity_key="e", item_type="sword", is_active=True).first()
        DungeonLocationItemTemplate.objects.filter(location=location).delete()
        DungeonLocationItemTemplate.objects.create(location=location, item_template=low, chance=1)
        DungeonLocationItemTemplate.objects.create(location=location, item_template=high, chance=99)
        location.item_drop_chance = 100

        with patch("apps.game.services.loot.random.uniform", side_effect=[0, 50]):
            draft = LootGenerationService.generate_item_reward(character, location)

        self.assertEqual(draft["template_id"], high.id)

    def test_loot_generation_loads_location_links_without_n_plus_one(self):
        user = User.objects.create_user("queries@example.com", "strongpass123")
        character = GameBalanceService.create_character(user, "Queries", CharacterClass.objects.get(key="warrior"))
        location = DungeonLocation.objects.get(name="Старый лес")
        templates = list(ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True)[:3])
        DungeonLocationItemTemplate.objects.filter(location=location).delete()
        for template in templates:
            DungeonLocationItemTemplate.objects.create(location=location, item_template=template, chance=10)
        location.item_drop_chance = 100
        GameBalanceService.rarity_config("f")

        with patch("apps.game.services.loot.random.uniform", side_effect=[0, 0]):
            with self.assertNumQueries(1):
                draft = LootGenerationService.generate_item_reward(character, location)

        self.assertEqual(draft["template_id"], templates[0].id)


class ApiSmokeTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()

    def test_register_create_character_and_start_run(self):
        response = self.client.post("/api/auth/register", {"email": "api@example.com", "password": "strongpass123"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access_token']}")

        response = self.client.post("/api/characters", {"name": "ApiHero", "class_key": "warrior", "gender": "male"}, format="json")
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/dungeons")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        response = self.client.post("/api/dungeon-runs", {"location_id": response.data[0]["id"]}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], DungeonRun.IN_PROGRESS)


class StatRefactorTests(TestCase):
    """Проверки Этапа 0: max_hp/current_hp, intellect и формула power."""

    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("stat@example.com", "strongpass123")
        self.warrior = CharacterClass.objects.get(key="warrior")
        self.character = GameBalanceService.create_character(self.user, "Stat", self.warrior)

    def test_create_character_initializes_hp_and_intellect(self):
        self.assertEqual(self.character.max_hp, self.warrior.start_max_hp)
        self.assertEqual(self.character.current_hp, self.warrior.start_max_hp)
        self.assertEqual(self.character.intellect, self.warrior.start_intellect)
        self.assertGreaterEqual(self.character.intellect, 1)

    def test_power_excludes_max_hp_and_weights_intellect(self):
        from apps.game.services.config import GameConfigService

        weights = GameConfigService.get_config("power_formula_config")
        self.assertNotIn("health", weights)
        self.assertEqual(weights["intellect"], 1.5)
        self.assertEqual(weights["critical_chance"], 1.5)
        self.assertEqual(weights["evasion"], 1.5)

        base = {
            "max_hp": 999,
            "intellect": 10,
            "attack": 0,
            "defense": 0,
            "critical_chance": 0,
            "evasion": 0,
        }
        power_with_hp = GameFormulaService.power_from_stats(base)
        power_without_hp = GameFormulaService.power_from_stats({**base, "max_hp": 0})
        self.assertEqual(power_with_hp, power_without_hp)
        self.assertEqual(power_with_hp, round(10 * 1.5, 2))

    def test_character_stats_aggregates_equipment_max_hp(self):
        template = ItemTemplate.objects.filter(slot="armor", item_type="armor").first()
        UserItem.objects.create(
            owner_user=self.user,
            equipped_character=self.character,
            template=template,
            name="HP armor",
            slot="armor",
            item_type="armor",
            rarity="f",
            item_level=1,
            stats={"max_hp": 25},
            durability_current=10,
            durability_max=10,
        )
        stats = GameFormulaService.character_stats(self.character)
        self.assertEqual(stats["max_hp"], self.character.max_hp + 25)
        self.assertIn("intellect", stats)

    def test_character_me_exposes_hp_fields(self):
        client = APIClient()
        token = self.client_login()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/characters/me")
        self.assertEqual(response.status_code, 200)
        stats = response.data["stats"]
        self.assertIn("max_hp", stats)
        self.assertIn("current_hp", stats)
        self.assertIn("hp_percent", stats)
        self.assertIn("intellect", stats)
        self.assertEqual(stats["current_hp"], stats["max_hp"])
        self.assertEqual(stats["hp_percent"], 100.0)

    def client_login(self) -> str:
        client = APIClient()
        response = client.post(
            "/api/auth/login",
            {"email": "stat@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        return response.data["access_token"]


class HpCycleTests(TestCase):
    """Проверки Этапа 1: списание HP после данжа и клампинг при смене экипировки."""

    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("hp@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "HpHero", CharacterClass.objects.get(key="warrior"))
        self.location = DungeonLocation.objects.get(name="Старый лес")

    def test_hp_formula_ceil_and_min(self):
        # 120 * 4% = 4.8 -> ceil 5
        self.assertEqual(GameFormulaService.hp_loss(120, 4), 5)
        # 0% -> 0
        self.assertEqual(GameFormulaService.hp_loss(120, 0), 0)
        # маленький процент всё равно минимум 1
        self.assertEqual(GameFormulaService.hp_loss(10, 0.1), 1)

    def test_successful_run_deducts_hp(self):
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])

        result = DungeonRunService.claim_run(self.user, run.id)
        self.character.refresh_from_db()

        expected_loss = GameFormulaService.hp_loss(self.character.max_hp, self.location.hp_loss_success_percent)
        self.assertGreater(expected_loss, 0)
        self.assertEqual(result.hp_loss, expected_loss)
        self.assertEqual(self.character.current_hp, self.character.max_hp - expected_loss)
        self.assertEqual(result.current_hp, self.character.current_hp)

    def test_hp_never_below_zero(self):
        # стартуем при полном HP (иначе сработает блок Этапа 2), затем роняем HP перед claim
        run = DungeonRunService.start_run(self.user, self.location.id)
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp"])
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 0  # провал -> большая потеря
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])

        DungeonRunService.claim_run(self.user, run.id)
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, 0)

    def test_unequip_clamps_current_hp(self):
        template = ItemTemplate.objects.filter(slot="armor", item_type="armor").first()
        item = UserItem.objects.create(
            owner_user=self.user,
            template=template,
            name="HP armor",
            slot="armor",
            item_type="armor",
            rarity="f",
            item_level=1,
            stats={"max_hp": 30},
            durability_current=10,
            durability_max=10,
        )
        InventoryService.equip(self.user, item.id)
        self.character.refresh_from_db()
        # «лечим» героя до нового максимума с экипировкой
        total_max = int(GameFormulaService.character_stats(self.character)["max_hp"])
        self.character.current_hp = total_max
        self.character.save(update_fields=["current_hp"])

        InventoryService.unequip(self.user, item.id)
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, self.character.max_hp)


class HpPenaltyTests(TestCase):
    """Проверки Этапа 2: штрафы success_chance от низкого HP и блок старта."""

    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("pen@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "Pen", CharacterClass.objects.get(key="warrior"))
        self.location = DungeonLocation.objects.get(name="Старый лес")

    def _set_hp_percent(self, pct: float) -> None:
        self.character.refresh_from_db()
        self.character.current_hp = int(round(self.character.max_hp * pct / 100))
        self.character.save(update_fields=["current_hp"])

    def test_penalty_tiers(self):
        max_hp = self.character.max_hp
        self.assertEqual(GameFormulaService.hp_success_penalty(max_hp, max_hp), 0.0)
        self.assertEqual(GameFormulaService.hp_success_penalty(int(max_hp * 0.4), max_hp), 5.0)
        self.assertEqual(GameFormulaService.hp_success_penalty(int(max_hp * 0.2), max_hp), 15.0)

    def test_block_threshold(self):
        max_hp = self.character.max_hp
        self.assertTrue(GameFormulaService.is_hp_too_low_to_start(int(max_hp * 0.05), max_hp))
        self.assertFalse(GameFormulaService.is_hp_too_low_to_start(int(max_hp * 0.5), max_hp))

    def test_start_blocked_at_low_hp(self):
        self._set_hp_percent(5)
        with self.assertRaises(Exception):
            DungeonRunService.start_run(self.user, self.location.id)

    def test_start_applies_penalty(self):
        run_full = DungeonRunService.start_run(self.user, self.location.id)
        base_chance = run_full.success_chance
        run_full.delete()

        self._set_hp_percent(20)  # 10–29% -> штраф 15
        run_low = DungeonRunService.start_run(self.user, self.location.id)
        self.assertEqual(round(base_chance - run_low.success_chance, 2), 15.0)

    def test_success_chance_subtracts_penalty(self):
        # равные power/required -> base 75 (не упирается в кап), штраф вычитается напрямую
        self.assertEqual(
            GameFormulaService.success_chance(50, 50, hp_penalty=0)
            - GameFormulaService.success_chance(50, 50, hp_penalty=15),
            15.0,
        )


class PotionTests(TestCase):
    """Проверки Этапа 3: формула лечения, использование зелий и склад героя."""

    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("potion@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "PotionHero", CharacterClass.objects.get(key="warrior"))
        self.potion = PotionTemplate.objects.get(code="medium_healing_potion")  # 40%
        self.storage = HeroPotionStorage.objects.create(character=self.character, potion=self.potion, count=3)

    def _max_hp(self) -> int:
        self.character.refresh_from_db()
        return int(GameFormulaService.character_stats(self.character)["max_hp"])

    def test_potion_heal_round_and_minimum(self):
        # 100 * 40% = 40
        self.assertEqual(GameFormulaService.potion_heal(100, 40), 40)
        # 0% -> 0
        self.assertEqual(GameFormulaService.potion_heal(100, 0), 0)
        # маленький процент всё равно минимум 1
        self.assertEqual(GameFormulaService.potion_heal(10, 1), 1)

    def test_use_potion_heals_and_decrements(self):
        max_hp = self._max_hp()
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp"])
        expected = GameFormulaService.potion_heal(max_hp, self.potion.heal_percent)

        result = PotionService.use_potion(self.user, self.potion.id, quantity=1)

        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, 1 + expected)
        self.assertEqual(result["healed"], expected)
        self.storage.refresh_from_db()
        self.assertEqual(self.storage.count, 2)

    def test_heal_is_capped_at_max_hp(self):
        max_hp = self._max_hp()
        self.character.current_hp = max_hp - 1
        self.character.save(update_fields=["current_hp"])

        result = PotionService.use_potion(self.user, self.potion.id, quantity=1)

        self.assertEqual(result["current_hp"], max_hp)
        self.assertEqual(result["healed"], 1)

    def test_use_potion_blocked_at_full_hp(self):
        self.character.current_hp = self._max_hp()
        self.character.save(update_fields=["current_hp"])

        with self.assertRaises(Exception):
            PotionService.use_potion(self.user, self.potion.id, quantity=1)

        self.storage.refresh_from_db()
        self.assertEqual(self.storage.count, 3)

    def test_not_enough_potions(self):
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp"])

        with self.assertRaises(Exception):
            PotionService.use_potion(self.user, self.potion.id, quantity=99)

        self.storage.refresh_from_db()
        self.assertEqual(self.storage.count, 3)

    def test_zero_count_row_kept_and_hidden(self):
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp"])
        self.storage.count = 1
        self.storage.save(update_fields=["count"])

        PotionService.use_potion(self.user, self.potion.id, quantity=1)

        self.storage.refresh_from_db()
        self.assertEqual(self.storage.count, 0)
        self.assertFalse(PotionService.list_potions(self.user).filter(pk=self.storage.pk).exists())

    def test_api_list_and_use(self):
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp"])
        client = APIClient()
        login = client.post("/api/auth/login", {"email": "potion@example.com", "password": "strongpass123"}, format="json")
        self.assertEqual(login.status_code, 200, login.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access_token']}")

        listing = client.get("/api/potions")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(listing.data[0]["id"], self.potion.id)

        used = client.post("/api/potions/use", {"potion_id": self.potion.id, "quantity": 1}, format="json")
        self.assertEqual(used.status_code, 200, used.data)
        self.assertGreater(used.data["current_hp"], 1)
        self.assertEqual(used.data["remaining"], 2)


class IngredientTests(TestCase):
    """Проверки Этапа 4: дроп ингредиентов, склад героя и ответ claim."""

    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("ingredient@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user, "Gatherer", CharacterClass.objects.get(key="warrior")
        )
        self.location = DungeonLocation.objects.get(name="Старый лес")
        self.herb = IngredientTemplate.objects.get(code="forest_herb")

    def _set_single_drop(self, chance_percent=100, min_quantity=2, max_quantity=2, ingredient=None):
        """Оставляет у локации единственную детерминированную запись дропа."""

        ingredient = ingredient or self.herb
        self.location.ingredient_drops.all().delete()
        return DungeonIngredientDrop.objects.create(
            location=self.location,
            ingredient=ingredient,
            chance_percent=chance_percent,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
        )

    def _force_successful_run(self):
        """Создаёт готовый к claim успешный забег с истёкшим таймером."""

        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])
        return run

    def test_roll_drops_always_drops_at_full_chance(self):
        self._set_single_drop(chance_percent=100, min_quantity=2, max_quantity=2)
        drops = IngredientDropService.roll_drops(self.location)
        self.assertEqual(drops, [{"ingredient_id": self.herb.id, "quantity": 2}])

    def test_roll_drops_quantity_within_range(self):
        self._set_single_drop(chance_percent=100, min_quantity=1, max_quantity=3)
        for _ in range(20):
            drops = IngredientDropService.roll_drops(self.location)
            self.assertEqual(len(drops), 1)
            self.assertTrue(1 <= drops[0]["quantity"] <= 3)

    def test_successful_claim_adds_ingredients_once(self):
        self._set_single_drop(chance_percent=100, min_quantity=2, max_quantity=2)
        run = self._force_successful_run()

        DungeonRunService.claim_run(self.user, run.id)
        storage = HeroIngredientStorage.objects.get(character=self.character, ingredient=self.herb)
        self.assertEqual(storage.count, 2)

        # Повторный claim не должен начислять ингредиенты ещё раз.
        DungeonRunService.claim_run(self.user, run.id)
        storage.refresh_from_db()
        self.assertEqual(storage.count, 2)

    def test_two_successful_runs_stack_into_single_row(self):
        self._set_single_drop(chance_percent=100, min_quantity=2, max_quantity=2)
        first = self._force_successful_run()
        DungeonRunService.claim_run(self.user, first.id)
        second = self._force_successful_run()
        DungeonRunService.claim_run(self.user, second.id)

        rows = HeroIngredientStorage.objects.filter(character=self.character, ingredient=self.herb)
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.first().count, 4)

    def test_failed_run_grants_no_ingredients(self):
        self._set_single_drop(chance_percent=100, min_quantity=2, max_quantity=2)
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 0
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])

        with patch("apps.game.services.dungeon_runs.random.uniform", return_value=50.0):
            DungeonRunService.claim_run(self.user, run.id)

        run.refresh_from_db()
        self.assertEqual(run.ingredients_reward, [])
        self.assertFalse(HeroIngredientStorage.objects.filter(character=self.character, count__gt=0).exists())

    def test_list_ingredients_hides_zero_count_rows(self):
        HeroIngredientStorage.objects.create(character=self.character, ingredient=self.herb, count=0)
        visible = IngredientService.list_ingredients(self.user)
        self.assertEqual(list(visible), [])

    def test_api_ingredients_listing(self):
        HeroIngredientStorage.objects.create(character=self.character, ingredient=self.herb, count=5)
        client = APIClient()
        login = client.post(
            "/api/auth/login",
            {"email": "ingredient@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access_token']}")

        listing = client.get("/api/ingredients")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        row = listing.data[0]
        self.assertEqual(row["id"], self.herb.id)
        self.assertEqual(row["code"], "forest_herb")
        self.assertEqual(row["count"], 5)
        self.assertIn("category", row)

    def test_claim_response_includes_ingredients(self):
        self._set_single_drop(chance_percent=100, min_quantity=2, max_quantity=2)
        run = self._force_successful_run()
        client = APIClient()
        login = client.post(
            "/api/auth/login",
            {"email": "ingredient@example.com", "password": "strongpass123"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access_token']}")

        response = client.post(f"/api/dungeon-runs/{run.id}/claim")
        self.assertEqual(response.status_code, 200, response.data)
        ingredients = response.data["rewards"]["ingredients"]
        run.refresh_from_db()
        self.assertEqual(len(ingredients), len(run.ingredients_reward))
        self.assertEqual(ingredients[0]["id"], self.herb.id)
        self.assertEqual(ingredients[0]["quantity"], 2)
        self.assertEqual(
            run.ingredients_reward,
            [{"ingredient_id": self.herb.id, "quantity": 2}],
        )
