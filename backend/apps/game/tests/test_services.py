from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, DungeonLocation, DungeonRun, ItemTemplate, User, UserItem
from apps.game.services import DungeonRunService, GameBalanceService, GameFormulaService, InventoryService


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
            rarity="common",
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
            name="Uncommon sword",
            slot="weapon",
            item_type="sword",
            rarity="uncommon",
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
            rarity="common",
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
            "rarity": "common",
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
