from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from apps.game.models import MoneyTransaction, User
from apps.game.services import MoneyService


class MoneyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("money@example.com", "strongpass123")

    def test_grant_increases_balance_and_creates_transaction(self):
        tx = MoneyService.grant(
            user=self.user, amount=100, reason=MoneyTransaction.Reason.DUNGEON_REWARD
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 100)
        self.assertEqual(tx.amount, 100)
        self.assertEqual(tx.balance_after, 100)

    def test_charge_decreases_balance_and_creates_transaction(self):
        MoneyService.grant(
            user=self.user, amount=100, reason=MoneyTransaction.Reason.DUNGEON_REWARD
        )

        tx = MoneyService.charge(
            user=self.user, amount=30, reason=MoneyTransaction.Reason.SHOP_PURCHASE
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 70)
        self.assertEqual(tx.amount, -30)
        self.assertEqual(tx.balance_after, 70)

    def test_charge_cannot_go_below_zero(self):
        MoneyService.grant(
            user=self.user, amount=10, reason=MoneyTransaction.Reason.DUNGEON_REWARD
        )
        with self.assertRaises(DRFValidationError):
            MoneyService.charge(
                user=self.user, amount=50, reason=MoneyTransaction.Reason.SHOP_PURCHASE
            )
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 10)

    def test_charge_uses_custom_insufficient_message(self):
        with self.assertRaises(DRFValidationError) as ctx:
            MoneyService.charge(
                user=self.user,
                amount=5,
                reason=MoneyTransaction.Reason.REPAIR,
                insufficient_message="not_enough_money_repair",
                locale="en",
            )
        self.assertIn("repair", str(ctx.exception).lower())

    def test_non_positive_amount_is_rejected(self):
        with self.assertRaises(DRFValidationError):
            MoneyService.grant(
                user=self.user, amount=0, reason=MoneyTransaction.Reason.DUNGEON_REWARD
            )
        with self.assertRaises(DRFValidationError):
            MoneyService.charge(
                user=self.user, amount=-5, reason=MoneyTransaction.Reason.SHOP_PURCHASE
            )

    def test_get_amount_reads_from_db(self):
        MoneyService.grant(
            user=self.user, amount=42, reason=MoneyTransaction.Reason.DUNGEON_REWARD
        )
        self.assertEqual(MoneyService.get_amount(self.user), 42)

    def test_idempotency_key_prevents_duplicate(self):
        first = MoneyService.grant(
            user=self.user,
            amount=100,
            reason=MoneyTransaction.Reason.EXCHANGE_FROM_PREMIUM,
            idempotency_key="exchange-1",
        )
        second = MoneyService.grant(
            user=self.user,
            amount=100,
            reason=MoneyTransaction.Reason.EXCHANGE_FROM_PREMIUM,
            idempotency_key="exchange-1",
        )

        self.assertEqual(first.id, second.id)
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 100)
        self.assertEqual(MoneyTransaction.objects.filter(user=self.user).count(), 1)
