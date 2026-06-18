import json
from unittest.mock import patch

from django.contrib import admin
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from rest_framework import status
from rest_framework.serializers import ValidationError as DRFValidationError
from rest_framework.test import APIClient, APITestCase

from apps.game.admin import _get_task_map
from apps.game.models import (
    AutoDungeonRun,
    AutoDungeonRunClaim,
    AutoDungeonRunStatus,
    CharacterClass,
    DungeonLocation,
    DungeonMiniGameConfig,
    DungeonRun,
    DungeonRunClaim,
    DungeonRunStatus,
    IngredientTemplate,
    ItemTemplate,
    User,
    UserItem,
)
from apps.game.services import (
    AutoDungeonRunService,
    ClaimResult,
    DungeonMiniGameService,
    DungeonRunService,
    GameBalanceService,
)


class AutoRunPeriodicTaskTests(TestCase):
    def test_dungeon_run_processors_are_seeded_as_periodic_tasks(self):
        expected_tasks = {
            "Завершение готовых походов в данжи": "apps.game.tasks.complete_due_dungeon_runs",
            "Обработка готовых автозапусков данжей": "apps.game.tasks.process_due_auto_dungeon_runs",
        }

        periodic_tasks = PeriodicTask.objects.filter(name__in=expected_tasks).select_related(
            "interval"
        )

        self.assertEqual(periodic_tasks.count(), len(expected_tasks))
        for periodic_task in periodic_tasks:
            self.assertEqual(periodic_task.task, expected_tasks[periodic_task.name])
            self.assertTrue(periodic_task.enabled)
            self.assertEqual(periodic_task.interval.every, 10)
            self.assertEqual(periodic_task.interval.period, "seconds")
            self.assertEqual(json.loads(periodic_task.kwargs), {"limit": 100})

    def test_admin_task_map_includes_auto_run_processor(self):
        task_map = _get_task_map()

        self.assertIn("process_due_auto_dungeon_runs", task_map)
        self.assertEqual(
            task_map["process_due_auto_dungeon_runs"].name,
            "apps.game.tasks.process_due_auto_dungeon_runs",
        )


class AutoRunAdminTests(TestCase):
    def test_auto_run_models_registered_in_admin(self):
        self.assertIn(AutoDungeonRun, admin.site._registry)
        self.assertIn(AutoDungeonRunClaim, admin.site._registry)

        auto_admin = admin.site._registry[AutoDungeonRun]
        claim_admin = admin.site._registry[AutoDungeonRunClaim]

        self.assertEqual(auto_admin.autocomplete_fields, ("user", "character", "location", "current_run"))
        self.assertEqual(claim_admin.autocomplete_fields, ("auto_run", "dungeon_run", "claim"))
        self.assertEqual(auto_admin.readonly_fields, ())
        self.assertEqual(claim_admin.readonly_fields, ())
        self.assertTrue(any(inline.model is AutoDungeonRunClaim for inline in auto_admin.inlines))


class AutoRunModelTests(TestCase):
    def setUp(self):
        call_command("seed_game", verbosity=0)
        self.user = User.objects.create_user("auto-run@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user,
            "AutoRunner",
            CharacterClass.objects.get(key="warrior"),
        )
        self.location = DungeonLocation.objects.get(name="Старый лес")
        self.run = self.create_dungeon_run()

    def create_dungeon_run(self):
        now = timezone.now()
        return DungeonRun.objects.create(
            character=self.character,
            location=self.location,
            status=DungeonRunStatus.CLAIMED,
            started_at=now,
            ends_at=now,
            completed_at=now,
            success_chance=100,
            is_success=True,
            experience_reward=10,
            money_reward_copper=5,
            items_reward=[],
            ingredients_reward=[],
            durability_loss=0,
            hp_loss=0,
        )

    def create_auto_run(self, **overrides):
        params = {
            "user": self.user,
            "character": self.character,
            "location": self.location,
            "current_run": self.run,
        }
        params.update(overrides)
        return AutoDungeonRun.objects.create(**params)

    def create_claim(self, dungeon_run):
        return DungeonRunClaim.objects.create(
            dungeon_run=dungeon_run,
            user=self.user,
            character=self.character,
            experience_claimed=10,
            money_claimed_copper=5,
        )

    def test_only_one_active_or_stopping_auto_run_per_character(self):
        self.create_auto_run(status=AutoDungeonRunStatus.ACTIVE)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_auto_run(status=AutoDungeonRunStatus.STOPPING)

    def test_only_one_unread_stopped_summary_per_character(self):
        self.create_auto_run(
            status=AutoDungeonRunStatus.STOPPED,
            summary_unread=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_auto_run(
                    status=AutoDungeonRunStatus.STOPPED,
                    summary_unread=True,
                )

    def test_auto_run_claim_is_unique_by_dungeon_run_and_claim(self):
        auto_run = self.create_auto_run(status=AutoDungeonRunStatus.STOPPED)
        first_run = self.run
        first_claim = self.create_claim(first_run)
        second_run = self.create_dungeon_run()
        second_claim = self.create_claim(second_run)

        AutoDungeonRunClaim.objects.create(
            auto_run=auto_run,
            dungeon_run=first_run,
            claim=first_claim,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AutoDungeonRunClaim.objects.create(
                    auto_run=auto_run,
                    dungeon_run=first_run,
                    claim=second_claim,
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AutoDungeonRunClaim.objects.create(
                    auto_run=auto_run,
                    dungeon_run=second_run,
                    claim=first_claim,
                )

    def test_new_auto_run_fields_have_russian_verbose_names(self):
        auto_run_verbose_names = {
            field.name: field.verbose_name
            for field in AutoDungeonRun._meta.fields
            if field.name
            in {
                "user",
                "character",
                "location",
                "current_run",
                "status",
                "stop_reason_code",
                "stop_reason_message",
                "stop_reason_details",
                "summary_unread",
                "started_at",
                "stopped_at",
                "runs_claimed",
                "success_count",
                "failure_count",
                "experience_total",
                "money_total_copper",
                "items_total",
                "ingredients_total",
                "current_hp",
                "max_hp",
                "durability_loss_total",
                "durability_changes",
                "summary",
            }
        }
        claim_verbose_names = {
            field.name: field.verbose_name
            for field in AutoDungeonRunClaim._meta.fields
            if field.name
            in {
                "auto_run",
                "dungeon_run",
                "claim",
                "is_success",
                "experience",
                "money_copper",
                "items_count",
                "ingredients_count",
                "current_hp",
                "max_hp",
                "hp_loss",
                "durability_loss",
                "items_preview",
                "ingredients_preview",
                "durability_changes",
                "counted_at",
            }
        }

        self.assertEqual(auto_run_verbose_names["stop_reason_message"], "Причина остановки")
        self.assertEqual(auto_run_verbose_names["summary_unread"], "Сводка не прочитана")
        self.assertEqual(auto_run_verbose_names["runs_claimed"], "Учтено походов")
        self.assertEqual(auto_run_verbose_names["money_total_copper"], "Всего меди")
        self.assertEqual(claim_verbose_names["auto_run"], "Автозапуск")
        self.assertEqual(claim_verbose_names["dungeon_run"], "Поход в данж")
        self.assertEqual(claim_verbose_names["is_success"], "Успешный поход")
        self.assertEqual(claim_verbose_names["hp_loss"], "Потеря HP")
        self.assertEqual(claim_verbose_names["items_preview"], "Превью предметов")


class AutoRunServiceStartTests(TestCase):
    def setUp(self):
        call_command("seed_game", verbosity=0)
        self.user = User.objects.create_user("auto-run-service@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user,
            "AutoServiceRunner",
            CharacterClass.objects.get(key="warrior"),
        )
        self.location = DungeonLocation.objects.get(name="Старый лес")

    def create_claimed_run(self):
        now = timezone.now()
        return DungeonRun.objects.create(
            character=self.character,
            location=self.location,
            status=DungeonRunStatus.CLAIMED,
            started_at=now,
            ends_at=now,
            completed_at=now,
            success_chance=100,
            is_success=True,
            experience_reward=10,
            money_reward_copper=5,
            items_reward=[],
            ingredients_reward=[],
            durability_loss=0,
            hp_loss=0,
        )

    def create_unread_stopped_auto_run(self):
        run = self.create_claimed_run()
        return AutoDungeonRun.objects.create(
            user=self.user,
            character=self.character,
            location=self.location,
            current_run=run,
            status=AutoDungeonRunStatus.STOPPED,
            summary_unread=True,
            stopped_at=timezone.now(),
        )

    def test_start_auto_run_creates_first_run_and_auto_state(self):
        run, auto_run = AutoDungeonRunService.start_auto_run(self.user, self.location.id)

        self.assertEqual(run.status, DungeonRunStatus.IN_PROGRESS)
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.ACTIVE)
        self.assertEqual(auto_run.current_run_id, run.id)
        self.assertEqual(auto_run.location_id, self.location.id)
        self.assertEqual(auto_run.current_hp, self.character.current_hp)
        self.assertGreater(auto_run.max_hp, 0)

    def test_start_normal_run_blocked_by_active_auto_run(self):
        AutoDungeonRunService.start_auto_run(self.user, self.location.id)

        with self.assertRaises(DRFValidationError):
            DungeonRunService.start_run(self.user, self.location.id)

    def test_unread_summary_blocks_new_start(self):
        self.create_unread_stopped_auto_run()

        with self.assertRaises(DRFValidationError):
            DungeonRunService.start_run(self.user, self.location.id)

    def test_stop_auto_run_is_one_way(self):
        AutoDungeonRunService.start_auto_run(self.user, self.location.id)

        first_stop = AutoDungeonRunService.request_stop(self.user)
        second_stop = AutoDungeonRunService.request_stop(self.user)

        first_stop.refresh_from_db()
        self.assertEqual(first_stop.status, AutoDungeonRunStatus.STOPPING)
        self.assertEqual(second_stop.status, AutoDungeonRunStatus.STOPPING)

    def test_mark_summary_read_unblocks_starts(self):
        auto_run = self.create_unread_stopped_auto_run()

        marked = AutoDungeonRunService.mark_summary_read(self.user)

        auto_run.refresh_from_db()
        self.assertEqual(marked.id, auto_run.id)
        self.assertFalse(auto_run.summary_unread)
        run = DungeonRunService.start_run(self.user, self.location.id)
        self.assertEqual(run.status, DungeonRunStatus.IN_PROGRESS)


class AutoRunApiTests(APITestCase):
    def setUp(self):
        call_command("seed_game", verbosity=0)
        self.password = "strongpass123"

    def register_and_authenticate(self, email):
        response = self.client.post(
            "/api/auth/register",
            {"email": email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access_token']}")
        return User.objects.get(email=email)

    def create_character(self):
        response = self.client.post(
            "/api/characters",
            {"name": "Auto Runner", "class_key": "warrior", "gender": "male"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def create_claimed_run(self, user, location):
        now = timezone.now()
        return DungeonRun.objects.create(
            character=user.character,
            location=location,
            status=DungeonRunStatus.CLAIMED,
            started_at=now,
            ends_at=now,
            completed_at=now,
            success_chance=100,
            is_success=True,
            experience_reward=10,
            money_reward_copper=5,
            items_reward=[],
            ingredients_reward=[],
            durability_loss=0,
            hp_loss=0,
        )

    def test_start_auto_run_and_current_envelope(self):
        self.register_and_authenticate("auto-run-api-start@example.com")
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")

        start = self.client.post(
            "/api/dungeon-runs",
            {"location_id": location.id, "auto_run": True},
            format="json",
        )

        self.assertEqual(start.status_code, status.HTTP_201_CREATED)
        auto_run = AutoDungeonRun.objects.get(status=AutoDungeonRunStatus.ACTIVE)
        current = self.client.get("/api/dungeon-runs/current")
        self.assertEqual(current.status_code, status.HTTP_200_OK)
        self.assertIn("current_run", current.data)
        self.assertIn("auto_run", current.data)
        self.assertEqual(current.data["current_run"]["id"], start.data["id"])
        self.assertEqual(current.data["auto_run"]["id"], auto_run.id)
        self.assertEqual(current.data["auto_run"]["status"], AutoDungeonRunStatus.ACTIVE)
        self.assertEqual(current.data["auto_run"]["current_hp"], auto_run.current_hp)
        self.assertEqual(current.data["auto_run"]["max_hp"], auto_run.max_hp)
        self.assertIn("hp_loss_total", current.data["auto_run"])

    def test_stop_endpoint_sets_stopping(self):
        self.register_and_authenticate("auto-run-api-stop@example.com")
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")
        start = self.client.post(
            "/api/dungeon-runs",
            {"location_id": location.id, "auto_run": True},
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_201_CREATED)

        response = self.client.post("/api/dungeon-auto-runs/current/stop", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], AutoDungeonRunStatus.STOPPING)

    def test_summary_read_endpoint_is_idempotent(self):
        user = self.register_and_authenticate("auto-run-api-summary@example.com")
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")
        run = self.create_claimed_run(user, location)
        auto_run = AutoDungeonRun.objects.create(
            user=user,
            character=user.character,
            location=location,
            current_run=run,
            status=AutoDungeonRunStatus.STOPPED,
            summary_unread=True,
            stopped_at=timezone.now(),
        )

        first = self.client.post("/api/dungeon-auto-runs/current/summary/read", {}, format="json")
        second = self.client.post("/api/dungeon-auto-runs/current/summary/read", {}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        auto_run.refresh_from_db()
        self.assertFalse(auto_run.summary_unread)

    def test_current_run_localizes_auto_run_stop_reason_message(self):
        user = self.register_and_authenticate("auto-run-api-reason@example.com")
        self.create_character()
        location = DungeonLocation.objects.get(name="Старый лес")
        run = self.create_claimed_run(user, location)
        AutoDungeonRun.objects.create(
            user=user,
            character=user.character,
            location=location,
            current_run=run,
            status=AutoDungeonRunStatus.STOPPED,
            summary_unread=True,
            stopped_at=timezone.now(),
            stop_reason_code="player_stopped",
            stop_reason_message="Auto run stopped after the current run.",
        )

        response = self.client.get("/api/dungeon-runs/current", HTTP_ACCEPT_LANGUAGE="ru")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["auto_run"]["stop_reason_message"],
            "Автозапуск остановлен после текущего данжа.",
        )


class AutoRunWorkerTests(TestCase):
    def setUp(self):
        call_command("seed_game", verbosity=0)
        self.user = User.objects.create_user("auto-run-worker@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user,
            "WorkerRunner",
            CharacterClass.objects.get(key="warrior"),
        )
        self.location = DungeonLocation.objects.get(name="Старый лес")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _due_auto_run(self):
        run, auto_run = AutoDungeonRunService.start_auto_run(self.user, self.location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])
        return run, auto_run

    def _due_auto_run_for(self, user, location):
        run, auto_run = AutoDungeonRunService.start_auto_run(user, location.id)
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.success_chance = 100
        run.save(update_fields=["ends_at", "success_chance", "updated_at"])
        return run, auto_run

    def _user_item(self, name, *, durability_current=10, durability_max=10, equipped=False):
        template = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()
        return UserItem.objects.create(
            owner_user=self.user,
            source_character=self.character,
            equipped_character=self.character if equipped else None,
            template=template,
            name=name,
            slot="weapon",
            item_type="sword",
            rarity="f",
            item_level=1,
            stats={"attack": 1},
            durability_current=durability_current,
            durability_max=durability_max,
        )

    def _claimed_run(self, *, is_success=True, experience=10, money=5, ingredients=None):
        now = timezone.now()
        return DungeonRun.objects.create(
            character=self.character,
            location=self.location,
            status=DungeonRunStatus.CLAIMED,
            started_at=now,
            ends_at=now,
            completed_at=now,
            success_chance=100 if is_success else 0,
            is_success=is_success,
            experience_reward=experience,
            money_reward_copper=money,
            items_reward=[],
            ingredients_reward=ingredients or [],
            durability_loss=0,
            hp_loss=0,
        )

    def test_worker_claims_and_starts_next_run(self):
        original_run, auto_run = self._due_auto_run()

        processed = AutoDungeonRunService.process_due_auto_runs(limit=10)

        self.assertEqual(processed, 1)
        auto_run.refresh_from_db()
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.ACTIVE)
        self.assertNotEqual(auto_run.current_run_id, original_run.id)
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertTrue(
            AutoDungeonRunClaim.objects.filter(
                auto_run=auto_run,
                dungeon_run=original_run,
            ).exists()
        )

    def test_worker_retry_does_not_double_count_claim(self):
        original_run, auto_run = self._due_auto_run()
        AutoDungeonRunService.process_due_auto_runs(limit=10)
        auto_run.refresh_from_db()
        new_run = auto_run.current_run
        new_run.ends_at = timezone.now() + timezone.timedelta(hours=1)
        new_run.save(update_fields=["ends_at", "updated_at"])

        AutoDungeonRunService.process_single_auto_run(auto_run.id)

        auto_run.refresh_from_db()
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertEqual(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).count(), 1)

    def test_worker_retry_accounts_claimed_current_run_without_double_granting(self):
        original_run, auto_run = self._due_auto_run()
        DungeonRunService.finalize_due_run(original_run.id)
        claimed = DungeonRunService.claim_run(self.user, original_run.id)
        self.user.refresh_from_db()
        money_after_claim = self.user.money_copper

        processed = AutoDungeonRunService.process_single_auto_run(auto_run.id)

        self.assertTrue(processed)
        self.user.refresh_from_db()
        auto_run.refresh_from_db()
        self.assertEqual(self.user.money_copper, money_after_claim)
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.ACTIVE)
        self.assertNotEqual(auto_run.current_run_id, original_run.id)
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertEqual(
            AutoDungeonRunClaim.objects.get(dungeon_run=original_run).claim_id,
            claimed.claim.id,
        )

        next_run = auto_run.current_run
        next_run.ends_at = timezone.now() + timezone.timedelta(hours=1)
        next_run.save(update_fields=["ends_at", "updated_at"])

        AutoDungeonRunService.process_single_auto_run(auto_run.id)
        auto_run.refresh_from_db()
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertEqual(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).count(), 1)

    def test_combat_failure_counts_and_continues_to_next_run(self):
        original_run, auto_run = self._due_auto_run()
        self.location.hp_loss_fail_percent = 0
        self.location.save(update_fields=["hp_loss_fail_percent", "updated_at"])
        original_run.success_chance = 0
        original_run.save(update_fields=["success_chance", "updated_at"])

        with patch("apps.game.services.dungeon_runs.random.uniform", return_value=50.0):
            processed = AutoDungeonRunService.process_due_auto_runs(limit=10)

        self.assertEqual(processed, 1)
        original_run.refresh_from_db()
        auto_run.refresh_from_db()
        self.assertEqual(original_run.status, DungeonRunStatus.CLAIMED)
        self.assertFalse(original_run.is_success)
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.ACTIVE)
        self.assertNotEqual(auto_run.current_run_id, original_run.id)
        self.assertEqual(auto_run.success_count, 0)
        self.assertEqual(auto_run.failure_count, 1)
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertEqual(AutoDungeonRunClaim.objects.get(dungeon_run=original_run).is_success, False)

    def test_record_claim_rebuilds_summary_accounting_and_preview_limits(self):
        ingredients = [
            IngredientTemplate.objects.create(code=f"summary_{index}", name=f"Summary {index}")
            for index in range(6)
        ]
        first_item = self._user_item("Preview 1")
        second_item = self._user_item("Preview 2")
        third_item = self._user_item("Preview 3")
        fourth_item = self._user_item("Preview 4")
        sword = self._user_item("Durability sword", durability_current=8, durability_max=10, equipped=True)
        ring_template = ItemTemplate.objects.filter(slot="ring", item_type="ring").first()
        ring = UserItem.objects.create(
            owner_user=self.user,
            source_character=self.character,
            equipped_character=self.character,
            template=ring_template,
            name="Durability ring",
            slot="ring",
            item_type="ring",
            rarity="f",
            item_level=1,
            stats={"attack": 1},
            durability_current=6,
            durability_max=10,
        )
        first_run = self._claimed_run(
            is_success=True,
            experience=12,
            money=7,
            ingredients=[
                {"ingredient_id": ingredients[0].id, "quantity": 2},
                {"ingredient_id": ingredients[1].id, "quantity": 3},
                {"ingredient_id": ingredients[2].id, "quantity": 4},
                {"ingredient_id": ingredients[3].id, "quantity": 5},
            ],
        )
        second_run = self._claimed_run(
            is_success=False,
            experience=0,
            money=0,
            ingredients=[
                {"ingredient_id": ingredients[1].id, "quantity": 4},
                {"ingredient_id": ingredients[4].id, "quantity": 6},
                {"ingredient_id": ingredients[5].id, "quantity": 7},
            ],
        )
        first_claim = DungeonRunClaim.objects.create(
            dungeon_run=first_run,
            user=self.user,
            character=self.character,
            experience_claimed=12,
            money_claimed_copper=7,
        )
        second_claim = DungeonRunClaim.objects.create(
            dungeon_run=second_run,
            user=self.user,
            character=self.character,
            experience_claimed=0,
            money_claimed_copper=0,
        )
        auto_run = AutoDungeonRun.objects.create(
            user=self.user,
            character=self.character,
            location=self.location,
            current_run=second_run,
            status=AutoDungeonRunStatus.ACTIVE,
        )

        AutoDungeonRunService._record_claim(
            auto_run,
            ClaimResult(
                run=first_run,
                claim=first_claim,
                items=[first_item, second_item, third_item, fourth_item],
                old_level=1,
                new_level=1,
                durability_total=3,
                durability_changes=[{"item": sword, "removed": 2}, {"item": ring, "removed": 1}],
                hp_loss=9,
                current_hp=91,
                max_hp=120,
                ingredients=first_run.ingredients_reward,
            ),
        )
        sword.durability_current = 5
        sword.save(update_fields=["durability_current", "updated_at"])
        AutoDungeonRunService._record_claim(
            auto_run,
            ClaimResult(
                run=second_run,
                claim=second_claim,
                items=[],
                old_level=1,
                new_level=1,
                durability_total=3,
                durability_changes=[{"item": sword, "removed": 3}],
                hp_loss=11,
                current_hp=80,
                max_hp=120,
                ingredients=second_run.ingredients_reward,
            ),
        )

        auto_run.refresh_from_db()
        self.assertEqual(auto_run.runs_claimed, 2)
        self.assertEqual(auto_run.success_count, 1)
        self.assertEqual(auto_run.failure_count, 1)
        self.assertEqual(auto_run.experience_total, 12)
        self.assertEqual(auto_run.money_total_copper, 7)
        self.assertEqual(auto_run.items_total, 4)
        self.assertEqual(auto_run.ingredients_total, 31)
        self.assertEqual(auto_run.current_hp, 80)
        self.assertEqual(auto_run.max_hp, 120)
        self.assertEqual(auto_run.durability_loss_total, 6)
        self.assertEqual(auto_run.summary["hp_loss_total"], 20)
        expected_durability_changes = [
            {
                "item_id": sword.id,
                "name": sword.name,
                "slot": "weapon",
                "durability": {"current": 5, "max": 10},
                "removed": 5,
            },
            {
                "item_id": ring.id,
                "name": ring.name,
                "slot": "ring",
                "durability": {"current": 6, "max": 10},
                "removed": 1,
            },
        ]
        self.assertEqual(
            sorted(auto_run.durability_changes, key=lambda change: change["item_id"]),
            sorted(expected_durability_changes, key=lambda change: change["item_id"]),
        )
        self.assertEqual(
            [item["name"] for item in auto_run.summary["items_preview"]],
            ["Preview 1", "Preview 2", "Preview 3"],
        )
        self.assertEqual(len(auto_run.summary["ingredients_preview"]), 5)
        self.assertEqual(
            {
                ingredient["ingredient_id"]: ingredient["quantity"]
                for ingredient in auto_run.summary["ingredients_preview"]
            },
            {
                ingredients[0].id: 2,
                ingredients[1].id: 7,
                ingredients[2].id: 4,
                ingredients[3].id: 5,
                ingredients[4].id: 6,
            },
        )
        self.assertEqual(auto_run.summary["durability_changes"], auto_run.durability_changes)

    def test_stopping_claims_current_run_and_stops(self):
        original_run, auto_run = self._due_auto_run()
        AutoDungeonRunService.request_stop(self.user)

        AutoDungeonRunService.process_due_auto_runs(limit=10)

        auto_run.refresh_from_db()
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertTrue(auto_run.summary_unread)
        self.assertEqual(auto_run.stop_reason_code, "player_stopped")
        self.assertEqual(auto_run.current_run_id, original_run.id)
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertTrue(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertTrue(AutoDungeonRunService.is_auto_owned_run(original_run.id))

    def test_start_failure_stops_auto_run_without_treating_failure_as_stop(self):
        _, auto_run = self._due_auto_run()
        self.location.daily_limit = 1
        self.location.save(update_fields=["daily_limit", "updated_at"])

        AutoDungeonRunService.process_due_auto_runs(limit=10)

        auto_run.refresh_from_db()
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertTrue(auto_run.summary_unread)
        self.assertEqual(auto_run.stop_reason_code, "location_limit_reached")
        self.assertEqual(auto_run.runs_claimed, 1)

    def test_mini_game_blocked_for_auto_owned_run(self):
        self.location.has_mini_game = True
        self.location.save(update_fields=["has_mini_game", "updated_at"])
        config = DungeonMiniGameConfig.objects.get(difficulty="6")
        run, _ = AutoDungeonRunService.start_auto_run(self.user, self.location.id)

        with self.assertRaises(DRFValidationError) as ctx:
            DungeonMiniGameService.start_attempt(self.user, run.id, config_id=config.id)

        self.assertIn("Mini-games are not available during Auto run.", str(ctx.exception))

    def test_manual_claim_blocked_for_auto_owned_run(self):
        run, _ = self._due_auto_run()
        DungeonRunService.finalize_due_run(run.id)

        self.assertTrue(AutoDungeonRunService.is_auto_owned_run(run.id))
        response = self.client.post(f"/api/dungeon-runs/{run.id}/claim", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Auto run will claim this reward automatically.", str(response.data))

    def test_system_error_stops_with_summary_without_failing_batch(self):
        _, auto_run = self._due_auto_run()

        with patch(
            "apps.game.services.auto_runs.DungeonRunService.claim_run",
            side_effect=RuntimeError("boom"),
        ):
            processed = AutoDungeonRunService.process_due_auto_runs(limit=10)

        auto_run.refresh_from_db()
        self.assertEqual(processed, 0)
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertEqual(auto_run.stop_reason_code, "system_error")
        self.assertTrue(auto_run.summary_unread)
        self.assertEqual(auto_run.runs_claimed, 0)
        self.assertEqual(
            auto_run.stop_reason_message,
            "Auto run stopped because of a server error. Please try again later.",
        )
        self.assertNotIn("Traceback", str(auto_run.stop_reason_details))
        self.assertNotIn("boom", str(auto_run.stop_reason_details))

    def test_batch_continues_after_one_auto_run_system_error(self):
        failed_run, failed_auto_run = self._due_auto_run()
        other_user = User.objects.create_user("auto-run-worker-other@example.com", "strongpass123")
        GameBalanceService.create_character(
            other_user,
            "OtherWorkerRunner",
            CharacterClass.objects.get(key="warrior"),
        )
        healthy_run, healthy_auto_run = self._due_auto_run_for(other_user, self.location)
        original_claim_run = DungeonRunService.claim_run

        def fail_first_run(user, run_id, *args, **kwargs):
            if run_id == failed_run.id:
                raise RuntimeError("boom")
            return original_claim_run(user, run_id, *args, **kwargs)

        with patch("apps.game.services.auto_runs.DungeonRunService.claim_run", side_effect=fail_first_run):
            processed = AutoDungeonRunService.process_due_auto_runs(limit=10)

        failed_auto_run.refresh_from_db()
        healthy_auto_run.refresh_from_db()
        self.assertEqual(processed, 1)
        self.assertEqual(failed_auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertEqual(failed_auto_run.stop_reason_code, "system_error")
        self.assertTrue(failed_auto_run.summary_unread)
        self.assertEqual(healthy_auto_run.status, AutoDungeonRunStatus.ACTIVE)
        self.assertNotEqual(healthy_auto_run.current_run_id, healthy_run.id)
        self.assertEqual(healthy_auto_run.runs_claimed, 1)

    def test_next_run_creation_rolls_back_when_attach_fails(self):
        original_run, auto_run = self._due_auto_run()
        original_save = AutoDungeonRun.save

        def fail_when_attaching_current_run(instance, *args, **kwargs):
            update_fields = set(kwargs.get("update_fields") or [])
            if "current_run" in update_fields:
                raise RuntimeError("attach failed")
            return original_save(instance, *args, **kwargs)

        with patch.object(AutoDungeonRun, "save", fail_when_attaching_current_run):
            with self.assertRaises(RuntimeError):
                AutoDungeonRunService.process_single_auto_run(auto_run.id)

        auto_run.refresh_from_db()
        original_run.refresh_from_db()
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertEqual(auto_run.stop_reason_code, "system_error")
        self.assertEqual(auto_run.current_run_id, original_run.id)
        self.assertEqual(auto_run.runs_claimed, 1)
        self.assertEqual(original_run.status, DungeonRunStatus.CLAIMED)
        self.assertTrue(DungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertTrue(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertEqual(
            DungeonRun.objects.filter(
                character=self.character,
                status=DungeonRunStatus.IN_PROGRESS,
            ).count(),
            0,
        )

    def test_claim_and_accounting_failure_keeps_current_run_claimed(self):
        original_run, auto_run = self._due_auto_run()
        equipped_item = self._user_item(
            "Atomic durability sword",
            durability_current=10,
            durability_max=10,
            equipped=True,
        )

        with patch(
            "apps.game.services.auto_runs.AutoDungeonRunService._record_claim",
            side_effect=RuntimeError("accounting failed"),
        ):
            with self.assertRaises(RuntimeError):
                AutoDungeonRunService.process_single_auto_run(auto_run.id)

        auto_run.refresh_from_db()
        original_run.refresh_from_db()
        equipped_item.refresh_from_db()
        self.assertEqual(auto_run.status, AutoDungeonRunStatus.STOPPED)
        self.assertEqual(auto_run.stop_reason_code, "system_error")
        self.assertEqual(auto_run.runs_claimed, 0)
        self.assertEqual(original_run.status, DungeonRunStatus.CLAIMED)
        self.assertTrue(DungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertFalse(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertLess(equipped_item.durability_current, 10)

        self.assertTrue(AutoDungeonRunService.is_auto_owned_run(original_run.id))
        response = self.client.post(f"/api/dungeon-runs/{original_run.id}/claim", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Auto run will claim this reward automatically.", str(response.data))
        self.location.has_mini_game = True
        self.location.save(update_fields=["has_mini_game", "updated_at"])
        config = DungeonMiniGameConfig.objects.get(difficulty="6")
        with self.assertRaises(DRFValidationError) as ctx:
            DungeonMiniGameService.start_attempt(self.user, original_run.id, config_id=config.id)

        self.assertIn("Mini-games are not available during Auto run.", str(ctx.exception))
        original_run.refresh_from_db()
        self.assertEqual(original_run.status, DungeonRunStatus.CLAIMED)
        self.assertTrue(DungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
        self.assertFalse(AutoDungeonRunClaim.objects.filter(dungeon_run=original_run).exists())
