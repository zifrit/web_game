from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from apps.billing.models import (
    PremiumCurrencyTransaction,
    PremiumTopUp,
    PremiumTopUpEvent,
    PremiumTopUpOffer,
    UserPremiumBalance,
)
from apps.billing.services import PremiumTopUpService
from apps.game.models import User


class PremiumTopUpServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("topup@example.com", "strongpass123")
        self.offer = PremiumTopUpOffer.objects.create(
            premium_amount=120,
            price_amount_minor=19900,
            sort_order=1,
        )

    def test_create_pending_top_up_snapshots_offer(self):
        top_up = PremiumTopUpService.create_pending(
            user=self.user,
            offer_id=self.offer.id,
            idempotency_key="click-1",
        )

        self.assertEqual(top_up.status, PremiumTopUp.Status.PENDING)
        self.assertEqual(top_up.premium_amount, 120)
        self.assertEqual(top_up.price_amount_minor, 19900)
        self.assertEqual(top_up.price_currency, "RUB")
        self.assertIsNone(top_up.checkout_url)
        self.assertEqual(top_up.idempotency_key, "click-1")

    def test_create_pending_is_idempotent_for_user_and_key(self):
        first = PremiumTopUpService.create_pending(
            user=self.user,
            offer_id=self.offer.id,
            idempotency_key="click-1",
        )
        second = PremiumTopUpService.create_pending(
            user=self.user,
            offer_id=self.offer.id,
            idempotency_key="click-1",
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(PremiumTopUp.objects.filter(user=self.user).count(), 1)

    def test_create_pending_rejects_inactive_offer(self):
        self.offer.is_active = False
        self.offer.save(update_fields=["is_active", "updated_at"])

        with self.assertRaises(DRFValidationError):
            PremiumTopUpService.create_pending(user=self.user, offer_id=self.offer.id)

    def test_mark_succeeded_grants_premium_once(self):
        top_up = PremiumTopUpService.create_pending(
            user=self.user,
            offer_id=self.offer.id,
            idempotency_key="click-1",
        )

        first = PremiumTopUpService.mark_succeeded(
            top_up_id=top_up.id,
            provider="manual",
            provider_payment_id="payment-1",
        )
        second = PremiumTopUpService.mark_succeeded(
            top_up_id=top_up.id,
            provider="manual",
            provider_payment_id="payment-1",
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.status, PremiumTopUp.Status.SUCCEEDED)
        self.assertEqual(first.premium_transaction.reason, PremiumCurrencyTransaction.Reason.PAYMENT)
        self.assertEqual(first.premium_transaction.amount, 120)
        self.assertEqual(first.premium_transaction.balance_after, 120)
        self.assertEqual(UserPremiumBalance.objects.get(user=self.user).amount, 120)
        self.assertEqual(PremiumCurrencyTransaction.objects.filter(user=self.user).count(), 1)


class PremiumTopUpModelValidationTests(TestCase):
    def test_offer_requires_positive_amounts(self):
        offer = PremiumTopUpOffer(premium_amount=0, price_amount_minor=0)

        with self.assertRaises(DjangoValidationError):
            offer.full_clean()

    def test_provider_event_id_is_unique_per_provider(self):
        PremiumTopUpEvent.objects.create(
            provider="manual",
            provider_event_id="event-1",
            event_type="payment.succeeded",
            payload={"id": "event-1"},
        )

        duplicate = PremiumTopUpEvent(
            provider="manual",
            provider_event_id="event-1",
            event_type="payment.succeeded",
            payload={"id": "event-1"},
        )

        with self.assertRaises(DjangoValidationError):
            duplicate.full_clean()
