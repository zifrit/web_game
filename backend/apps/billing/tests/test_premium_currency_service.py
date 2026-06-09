from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from apps.billing.models import PremiumCurrencyTransaction, UserPremiumBalance
from apps.billing.services import PremiumCurrencyService
from apps.game.models import User


class PremiumCurrencyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("premium@example.com", "strongpass123")

    def test_add_increases_balance_and_creates_transaction(self):
        tx = PremiumCurrencyService.grant(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        balance = UserPremiumBalance.objects.get(user=self.user)
        self.assertEqual(balance.amount, 100)
        self.assertEqual(tx.amount, 100)
        self.assertEqual(tx.balance_after, 100)

    def test_spend_decreases_balance_and_creates_transaction(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        tx = PremiumCurrencyService.charge(
            user=self.user, amount=30, reason=PremiumCurrencyTransaction.Reason.SHOP_PURCHASE
        )

        balance = UserPremiumBalance.objects.get(user=self.user)
        self.assertEqual(balance.amount, 70)
        self.assertEqual(tx.amount, -30)
        self.assertEqual(tx.balance_after, 70)

    def test_spend_cannot_go_below_zero(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=10, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        with self.assertRaises(DRFValidationError):
            PremiumCurrencyService.charge(
                user=self.user, amount=50, reason=PremiumCurrencyTransaction.Reason.SHOP_PURCHASE
            )
        self.assertEqual(UserPremiumBalance.objects.get(user=self.user).amount, 10)

    def test_non_positive_amount_is_rejected(self):
        with self.assertRaises(DRFValidationError):
            PremiumCurrencyService.grant(
                user=self.user, amount=0, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
            )
        with self.assertRaises(DRFValidationError):
            PremiumCurrencyService.charge(
                user=self.user, amount=-5, reason=PremiumCurrencyTransaction.Reason.SHOP_PURCHASE
            )

    def test_idempotency_key_prevents_duplicate(self):
        first = PremiumCurrencyService.grant(
            user=self.user,
            amount=100,
            reason=PremiumCurrencyTransaction.Reason.PAYMENT,
            idempotency_key="order-1",
        )
        second = PremiumCurrencyService.grant(
            user=self.user,
            amount=100,
            reason=PremiumCurrencyTransaction.Reason.PAYMENT,
            idempotency_key="order-1",
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(UserPremiumBalance.objects.get(user=self.user).amount, 100)
        self.assertEqual(PremiumCurrencyTransaction.objects.filter(user=self.user).count(), 1)
