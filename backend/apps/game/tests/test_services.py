from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, DungeonLocation, DungeonRun, ItemTemplate, RarityConfig, User, UserItem
from apps.game.ranks import RANKS, rank_for_level
from apps.game.services import DungeonRunService, GameBalanceService, GameFormulaService, InventoryService, LootGenerationService


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

    def test_rank_template_names_are_rank_specific(self):
        f_swords = set(ItemTemplate.objects.filter(rarity_key="f", item_type="sword", is_active=True).values_list("name", flat=True))
        e_swords = set(ItemTemplate.objects.filter(rarity_key="e", item_type="sword", is_active=True).values_list("name", flat=True))

        self.assertEqual(f_swords, {"F Меч новичка", "F Меч странника", "F Меч ополченца"})
        self.assertEqual(e_swords, {"E Меч разведчика", "E Меч стража", "E Меч железной клятвы"})
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
            location.rarity_chances = {candidate.key: 100 if candidate.key == rank.key else 0 for candidate in RANKS}
            draft = LootGenerationService.generate_item_reward(character, location)
            self.assertIsNotNone(draft)
            self.assertEqual(draft["rarity"], rank.key)
            self.assertGreaterEqual(draft["item_level"], rank.min_level)
            self.assertLessEqual(draft["item_level"], rank.max_level)


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
