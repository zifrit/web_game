from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.test import override_settings
from django.utils import timezone
from cryptography.fernet import Fernet
import pyotp
from rest_framework import status
from rest_framework.test import APITestCase

from apps.game.models import CharacterClass, DungeonLocation, DungeonMiniGameAttempt, DungeonRun, DungeonRunClaim, DungeonRunStatus, ItemTemplate, MediaAsset, UserItem, UserTwoFactor
from apps.game.permissions import IsSuperuserOrOwner
from apps.game.two_factor import TOTP_INTERVAL_SECONDS, current_timecode


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

    def test_public_and_private_endpoint_permissions(self):
        public_classes = self.client.get("/api/character-classes")
        self.assertEqual(public_classes.status_code, status.HTTP_200_OK)

        public_register = self.client.post("/api/auth/register", {"email": "public@example.com", "password": "strong_password_123"}, format="json")
        self.assertEqual(public_register.status_code, status.HTTP_201_CREATED, public_register.data)

        public_login = self.client.post("/api/auth/login", {"email": "public@example.com", "password": "strong_password_123"}, format="json")
        self.assertEqual(public_login.status_code, status.HTTP_200_OK, public_login.data)

        public_refresh_without_auth_header = self.client.post("/api/auth/refresh", {}, format="json")
        self.assertEqual(public_refresh_without_auth_header.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.credentials()
        for path in ("/api/auth/me", "/api/characters/me", "/api/inventory", "/api/dungeons", "/api/leaderboard?type=level"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, path)

    def test_object_permissions_keep_user_objects_private(self):
        owner = self.register_and_authenticate("owner@example.com")
        self.create_character()
        owner_character = owner.character
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword", rarity_key="f").first()
        item = UserItem.objects.create(
            owner_user=owner,
            source_character=owner_character,
            template=template,
            name=template.name,
            slot=template.slot,
            item_type=template.item_type,
            rarity="f",
            item_level=1,
            stats={"attack": 5},
            durability_current=10,
            durability_max=10,
        )
        location = DungeonLocation.objects.get(name="Старый лес")
        run = DungeonRun.objects.create(
            character=owner_character,
            location=location,
            status=DungeonRunStatus.SUCCESS_WAITING_CLAIM,
            started_at=timezone.now(),
            ends_at=timezone.now(),
            completed_at=timezone.now(),
            success_chance=100,
            is_success=True,
            experience_reward=1,
            money_reward_copper=1,
            items_reward=[],
            durability_loss=0,
        )

        owner_item = self.client.get(f"/api/inventory/items/{item.id}")
        self.assertEqual(owner_item.status_code, status.HTTP_200_OK, owner_item.data)

        intruder = self.register_and_authenticate("intruder@example.com")
        self.create_character("mage")

        intruder_item = self.client.get(f"/api/inventory/items/{item.id}")
        self.assertEqual(intruder_item.status_code, status.HTTP_404_NOT_FOUND)

        intruder_claim = self.client.post(f"/api/dungeon-runs/{run.id}/claim", {}, format="json")
        self.assertEqual(intruder_claim.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(DungeonRunClaim.objects.filter(dungeon_run=run).exists())

        self.client.credentials()
        owner_login = self.client.post("/api/auth/login", {"email": owner.email, "password": "strong_password_123"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {owner_login.data['access_token']}")
        owner_claim = self.client.post(f"/api/dungeon-runs/{run.id}/claim", {}, format="json")
        self.assertEqual(owner_claim.status_code, status.HTTP_200_OK, owner_claim.data)
        self.assertTrue(DungeonRunClaim.objects.filter(dungeon_run=run, user=owner).exists())

        superuser = User.objects.create_superuser(email="admin@example.com", password="strong_password_123")
        permission = IsSuperuserOrOwner()
        request = type("Request", (), {"user": superuser})()
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, item))

        self.client.credentials()
        admin_login = self.client.post("/api/auth/login", {"email": superuser.email, "password": "strong_password_123"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_login.data['access_token']}")
        admin_inventory = self.client.get("/api/inventory")
        self.assertEqual(admin_inventory.status_code, status.HTTP_404_NOT_FOUND)

    def test_register_create_character_and_fetch_profile(self):
        user = self.register_and_authenticate()

        user_avatar = MediaAsset.objects.create(name="User avatar")
        self.assertIsNone(user_avatar.asset_type)
        self.assertEqual(MediaAsset.AssetType.CHARACTERS.label, "Персонажи")
        user_avatar.small.save("user-small.png", ContentFile(b"user-avatar"), save=True)
        user.avatar_media = user_avatar
        user.save(update_fields=["avatar_media"])

        login = self.client.post("/api/auth/login", {"email": user.email, "password": "strong_password_123"}, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("avatar", login.data["user"])
        self.assertTrue(login.data["user"]["avatar"]["small_url"])
        self.assertEqual(set(login.data["user"]["avatar"].keys()), {"large_url", "medium_url", "small_url"})

        me_user = self.client.get("/api/auth/me")
        self.assertEqual(me_user.status_code, status.HTTP_200_OK)
        self.assertIn("avatar", me_user.data)
        self.assertTrue(me_user.data["avatar"]["small_url"])
        self.assertNotIn("original_url", me_user.data["avatar"])
        self.assertNotIn("icon_url", me_user.data["avatar"])

        class_media = MediaAsset.objects.create(name="Warrior class art")
        class_media.medium.save("warrior-medium.png", ContentFile(b"medium-art"), save=True)
        class_media.small.save("warrior-small.png", ContentFile(b"small-art"), save=True)
        warrior_class = CharacterClass.objects.get(key="warrior")
        warrior_class.media = class_media
        warrior_class.save(update_fields=["media"])

        classes = self.client.get("/api/character-classes")
        self.assertEqual(classes.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(classes.data), 4)
        self.assertEqual(classes.data[0]["name"], "Warrior")
        self.assertIn("media", classes.data[0])
        self.assertTrue(classes.data[0]["media"]["medium_url"])
        self.assertEqual(set(classes.data[0]["media"].keys()), {"large_url", "medium_url", "small_url"})

        classes_ru = self.client.get("/api/character-classes", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(classes_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(classes_ru.data[0]["name"], "Воин")

        character = self.create_character()
        self.assertEqual(character["class_key"], "warrior")

        avatar_media = MediaAsset.objects.create(name="Hero avatar")
        avatar_media.large.save("hero-large.png", ContentFile(b"large-avatar"), save=True)
        hero = User.objects.get(email="hero@example.com").character
        hero.avatar_media = avatar_media
        hero.save(update_fields=["avatar_media"])

        me = self.client.get("/api/characters/me")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["class"]["key"], "warrior")
        self.assertEqual(me.data["class"]["name"], "Warrior")
        self.assertEqual(me.data["rank"], "F")
        self.assertIn("media", me.data["class"])
        self.assertTrue(me.data["class"]["media"]["medium_url"])
        self.assertIn("avatar", me.data)
        self.assertTrue(me.data["avatar"]["large_url"])
        self.assertNotIn("original_url", me.data["avatar"])
        self.assertNotIn("icon_url", me.data["avatar"])
        self.assertGreater(me.data["stats"]["power"], 0)
        self.assertEqual(set(me.data["equipment"].keys()), {"weapon", "helmet", "armor", "boots", "ring"})

        me_ru = self.client.get("/api/characters/me", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(me_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(me_ru.data["class"]["name"], "Воин")

    @override_settings(TOTP_ENCRYPTION_KEY=Fernet.generate_key().decode())
    def test_totp_two_factor_login_lifecycle(self):
        register = self.client.post("/api/auth/register", {"email": "totp@example.com", "password": "strong_password_123"}, format="json")
        self.assertEqual(register.status_code, status.HTTP_201_CREATED, register.data)
        self.assertIn("access_token", register.data)
        self.assertEqual(register.data["user"]["two_factor"]["totp_protection"], False)

        unprotected_login = self.client.post("/api/auth/login", {"email": "totp@example.com", "password": "strong_password_123"}, format="json")
        self.assertEqual(unprotected_login.status_code, status.HTTP_200_OK, unprotected_login.data)
        self.assertIn("access_token", unprotected_login.data)

        self.client.credentials()
        unauthorized_setup = self.client.post("/api/auth/two-factor/setup", {}, format="json")
        self.assertEqual(unauthorized_setup.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register.data['access_token']}")
        setup = self.client.post("/api/auth/two-factor/setup", {}, format="json")
        self.assertEqual(setup.status_code, status.HTTP_200_OK, setup.data)
        self.assertIn("secret", setup.data)
        self.assertTrue(setup.data["qr_data_url"].startswith("data:image/png;base64,"))

        user = User.objects.get(email="totp@example.com")
        two_factor = UserTwoFactor.objects.get(user=user)
        self.assertFalse(two_factor.totp_protection)
        self.assertTrue(two_factor.pending_secret_ciphertext)

        confirm_code = pyotp.TOTP(setup.data["secret"]).now()
        confirm = self.client.post("/api/auth/two-factor/confirm", {"code": confirm_code}, format="json")
        self.assertEqual(confirm.status_code, status.HTTP_200_OK, confirm.data)
        self.assertEqual(confirm.data["totp_protection"], True)

        two_factor.refresh_from_db()
        self.assertTrue(two_factor.totp_protection)
        self.assertTrue(two_factor.active_secret_ciphertext)
        self.assertFalse(two_factor.pending_secret_ciphertext)

        protected_login = self.client.post("/api/auth/login", {"email": "totp@example.com", "password": "strong_password_123"}, format="json")
        self.assertEqual(protected_login.status_code, status.HTTP_200_OK, protected_login.data)
        self.assertEqual(protected_login.data["two_factor_required"], True)
        self.assertIn("challenge_token", protected_login.data)
        self.assertNotIn("access_token", protected_login.data)

        wrong_totp = self.client.post(
            "/api/auth/login/totp",
            {"challenge_token": protected_login.data["challenge_token"], "code": "000000"},
            format="json",
        )
        self.assertEqual(wrong_totp.status_code, status.HTTP_400_BAD_REQUEST)

        login_code = pyotp.TOTP(setup.data["secret"]).now()
        verified_login = self.client.post(
            "/api/auth/login/totp",
            {"challenge_token": protected_login.data["challenge_token"], "code": login_code},
            format="json",
        )
        self.assertEqual(verified_login.status_code, status.HTTP_200_OK, verified_login.data)
        self.assertIn("access_token", verified_login.data)

        replay = self.client.post(
            "/api/auth/login/totp",
            {"challenge_token": protected_login.data["challenge_token"], "code": login_code},
            format="json",
        )
        self.assertEqual(replay.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {verified_login.data['access_token']}")
        disable_bad_password = self.client.post(
            "/api/auth/two-factor/disable",
            {"password": "wrong_password", "code": pyotp.TOTP(setup.data["secret"]).at((current_timecode() + 1) * TOTP_INTERVAL_SECONDS)},
            format="json",
        )
        self.assertEqual(disable_bad_password.status_code, status.HTTP_400_BAD_REQUEST)

        disable_code = pyotp.TOTP(setup.data["secret"]).at((current_timecode() + 1) * TOTP_INTERVAL_SECONDS)
        disable = self.client.post(
            "/api/auth/two-factor/disable",
            {"password": "strong_password_123", "code": disable_code},
            format="json",
        )
        self.assertEqual(disable.status_code, status.HTTP_200_OK, disable.data)
        self.assertEqual(disable.data["totp_protection"], False)

        two_factor.refresh_from_db()
        self.assertFalse(two_factor.totp_protection)
        self.assertFalse(two_factor.active_secret_ciphertext)

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
        self.assertEqual(claim.data["success_chance"], 100)
        if claim.data["rewards"]["items"]:
            item = claim.data["rewards"]["items"][0]
            self.assertFalse(item["name"].startswith(("F ", "E ", "D ", "C ", "B ", "A ", "S ", "EX ")))
            self.assertIn(item["rarity"], {"f", "e", "d", "c", "b", "a", "s", "ex"})
            self.assertGreaterEqual(item["item_level"], 1)
            self.assertIn("stats", item)
            self.assertIsInstance(item["stats"], dict)
            self.assertEqual(set(item["durability"].keys()), {"current", "max"})
            self.assertGreaterEqual(item["durability"]["max"], item["durability"]["current"])
        self.assertEqual(DungeonRunClaim.objects.count(), 1)

        second_claim = self.client.post(f"/api/dungeon-runs/{start.data['id']}/claim", {}, format="json")
        self.assertEqual(second_claim.status_code, status.HTTP_200_OK, second_claim.data)
        self.assertEqual(DungeonRunClaim.objects.count(), 1)

    def test_dungeon_mini_game_accelerates_active_run_and_has_history(self):
        self.register_and_authenticate("mini-game@example.com")
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")
        location.duration_seconds = 120
        location.has_mini_game = True
        location.save(update_fields=["duration_seconds", "has_mini_game", "updated_at"])

        start = self.client.post("/api/dungeon-runs", {"location_id": location.id}, format="json")
        self.assertEqual(start.status_code, status.HTTP_201_CREATED, start.data)
        self.assertTrue(start.data["location"]["has_mini_game"])
        self.assertTrue(start.data["mini_game"]["available"])
        self.assertFalse(start.data["mini_game"]["started"])
        self.assertNotIn("config", start.data["mini_game"])
        self.assertNotIn("attempt", start.data["mini_game"])

        attempt = self.client.post(f"/api/dungeon-runs/{start.data['id']}/mini-game/start", {}, format="json")
        self.assertEqual(attempt.status_code, status.HTTP_201_CREATED, attempt.data)
        self.assertEqual(len(attempt.data["board"]), attempt.data["config"]["pairs_count"] * 2)
        self.assertTrue(all(card["state"] == "hidden" for card in attempt.data["board"]))
        self.assertTrue(all(card["face"] is None for card in attempt.data["board"]))
        self.assertTrue(all(card["image_url"] is None for card in attempt.data["board"]))
        self.assertTrue(all("pair_key" not in card for card in attempt.data["board"]))

        current_started = self.client.get("/api/dungeon-runs/current")
        self.assertEqual(current_started.status_code, status.HTTP_200_OK, current_started.data)
        self.assertFalse(current_started.data["mini_game"]["available"])
        self.assertTrue(current_started.data["mini_game"]["started"])
        self.assertEqual(current_started.data["mini_game"]["status"], DungeonMiniGameAttempt.IN_PROGRESS)
        self.assertNotIn("config", current_started.data["mini_game"])
        self.assertNotIn("attempt", current_started.data["mini_game"])

        existing_attempt = self.client.post(f"/api/dungeon-runs/{start.data['id']}/mini-game/start", {}, format="json")
        self.assertEqual(existing_attempt.status_code, status.HTTP_201_CREATED, existing_attempt.data)
        self.assertEqual(existing_attempt.data["id"], attempt.data["id"])
        self.assertEqual(len(existing_attempt.data["board"]), attempt.data["config"]["pairs_count"] * 2)

        run_before = DungeonRun.objects.get(pk=start.data["id"])
        attempt_model = DungeonMiniGameAttempt.objects.get(pk=attempt.data["id"])
        pairs = {}
        for card in attempt_model.board:
            pairs.setdefault(card["pair_key"], []).append(card["id"])

        complete = None
        for card_ids in pairs.values():
            reveal = self.client.post(
                f"/api/dungeon-mini-games/{attempt.data['id']}/reveal",
                {"card_id": card_ids[0]},
                format="json",
            )
            self.assertEqual(reveal.status_code, status.HTTP_200_OK, reveal.data)
            self.assertEqual(reveal.data["id"], card_ids[0])
            self.assertIsNotNone(reveal.data["face"])
            self.assertTrue(reveal.data["image_url"].endswith(".svg"))
            complete = self.client.post(
                f"/api/dungeon-mini-games/{attempt.data['id']}/move",
                {"first_card_id": card_ids[0], "second_card_id": card_ids[1]},
                format="json",
            )
            self.assertEqual(complete.status_code, status.HTTP_200_OK, complete.data)
            self.assertTrue(complete.data["matched"])

        self.assertIsNotNone(complete)
        self.assertEqual(complete.data["attempt"]["status"], DungeonMiniGameAttempt.SUCCESS)
        self.assertGreater(complete.data["attempt"]["duration_reduction_seconds"], 0)
        self.assertTrue(complete.data["reward_granted"])
        forbidden_complete = self.client.post(
            f"/api/dungeon-mini-games/{attempt.data['id']}/complete",
            {"success": True},
            format="json",
        )
        self.assertEqual(forbidden_complete.status_code, status.HTTP_404_NOT_FOUND)
        run_after = DungeonRun.objects.get(pk=start.data["id"])
        self.assertLess(run_after.ends_at, run_before.ends_at)

        current = self.client.get("/api/dungeon-runs/current")
        self.assertEqual(current.status_code, status.HTTP_200_OK, current.data)
        self.assertFalse(current.data["mini_game"]["available"])

        history = self.client.get("/api/dungeon-mini-games/history")
        self.assertEqual(history.status_code, status.HTTP_200_OK, history.data)
        self.assertEqual(history.data[0]["status"], DungeonMiniGameAttempt.SUCCESS)
        self.assertEqual(history.data[0]["location_name"], "Old Forest")

    def test_inventory_equip_repair_and_unequip(self):
        user = self.register_and_authenticate()
        self.create_character()
        user.money_copper = 500
        user.save()
        character = user.character
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword", rarity_key="f").first()
        item = UserItem.objects.create(
            owner_user=user,
            source_character=character,
            template=template,
            name=template.name,
            slot=template.slot,
            item_type=template.item_type,
            rarity="f",
            item_level=1,
            stats={"attack": 5},
            durability_current=5,
            durability_max=10,
        )

        item_media = MediaAsset.objects.create(name="Sword icon", asset_type=MediaAsset.AssetType.WEAPONS)
        item_media.small.save("sword-small.png", ContentFile(b"small"), save=True)
        item_media.medium.save("sword-medium.png", ContentFile(b"medium"), save=True)
        item_media.large.save("sword-large.png", ContentFile(b"large"), save=True)
        template.media = item_media
        template.save(update_fields=["media"])

        inventory = self.client.get("/api/inventory")
        self.assertEqual(inventory.status_code, status.HTTP_200_OK)
        self.assertEqual(inventory.data["items_count"], 1)
        self.assertIsNone(inventory.data["slots_limit"])
        self.assertIsNone(inventory.data["free_slots"])
        self.assertEqual(inventory.data["items"][0]["name"], template.name_i18n["en"])
        self.assertIn("media", inventory.data["items"][0])
        self.assertTrue(inventory.data["items"][0]["media"]["medium_url"])
        self.assertNotIn("icon_url", inventory.data["items"][0])

        item_detail_ru = self.client.get(f"/api/inventory/items/{item.id}", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(item_detail_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(item_detail_ru.data["name"], template.name_i18n["ru"])
        self.assertTrue(item_detail_ru.data["media"]["large_url"])
        self.assertEqual(set(item_detail_ru.data["media"].keys()), {"large_url", "medium_url", "small_url"})

        equip = self.client.post(f"/api/inventory/items/{item.id}/equip", {}, format="json")
        self.assertEqual(equip.status_code, status.HTTP_200_OK, equip.data)
        self.assertEqual(equip.data["equipped_slot"], "weapon")
        self.assertEqual(equip.data["item"]["id"], item.id)
        self.assertIsNone(equip.data["replaced_item"])
        self.assertEqual(equip.data["equipment"]["weapon"]["id"], item.id)
        self.assertEqual(equip.data["equipment_summary"]["attack"], 5.0)
        self.assertEqual(equip.data["stats"]["power"], equip.data["new_power"])

        character_response = self.client.get("/api/characters/me")
        self.assertEqual(character_response.status_code, status.HTTP_200_OK)
        self.assertEqual(character_response.data["equipment"]["weapon"]["durability"], {"current": 5, "max": 10})

        equipped_inventory = self.client.get("/api/inventory")
        self.assertEqual(equipped_inventory.status_code, status.HTTP_200_OK)
        self.assertEqual(equipped_inventory.data["equipped"]["weapon"]["durability"], {"current": 5, "max": 10})

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
        self.assertEqual(preview.data["repair_cost_copper"], 25)
        self.assertEqual(preview.data["can_repair"], True)

        repair = self.client.post(f"/api/inventory/items/{item.id}/repair", {}, format="json")
        self.assertEqual(repair.status_code, status.HTTP_200_OK, repair.data)
        self.assertEqual(repair.data["durability"]["current"], 10)
        self.assertEqual(repair.data["remaining_money_copper"], 475)

        item.durability_current = 6
        item.save(update_fields=["durability_current"])
        bulk_preview = self.client.post("/api/inventory/items/repair-preview", {"item_ids": [item.id]}, format="json")
        self.assertEqual(bulk_preview.status_code, status.HTTP_200_OK, bulk_preview.data)
        self.assertEqual(bulk_preview.data["items_count"], 1)
        self.assertEqual(bulk_preview.data["repair_cost_copper"], 10)

        bulk_repair = self.client.post("/api/inventory/items/repair", {"item_ids": [item.id]}, format="json")
        self.assertEqual(bulk_repair.status_code, status.HTTP_200_OK, bulk_repair.data)
        self.assertEqual(bulk_repair.data["repair_cost_copper"], 10)
        self.assertEqual(bulk_repair.data["remaining_money_copper"], 465)

        replacement = UserItem.objects.create(
            owner_user=user,
            source_character=character,
            template=template,
            name="Новый меч",
            slot=template.slot,
            item_type=template.item_type,
            rarity="f",
            item_level=1,
            stats={"attack": 7},
            durability_current=10,
            durability_max=10,
        )
        replace = self.client.post(f"/api/inventory/items/{replacement.id}/equip", {}, format="json")
        self.assertEqual(replace.status_code, status.HTTP_200_OK, replace.data)
        self.assertEqual(replace.data["item"]["id"], replacement.id)
        self.assertEqual(replace.data["replaced_item"]["id"], item.id)
        self.assertEqual(replace.data["equipment"]["weapon"]["id"], replacement.id)
        self.assertEqual(replace.data["stats"]["power"], replace.data["new_power"])

        unequip = self.client.post(f"/api/inventory/items/{replacement.id}/unequip", {}, format="json")
        self.assertEqual(unequip.status_code, status.HTTP_200_OK)
        self.assertEqual(unequip.data["item"]["id"], replacement.id)
        self.assertIsNone(unequip.data["equipment"]["weapon"])
        self.assertEqual(unequip.data["stats"]["power"], unequip.data["new_power"])

        destroy_preview = self.client.post("/api/inventory/items/destroy-preview", {"item_ids": [replacement.id]}, format="json")
        self.assertEqual(destroy_preview.status_code, status.HTTP_200_OK, destroy_preview.data)
        self.assertEqual(destroy_preview.data["items_count"], 1)
        self.assertEqual(destroy_preview.data["refund_copper"], 20)

        destroy = self.client.post("/api/inventory/items/destroy", {"item_ids": [replacement.id]}, format="json")
        self.assertEqual(destroy.status_code, status.HTTP_200_OK, destroy.data)
        self.assertEqual(destroy.data["refund_copper"], 20)
        self.assertFalse(UserItem.objects.filter(pk=replacement.id).exists())

    def test_inventory_is_paginated_by_twenty_four_items(self):
        user = self.register_and_authenticate("pack@example.com")
        self.create_character()
        character = user.character
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword", rarity_key="f").first()
        for index in range(25):
            UserItem.objects.create(
                owner_user=user,
                source_character=character,
                template=template,
                name=f"{template.name} {index}",
                slot=template.slot,
                item_type=template.item_type,
                rarity="f",
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
        user = self.register_and_authenticate()
        self.create_character()
        avatar = MediaAsset.objects.create(name="Leaderboard avatar")
        avatar.small.save("board-small.png", ContentFile(b"small"), save=True)
        user.character.avatar_media = avatar
        user.character.save(update_fields=["avatar_media"])

        response = self.client.get("/api/leaderboard?type=level")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "level")
        self.assertEqual(response.data["items"][0]["rank"], 1)
        self.assertEqual(response.data["items"][0]["class"]["name"], "Warrior")
        self.assertTrue(response.data["items"][0]["avatar"]["small_url"])
        self.assertNotIn("icon_url", response.data["items"][0]["avatar"])

    def test_dungeons_and_validation_are_localized(self):
        self.register_and_authenticate("locale@example.com")
        self.create_character()

        dungeon_media = MediaAsset.objects.create(name="Old forest art")
        dungeon_media.medium.save("forest-medium.png", ContentFile(b"forest"), save=True)
        location = DungeonLocation.objects.get(name="Старый лес")
        location.media = dungeon_media
        location.save(update_fields=["media"])

        dungeons = self.client.get("/api/dungeons")
        self.assertEqual(dungeons.status_code, status.HTTP_200_OK)
        self.assertEqual(dungeons.data[0]["name"], "Old Forest")
        self.assertEqual(dungeons.data[0]["description"], "A safe starting location.")
        self.assertIn("has_mini_game", dungeons.data[0])
        self.assertTrue(dungeons.data[0]["media"]["medium_url"])
        self.assertNotIn("original_url", dungeons.data[0]["media"])

        dungeons_ru = self.client.get("/api/dungeons", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(dungeons_ru.status_code, status.HTTP_200_OK)
        self.assertEqual(dungeons_ru.data[0]["name"], "Старый лес")
        self.assertEqual(dungeons_ru.data[0]["description"], "Безопасная стартовая локация.")

        bad_board = self.client.get("/api/leaderboard?type=gold", HTTP_ACCEPT_LANGUAGE="ru")
        self.assertEqual(bad_board.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(bad_board.data["detail"], "В MVP доступен только рейтинг по уровню.")
