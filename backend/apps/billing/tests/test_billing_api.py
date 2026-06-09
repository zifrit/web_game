from django.test import TestCase
from rest_framework.test import APIClient

from apps.billing.models import CurrencyExchangeOffer, PremiumCurrencyTransaction
from apps.billing.services import PremiumCurrencyService
from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, User
from apps.game.services import GameBalanceService


class BillingApiTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("billingapi@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(
            self.user, "Trader", CharacterClass.objects.get(key="warrior")
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.offer = CurrencyExchangeOffer.objects.create(premium_cost=50, money_copper_reward=60_000)
        self.inactive_offer = CurrencyExchangeOffer.objects.create(
            premium_cost=999, money_copper_reward=10_000, is_active=False
        )

    def test_exchange_offers_returns_active_only(self):
        response = self.client.get("/api/billing/exchange-offers")
        self.assertEqual(response.status_code, 200)
        ids = [offer["id"] for offer in response.data]
        self.assertIn(self.offer.id, ids)
        self.assertNotIn(self.inactive_offer.id, ids)

    def test_exchange_offer_detail(self):
        response = self.client.get(f"/api/billing/exchange-offers/{self.offer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["premium_cost"], 50)
        self.assertTrue(response.data["is_active"])

    def test_exchange_performs_and_returns_balances(self):
        PremiumCurrencyService.add(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        response = self.client.post(
            f"/api/billing/exchange-offers/{self.offer.id}/exchange", {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["transaction"]["premium_spent"], 50)
        self.assertEqual(response.data["balances"]["premium_currency"], 50)
        self.assertEqual(response.data["balances"]["money_copper"], 60_000)

    def test_exchange_rejects_insufficient_premium(self):
        PremiumCurrencyService.add(
            user=self.user, amount=10, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        response = self.client.post(
            f"/api/billing/exchange-offers/{self.offer.id}/exchange", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_exchange_transactions_user_scoped(self):
        PremiumCurrencyService.add(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        self.client.post(f"/api/billing/exchange-offers/{self.offer.id}/exchange", {}, format="json")

        response = self.client.get("/api/billing/exchange-transactions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

        other = User.objects.create_user("other2@example.com", "strongpass123")
        other_client = APIClient()
        other_client.force_authenticate(user=other)
        other_response = other_client.get("/api/billing/exchange-transactions")
        self.assertEqual(other_response.data["results"], [])

    def test_premium_transactions_user_scoped(self):
        PremiumCurrencyService.add(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        response = self.client.get("/api/billing/premium-transactions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["amount"], 100)

    def test_unauthenticated_cannot_access(self):
        anon = APIClient()
        response = anon.get("/api/billing/exchange-offers")
        self.assertIn(response.status_code, (401, 403))
