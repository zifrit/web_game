from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, DungeonLocation, DungeonLocationItemTemplate, DungeonMiniGameAttempt, DungeonRun, ItemTemplate, RarityConfig, User, UserItem
from apps.game.services import DungeonMiniGameService, DungeonRunService, GameBalanceService, GameFormulaService, InventoryService, LootGenerationService
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

        self.assertEqual(stats["attack"], self.character.base_attack)

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

    def test_mini_game_success_reduces_remaining_run_time(self):
        self.location.has_mini_game = True
        self.location.duration_seconds = 120
        self.location.save(update_fields=["has_mini_game", "duration_seconds", "updated_at"])
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() + timezone.timedelta(seconds=100)
        run.save(update_fields=["ends_at", "updated_at"])

        attempt = DungeonMiniGameService.start_attempt(self.user, run.id)
        self.assertEqual(len(attempt.board), attempt.config.pairs_count * 2)

        before = run.ends_at
        finished = DungeonMiniGameService.finish_attempt(
            self.user,
            attempt.id,
            success=True,
            moves_count=attempt.config.pairs_count,
            matched_pairs_count=attempt.config.pairs_count,
        )
        run.refresh_from_db()

        self.assertEqual(finished.status, DungeonMiniGameAttempt.SUCCESS)
        self.assertEqual(finished.duration_reduction_seconds, attempt.config.reward_duration_reduction_seconds)
        self.assertEqual(run.ends_at, before - timezone.timedelta(seconds=attempt.config.reward_duration_reduction_seconds))

    def test_mini_game_success_does_not_reduce_before_run_start(self):
        self.location.has_mini_game = True
        self.location.duration_seconds = 120
        self.location.save(update_fields=["has_mini_game", "duration_seconds", "updated_at"])
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.started_at = timezone.now() - timezone.timedelta(seconds=10)
        run.ends_at = run.started_at + timezone.timedelta(seconds=30)
        run.save(update_fields=["started_at", "ends_at", "updated_at"])

        attempt = DungeonMiniGameService.start_attempt(self.user, run.id)
        finished = DungeonMiniGameService.finish_attempt(
            self.user,
            attempt.id,
            success=True,
            moves_count=attempt.config.pairs_count,
            matched_pairs_count=attempt.config.pairs_count,
        )
        run.refresh_from_db()

        self.assertEqual(finished.status, DungeonMiniGameAttempt.SUCCESS)
        self.assertEqual(finished.duration_reduction_seconds, 30)
        self.assertEqual(run.ends_at, run.started_at)

    def test_mini_game_timer_failure_does_not_reduce_run_time(self):
        self.location.has_mini_game = True
        self.location.duration_seconds = 120
        self.location.save(update_fields=["has_mini_game", "duration_seconds", "updated_at"])
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() + timezone.timedelta(seconds=100)
        run.save(update_fields=["ends_at", "updated_at"])
        attempt = DungeonMiniGameService.start_attempt(self.user, run.id)
        attempt.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        attempt.save(update_fields=["expires_at", "updated_at"])

        before = run.ends_at
        finished = DungeonMiniGameService.finish_attempt(
            self.user,
            attempt.id,
            success=True,
            moves_count=attempt.config.pairs_count,
            matched_pairs_count=attempt.config.pairs_count,
        )
        run.refresh_from_db()

        self.assertEqual(finished.status, DungeonMiniGameAttempt.FAILED)
        self.assertEqual(finished.duration_reduction_seconds, 0)
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

        response = self.client.post("/api/characters", {"name": "ApiHero", "class_key": "warrior"}, format="json")
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/dungeons")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        response = self.client.post("/api/dungeon-runs", {"location_id": response.data[0]["id"]}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], DungeonRun.IN_PROGRESS)
