from django.test import TestCase
from rest_framework.test import APIClient

from apps.billing.models import PremiumCurrencyTransaction
from apps.billing.services import PremiumCurrencyService
from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import (
    CharacterClass,
    IngredientTemplate,
    ItemTemplate,
    ShopOffer,
    ShopOfferIngredient,
    ShopOfferItem,
    ShopPurchase,
    User,
)
from apps.game.services import GameBalanceService


class ShopApiTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("shopapi@example.com", "strongpass123")
        self.user.money_copper = 1_000_000
        self.user.save(update_fields=["money_copper"])
        self.character = GameBalanceService.create_character(
            self.user, "ApiShopper", CharacterClass.objects.get(key="warrior")
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.ingredient = IngredientTemplate.objects.first()
        self.sword = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()

    def _ingredient_offer(self, **kwargs):
        defaults = dict(
            reward_kind=ShopOffer.RewardKind.INGREDIENT,
            delivery_mode=ShopOffer.DeliveryMode.SINGLE,
            name_i18n={"en": "Herb offer", "ru": "Трава"},
            description_i18n={"en": "A herb"},
            quantity=1,
            price_money_copper=100,
        )
        defaults.update(kwargs)
        offer = ShopOffer.objects.create(**defaults)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredient, chance=1)
        return offer

    def test_unauthenticated_cannot_access(self):
        anon = APIClient()
        response = anon.get("/api/shop/offers")
        self.assertIn(response.status_code, (401, 403))

    def test_offers_returns_active_only(self):
        active = self._ingredient_offer()
        inactive = self._ingredient_offer(is_active=False, name_i18n={"en": "Inactive"})

        response = self.client.get("/api/shop/offers")
        self.assertEqual(response.status_code, 200)
        ids = [offer["id"] for offer in response.data]
        self.assertIn(active.id, ids)
        self.assertNotIn(inactive.id, ids)

    def test_list_excludes_possible_rewards(self):
        self._ingredient_offer()
        response = self.client.get("/api/shop/offers")
        self.assertNotIn("possible_rewards", response.data[0])

    def test_detail_includes_possible_rewards_with_chances(self):
        offer = ShopOffer.objects.create(
            reward_kind=ShopOffer.RewardKind.ITEM,
            delivery_mode=ShopOffer.DeliveryMode.CHEST,
            name_i18n={"en": "Chest"},
            quantity=2,
            price_money_copper=5000,
        )
        ShopOfferItem.objects.create(offer=offer, item_template=self.sword, chance=3)

        response = self.client.get(f"/api/shop/offers/{offer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("possible_rewards", response.data)
        reward = response.data["possible_rewards"][0]
        self.assertIn("chance", reward)
        self.assertIn("chance_percent", reward)
        self.assertEqual(reward["chance_percent"], 100.0)

    def test_buy_creates_purchase_and_returns_balances(self):
        offer = self._ingredient_offer()
        response = self.client.post(
            f"/api/shop/offers/{offer.id}/buy",
            {"purchase_count": 2, "payment_currency": "money_copper"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("balances", response.data)
        self.assertEqual(response.data["balances"]["money_copper"], 1_000_000 - 200)
        self.assertTrue(ShopPurchase.objects.filter(user=self.user, offer=offer).exists())

    def test_buy_ignores_client_side_price(self):
        offer = self._ingredient_offer(price_money_copper=100)
        response = self.client.post(
            f"/api/shop/offers/{offer.id}/buy",
            {"purchase_count": 1, "payment_currency": "money_copper", "unit_price": 1, "total_price": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        # Backend charges 100, not the client-sent 1.
        self.assertEqual(response.data["balances"]["money_copper"], 1_000_000 - 100)

    def test_purchases_are_user_scoped(self):
        offer = self._ingredient_offer()
        self.client.post(
            f"/api/shop/offers/{offer.id}/buy",
            {"purchase_count": 1, "payment_currency": "money_copper"},
            format="json",
        )

        other = User.objects.create_user("other@example.com", "strongpass123")
        other.money_copper = 1000
        other.save(update_fields=["money_copper"])
        GameBalanceService.create_character(other, "Other", CharacterClass.objects.get(key="warrior"))
        other_client = APIClient()
        other_client.force_authenticate(user=other)

        response = other_client.get("/api/shop/purchases")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])


class AuthMePremiumTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("me@example.com", "strongpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_me_includes_premium_currency_zero_without_balance(self):
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["premium_currency"], 0)

    def test_me_reflects_premium_balance(self):
        PremiumCurrencyService.grant(
            user=self.user, amount=40, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.data["premium_currency"], 40)
