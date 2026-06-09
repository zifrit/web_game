from django.test import TestCase

from apps.billing.models import PremiumCurrencyTransaction
from apps.billing.services import PremiumCurrencyService
from apps.game.models import MoneyTransaction, User
from apps.game.services import MONEY_COPPER, PREMIUM_CURRENCY, all_balances, get_wallet


class WalletRegistryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("wallet@example.com", "strongpass123")

    def test_get_wallet_returns_adapter_for_each_currency(self):
        self.assertEqual(get_wallet(MONEY_COPPER).key, MONEY_COPPER)
        self.assertEqual(get_wallet(PREMIUM_CURRENCY).key, PREMIUM_CURRENCY)

    def test_unknown_currency_raises(self):
        with self.assertRaises(ValueError):
            get_wallet("doubloons")

    def test_copper_wallet_grant_charge_balance_delegate_to_moneyservice(self):
        wallet = get_wallet(MONEY_COPPER)
        wallet.grant(self.user, amount=100, reason=MoneyTransaction.Reason.DUNGEON_REWARD)
        wallet.charge(self.user, amount=40, reason=MoneyTransaction.Reason.SHOP_PURCHASE)

        self.assertEqual(wallet.get_balance(self.user), 60)
        self.user.refresh_from_db()
        self.assertEqual(self.user.money_copper, 60)

    def test_premium_wallet_delegates_to_premium_service(self):
        wallet = get_wallet(PREMIUM_CURRENCY)
        tx = wallet.grant(
            self.user, amount=50, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        self.assertEqual(tx.balance_after, 50)
        self.assertEqual(wallet.get_balance(self.user), 50)
        self.assertEqual(PremiumCurrencyService.get_amount(self.user), 50)

    def test_all_balances_returns_every_currency(self):
        get_wallet(MONEY_COPPER).grant(
            self.user, amount=7, reason=MoneyTransaction.Reason.DUNGEON_REWARD
        )
        get_wallet(PREMIUM_CURRENCY).grant(
            self.user, amount=3, reason=PremiumCurrencyTransaction.Reason.ADMIN_GRANT
        )

        self.assertEqual(
            all_balances(self.user),
            {MONEY_COPPER: 7, PREMIUM_CURRENCY: 3},
        )
