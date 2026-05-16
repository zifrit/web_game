from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.game.models import DungeonLocation, DungeonRunClaim, ItemTemplate, UserItem


User = get_user_model()


class MvpApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_game", verbosity=0)

    def register_and_authenticate(self, email="hero@example.com"):
        response = self.client.post("/api/auth/register", {"email": email, "password": "strong_password_123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access_token']}")
        return User.objects.get(email=email)

    def create_character(self, class_key="warrior"):
        response = self.client.post("/api/characters", {"name": "Arthas", "class_key": class_key}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def test_register_create_character_and_fetch_profile(self):
        self.register_and_authenticate()

        classes = self.client.get("/api/character-classes")
        self.assertEqual(classes.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(classes.data), 4)

        character = self.create_character()
        self.assertEqual(character["class_key"], "warrior")

        me = self.client.get("/api/characters/me")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["class"]["key"], "warrior")
        self.assertGreater(me.data["stats"]["power"], 0)
        self.assertEqual(set(me.data["equipment"].keys()), {"weapon", "helmet", "armor", "boots", "ring"})

    def test_dungeon_run_claim_is_idempotent(self):
        self.register_and_authenticate()
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")
        location.duration_seconds = 0
        location.required_power = 1
        location.item_drop_chance = 100
        location.save()

        start = self.client.post("/api/dungeon-runs", {"location_id": location.id}, format="json")
        self.assertEqual(start.status_code, status.HTTP_201_CREATED, start.data)

        current = self.client.get("/api/dungeon-runs/current")
        self.assertEqual(current.status_code, status.HTTP_200_OK)
        self.assertEqual(current.data["status"], "SUCCESS_WAITING_CLAIM")

        claim = self.client.post(f"/api/dungeon-runs/{start.data['id']}/claim", {}, format="json")
        self.assertEqual(claim.status_code, status.HTTP_200_OK, claim.data)
        self.assertEqual(claim.data["status"], "CLAIMED")
        self.assertEqual(claim.data["is_success"], True)
        self.assertEqual(DungeonRunClaim.objects.count(), 1)

        second_claim = self.client.post(f"/api/dungeon-runs/{start.data['id']}/claim", {}, format="json")
        self.assertEqual(second_claim.status_code, status.HTTP_200_OK, second_claim.data)
        self.assertEqual(DungeonRunClaim.objects.count(), 1)

    def test_inventory_equip_repair_and_unequip(self):
        user = self.register_and_authenticate()
        self.create_character()
        user.money_copper = 500
        user.save()
        character = user.character
        template = ItemTemplate.objects.get(name="Ржавый меч")
        item = UserItem.objects.create(
            owner_user=user,
            source_character=character,
            template=template,
            name="Обычный ржавый меч",
            slot=template.slot,
            item_type=template.item_type,
            rarity="common",
            item_level=1,
            stats={"attack": 5},
            durability_current=5,
            durability_max=10,
        )

        equip = self.client.post(f"/api/inventory/items/{item.id}/equip", {}, format="json")
        self.assertEqual(equip.status_code, status.HTTP_200_OK, equip.data)
        self.assertEqual(equip.data["equipped_slot"], "weapon")

        item.durability_current = 0
        item.save(update_fields=["durability_current"])
        location = DungeonLocation.objects.first()
        blocked = self.client.post("/api/dungeon-runs", {"location_id": location.id}, format="json")
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        preview = self.client.get(f"/api/inventory/items/{item.id}/repair-preview")
        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertEqual(preview.data["repair_cost_copper"], 100)
        self.assertEqual(preview.data["can_repair"], True)

        repair = self.client.post(f"/api/inventory/items/{item.id}/repair", {}, format="json")
        self.assertEqual(repair.status_code, status.HTTP_200_OK, repair.data)
        self.assertEqual(repair.data["durability"]["current"], 10)
        self.assertEqual(repair.data["remaining_money_copper"], 400)

        unequip = self.client.post(f"/api/inventory/items/{item.id}/unequip", {}, format="json")
        self.assertEqual(unequip.status_code, status.HTTP_200_OK)

    def test_leaderboard_level_response(self):
        self.register_and_authenticate()
        self.create_character()

        response = self.client.get("/api/leaderboard?type=level")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "level")
        self.assertEqual(response.data["items"][0]["rank"], 1)
