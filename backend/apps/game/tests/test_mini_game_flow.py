from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import serializers

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import (
    CharacterClass,
    DungeonLocation,
    DungeonMiniGameAttempt,
    DungeonMiniGameConfig,
    User,
)
from apps.game.services import DungeonMiniGameService, DungeonRunService, GameBalanceService
from apps.game.services.mini_game_store import MiniGameStore


class MiniGameFlowTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("flow@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user, "Flow", CharacterClass.objects.get(key="warrior")
        )
        self.location = DungeonLocation.objects.get(name="Старый лес")
        self.location.has_mini_game = True
        self.location.duration_seconds = 120
        self.location.save(update_fields=["has_mini_game", "duration_seconds", "updated_at"])
        self.config = DungeonMiniGameConfig.objects.get(difficulty="6")

    def _start(self):
        run = DungeonRunService.start_run(self.user, self.location.id)
        run.ends_at = timezone.now() + timezone.timedelta(seconds=100)
        run.save(update_fields=["ends_at", "updated_at"])
        attempt = DungeonMiniGameService.start_attempt(self.user, run.id, config_id=self.config.id)
        return run, attempt

    def test_start_requires_valid_config(self):
        run = DungeonRunService.start_run(self.user, self.location.id)
        with self.assertRaises(serializers.ValidationError):
            DungeonMiniGameService.start_attempt(self.user, run.id, config_id=999999)

    def test_start_blocked_without_location_flag(self):
        self.location.has_mini_game = False
        self.location.save(update_fields=["has_mini_game", "updated_at"])
        run = DungeonRunService.start_run(self.user, self.location.id)
        with self.assertRaises(serializers.ValidationError):
            DungeonMiniGameService.start_attempt(self.user, run.id, config_id=self.config.id)

    def test_repeated_move_is_idempotent(self):
        run, attempt = self._start()
        # Берём заведомо не-парные карты, чтобы ход не завершил игру.
        by_pair = {}
        for card in attempt.board:
            by_pair.setdefault(card["pair_key"], []).append(card["id"])
        keys = list(by_pair)
        first_id = by_pair[keys[0]][0]
        second_id = by_pair[keys[1]][0]

        DungeonMiniGameService.reveal_card(self.user, attempt.id, card_id=first_id)
        first = DungeonMiniGameService.make_move(
            self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
        )
        repeat = DungeonMiniGameService.make_move(
            self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
        )
        self.assertEqual(first, repeat)
        self.assertEqual(first["attempt"]["moves_count"], 1)

    def test_lost_redis_key_finishes_as_system_error_win(self):
        run, attempt = self._start()
        before = run.ends_at
        MiniGameStore.clear(run.id)

        first_id, second_id = attempt.board[0]["id"], attempt.board[1]["id"]
        result = DungeonMiniGameService.make_move(
            self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
        )
        attempt.refresh_from_db()
        run.refresh_from_db()

        self.assertTrue(result["finished"])
        self.assertEqual(attempt.status, DungeonMiniGameAttempt.SUCCESS)
        self.assertTrue(attempt.system_error)
        # Полное ускорение: percent=10 от 120 = 12 секунд.
        self.assertEqual(attempt.duration_reduction_seconds, 12)
        self.assertEqual(run.ends_at, before - timezone.timedelta(seconds=12))

    def test_busy_lock_rejects_concurrent_move(self):
        run, attempt = self._start()
        first_id, second_id = attempt.board[0]["id"], attempt.board[1]["id"]
        with MiniGameStore.lock(run.id):
            with self.assertRaises(serializers.ValidationError):
                DungeonMiniGameService.make_move(
                    self.user, attempt.id, first_card_id=first_id, second_card_id=second_id
                )

    def test_finalize_due_run_fails_active_attempt(self):
        run, attempt = self._start()
        run.ends_at = timezone.now() - timezone.timedelta(seconds=1)
        run.save(update_fields=["ends_at", "updated_at"])
        DungeonRunService.finalize_due_run(run)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, DungeonMiniGameAttempt.FAILED)
        self.assertIsNone(MiniGameStore.load(run.id))
