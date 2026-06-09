from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from apps.billing.models import PremiumCurrencyTransaction, UserPremiumBalance
from apps.billing.services import PremiumCurrencyService
from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import (
    CharacterClass,
    HeroIngredientStorage,
    HeroPotionStorage,
    IngredientTemplate,
    ItemTemplate,
    PotionTemplate,
    ShopOffer,
    ShopOfferIngredient,
    ShopOfferItem,
    ShopOfferPotion,
    ShopPurchase,
    User,
    UserItem,
)
from apps.game.services import GameBalanceService, ShopService


class ShopServiceTestBase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.user = User.objects.create_user("shop@example.com", "strongpass123")
        self.user.money_copper = 1_000_000
        self.user.save(update_fields=["money_copper"])
        self.character = GameBalanceService.create_character(
            self.user, "Shopper", CharacterClass.objects.get(key="warrior")
        )
        self.ingredients = list(IngredientTemplate.objects.all()[:2])
        self.potions = list(PotionTemplate.objects.all()[:2])
        self.sword = ItemTemplate.objects.filter(slot="weapon", item_type="sword").first()

    def _offer(self, **kwargs):
        defaults = dict(
            reward_kind=ShopOffer.RewardKind.INGREDIENT,
            delivery_mode=ShopOffer.DeliveryMode.SINGLE,
            name_i18n={"en": "Test offer"},
            quantity=1,
            price_money_copper=100,
        )
        defaults.update(kwargs)
        return ShopOffer.objects.create(**defaults)


class ShopModelValidationTests(ShopServiceTestBase):
    def test_offer_requires_at_least_one_price(self):
        offer = ShopOffer(
            reward_kind=ShopOffer.RewardKind.INGREDIENT,
            delivery_mode=ShopOffer.DeliveryMode.SINGLE,
            name_i18n={"en": "No price"},
            quantity=1,
            price_money_copper=None,
            price_premium_currency=None,
        )
        with self.assertRaises(ValidationError):
            offer.clean()

    def test_single_offer_requires_quantity_one(self):
        offer = ShopOffer(
            reward_kind=ShopOffer.RewardKind.INGREDIENT,
            delivery_mode=ShopOffer.DeliveryMode.SINGLE,
            name_i18n={"en": "Bad qty"},
            quantity=3,
            price_money_copper=100,
        )
        with self.assertRaises(ValidationError):
            offer.clean()

    def test_chance_must_be_positive(self):
        offer = self._offer()
        entry = ShopOfferIngredient(offer=offer, ingredient_template=self.ingredients[0], chance=0)
        with self.assertRaises(ValidationError):
            entry.clean()


class ShopIngredientPurchaseTests(ShopServiceTestBase):
    def test_single_ingredient_with_money(self):
        offer = self._offer(quantity=1, price_money_copper=100)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)

        result = ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=2, payment_currency="money_copper"
        )

        storage = HeroIngredientStorage.objects.get(character=self.character, ingredient=self.ingredients[0])
        self.assertEqual(storage.count, 2)  # quantity(1) * purchase_count(2)
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 1_000_000 - 200)
        self.assertEqual(result["balances"]["money_copper"], self.user.money_copper)
        self.assertFalse(PremiumCurrencyTransaction.objects.filter(user=self.user).exists())

    def test_single_requires_exactly_one_entry(self):
        offer = self._offer(quantity=1)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[1], chance=1)
        with self.assertRaises(DRFValidationError):
            ShopService.buy_offer(
                user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="money_copper"
            )

    def test_chest_ingredient_grouped_storage_update(self):
        offer = self._offer(delivery_mode=ShopOffer.DeliveryMode.CHEST, quantity=3, price_money_copper=50)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[1], chance=1)

        ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=2, payment_currency="money_copper"
        )

        total = sum(
            HeroIngredientStorage.objects.filter(
                character=self.character, ingredient__in=self.ingredients
            ).values_list("count", flat=True)
        )
        self.assertEqual(total, 6)  # quantity(3) * purchase_count(2)

    def test_chest_requires_at_least_one_entry(self):
        offer = self._offer(delivery_mode=ShopOffer.DeliveryMode.CHEST, quantity=3)
        with self.assertRaises(DRFValidationError):
            ShopService.buy_offer(
                user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="money_copper"
            )


class ShopPotionPurchaseTests(ShopServiceTestBase):
    def test_single_potion(self):
        offer = self._offer(reward_kind=ShopOffer.RewardKind.POTION, quantity=1)
        ShopOfferPotion.objects.create(offer=offer, potion_template=self.potions[0], chance=1)

        ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=3, payment_currency="money_copper"
        )

        storage = HeroPotionStorage.objects.get(character=self.character, potion=self.potions[0])
        self.assertEqual(storage.count, 3)

    def test_chest_potion(self):
        offer = self._offer(
            reward_kind=ShopOffer.RewardKind.POTION,
            delivery_mode=ShopOffer.DeliveryMode.CHEST,
            quantity=4,
        )
        ShopOfferPotion.objects.create(offer=offer, potion_template=self.potions[0], chance=1)
        ShopOfferPotion.objects.create(offer=offer, potion_template=self.potions[1], chance=1)

        ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="money_copper"
        )

        total = sum(
            HeroPotionStorage.objects.filter(
                character=self.character, potion__in=self.potions
            ).values_list("count", flat=True)
        )
        self.assertEqual(total, 4)


class ShopItemPurchaseTests(ShopServiceTestBase):
    def test_single_item_creates_unique_rows(self):
        offer = self._offer(reward_kind=ShopOffer.RewardKind.ITEM, quantity=1)
        ShopOfferItem.objects.create(offer=offer, item_template=self.sword, chance=1)

        result = ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=2, payment_currency="money_copper"
        )

        items = UserItem.objects.filter(owner_user=self.user)
        self.assertEqual(items.count(), 2)
        payload_items = result["purchase"].result_payload["items"]
        self.assertEqual(len(payload_items), 2)
        self.assertEqual(len({entry["user_item_id"] for entry in payload_items}), 2)

    def test_chest_item_creates_quantity_times_purchase_count(self):
        offer = self._offer(
            reward_kind=ShopOffer.RewardKind.ITEM,
            delivery_mode=ShopOffer.DeliveryMode.CHEST,
            quantity=3,
        )
        ShopOfferItem.objects.create(offer=offer, item_template=self.sword, chance=1)

        ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=2, payment_currency="money_copper"
        )

        self.assertEqual(UserItem.objects.filter(owner_user=self.user).count(), 6)


class ShopPaymentTests(ShopServiceTestBase):
    def test_cannot_buy_with_unavailable_currency(self):
        offer = self._offer(price_money_copper=100, price_premium_currency=None)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)
        with self.assertRaises(DRFValidationError):
            ShopService.buy_offer(
                user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="premium_currency"
            )

    def test_cannot_buy_without_enough_money(self):
        self.user.money_copper = 50
        self.user.save(update_fields=["money_copper"])
        offer = self._offer(price_money_copper=100)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)
        with self.assertRaises(DRFValidationError):
            ShopService.buy_offer(
                user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="money_copper"
            )

    def test_buying_with_premium_creates_premium_transaction(self):
        PremiumCurrencyService.add(
            user=self.user, amount=100, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )
        offer = self._offer(price_money_copper=None, price_premium_currency=10)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)

        result = ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=2, payment_currency="premium_currency"
        )

        spend_tx = PremiumCurrencyTransaction.objects.filter(
            user=self.user, reason=PremiumCurrencyTransaction.Reason.SHOP_PURCHASE
        )
        self.assertTrue(spend_tx.exists())
        self.assertEqual(spend_tx.first().amount, -20)  # unit 10 * purchase_count 2
        self.assertEqual(result["balances"]["premium_currency"], 80)

    def test_buying_with_money_does_not_create_premium_transaction(self):
        offer = self._offer(price_money_copper=100, price_premium_currency=10)
        ShopOfferIngredient.objects.create(offer=offer, ingredient_template=self.ingredients[0], chance=1)

        ShopService.buy_offer(
            user=self.user, offer_id=offer.id, purchase_count=1, payment_currency="money_copper"
        )

        self.assertFalse(
            PremiumCurrencyTransaction.objects.filter(
                user=self.user, reason=PremiumCurrencyTransaction.Reason.SHOP_PURCHASE
            ).exists()
        )
