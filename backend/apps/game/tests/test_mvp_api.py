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
        self.assertEqual(classes.data[0]["name"], "Warrior")

        classes_ru = self.client.get("/api/character-classes", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(classes_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(classes_ru.data[0]["name"], "Воин")

        character = self.create_character()
        self.assertEqual(character["class_key"], "warrior")

        me = self.client.get("/api/characters/me")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["class"]["key"], "warrior")
        self.assertEqual(me.data["class"]["name"], "Warrior")
        self.assertGreater(me.data["stats"]["power"], 0)
        self.assertEqual(set(me.data["equipment"].keys()), {"weapon", "helmet", "armor", "boots", "ring"})

        me_ru = self.client.get("/api/characters/me", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(me_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(me_ru.data["class"]["name"], "Воин")

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
        self.assertEqual(current.data["location"]["name"], "Old Forest")

        claim = self.client.post(f"/api/dungeon-runs/{start.data['id']}/claim", {}, format="json")
        self.assertEqual(claim.status_code, status.HTTP_200_OK, claim.data)
        self.assertEqual(claim.data["status"], "CLAIMED")
        self.assertEqual(claim.data["is_success"], True)
        if claim.data["rewards"]["items"]:
            self.assertTrue(claim.data["rewards"]["items"][0]["name"].startswith(("Common", "Uncommon", "Rare", "Epic")))
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

        inventory = self.client.get("/api/inventory")
        self.assertEqual(inventory.status_code, status.HTTP_200_OK)
        self.assertEqual(inventory.data["items_count"], 1)
        self.assertIsNone(inventory.data["slots_limit"])
        self.assertIsNone(inventory.data["free_slots"])
        self.assertEqual(inventory.data["items"][0]["name"], "Common Rusty Sword")

        item_detail_ru = self.client.get(f"/api/inventory/items/{item.id}", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(item_detail_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(item_detail_ru.data["name"], "Обычный Ржавый меч")

        equip = self.client.post(f"/api/inventory/items/{item.id}/equip", {}, format="json")
        self.assertEqual(equip.status_code, status.HTTP_200_OK, equip.data)
        self.assertEqual(equip.data["equipped_slot"], "weapon")

        item.durability_current = 0
        item.save(update_fields=["durability_current"])
        location = DungeonLocation.objects.first()
        blocked = self.client.post("/api/dungeon-runs", {"location_id": location.id}, format="json")
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Broken equipped items", str(blocked.data))

        blocked_ru = self.client.post("/api/dungeon-runs", {"location_id": location.id}, format="json", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(blocked_ru.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Сломанные", str(blocked_ru.data))

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

    def test_inventory_is_paginated_by_twenty_four_items(self):
        user = self.register_and_authenticate("pack@example.com")
        self.create_character()
        character = user.character
        template = ItemTemplate.objects.get(name="Ржавый меч")
        for index in range(25):
            UserItem.objects.create(
                owner_user=user,
                source_character=character,
                template=template,
                name=f"Обычный ржавый меч {index}",
                slot=template.slot,
                item_type=template.item_type,
                rarity="common",
                item_level=1,
                stats={"attack": 5},
                durability_current=10,
                durability_max=10,
            )

        first_page = self.client.get("/api/inventory")
        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(first_page.data["items_count"], 25)
        self.assertIsNone(first_page.data["slots_limit"])
        self.assertEqual(len(first_page.data["items"]), 24)
        self.assertEqual(first_page.data["pagination"]["page_size"], 24)
        self.assertEqual(first_page.data["pagination"]["total_pages"], 2)
        self.assertEqual(first_page.data["pagination"]["has_next"], True)

        second_page = self.client.get("/api/inventory?page=2")
        self.assertEqual(second_page.status_code, status.HTTP_200_OK)
        self.assertEqual(len(second_page.data["items"]), 1)
        self.assertEqual(second_page.data["pagination"]["has_next"], False)

    def test_leaderboard_level_response(self):
        self.register_and_authenticate()
        self.create_character()

        response = self.client.get("/api/leaderboard?type=level")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "level")
        self.assertEqual(response.data["items"][0]["rank"], 1)
        self.assertEqual(response.data["items"][0]["class"]["name"], "Warrior")

    def test_dungeons_and_validation_are_localized(self):
        self.register_and_authenticate("locale@example.com")
        self.create_character()

        dungeons = self.client.get("/api/dungeons")
        self.assertEqual(dungeons.status_code, status.HTTP_200_OK)
        self.assertEqual(dungeons.data[0]["name"], "Old Forest")
        self.assertEqual(dungeons.data[0]["description"], "A safe starting location.")

        dungeons_ru = self.client.get("/api/dungeons", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(dungeons_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(dungeons_ru.data[0]["name"], "Старый лес")
        self.assertEqual(dungeons_ru.data[0]["description"], "Безопасная стартовая локация.")

        bad_board = self.client.get("/api/leaderboard?type=gold", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(bad_board.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(bad_board.data["detail"], "В MVP доступен только рейтинг по уровню.")
