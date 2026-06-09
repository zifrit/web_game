from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from apps.billing.models import (
    CurrencyExchangeOffer,
    CurrencyExchangeTransaction,
    PremiumCurrencyTransaction,
    UserPremiumBalance,
)
from apps.billing.services import CurrencyExchangeService, PremiumCurrencyService
from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, User
from apps.game.services import GameBalanceService


class CurrencyExchangeServiceTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("exchange@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user, "Trader", CharacterClass.objects.get(key="warrior")
        )
        self.offer = CurrencyExchangeOffer.objects.create(
            premium_cost=50, money_copper_reward=60_000
        )

    def test_exchange_subtracts_premium_and_adds_money(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        CurrencyExchangeService.exchange(user=self.user, offer_id=self.offer.id)

        self.assertEqual(UserPremiumBalance.objects.get(user=self.user).amount, 50)
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 60_000)

    def test_exchange_creates_both_transactions(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        exchange_tx = CurrencyExchangeService.exchange(user=self.user, offer_id=self.offer.id)

        self.assertIsInstance(exchange_tx, CurrencyExchangeTransaction)
        self.assertEqual(exchange_tx.premium_spent, 50)
        self.assertEqual(exchange_tx.money_copper_received, 60_000)
        self.assertEqual(
            exchange_tx.premium_transaction.reason,
            PremiumCurrencyTransaction.Reason.EXCHANGE_TO_MONEY,
        )
        self.assertEqual(exchange_tx.premium_transaction.amount, -50)

    def test_failed_exchange_does_not_mutate_balances(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=10, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        with self.assertRaises(DRFValidationError):
            CurrencyExchangeService.exchange(user=self.user, offer_id=self.offer.id)

        self.assertEqual(UserPremiumBalance.objects.get(user=self.user).amount, 10)
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 0)
        self.assertFalse(CurrencyExchangeTransaction.objects.filter(user=self.user).exists())
