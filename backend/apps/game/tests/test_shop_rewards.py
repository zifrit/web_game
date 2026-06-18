from django.test import TestCase

from apps.game.models import ShopOffer
from apps.game.services.shop_rewards import REWARD_KINDS, reward_descriptor


class RewardDescriptorTests(TestCase):
    def test_every_reward_kind_has_a_descriptor(self):
        for kind in ShopOffer.RewardKind.values:
            self.assertIsNotNone(reward_descriptor(kind), f"missing descriptor for {kind}")

    def test_unknown_kind_returns_none(self):
        self.assertIsNone(reward_descriptor("armor_set"))

    def test_stackable_descriptors_declare_storage(self):
        for descriptor in REWARD_KINDS.values():
            if descriptor.stackable:
                self.assertIsNotNone(descriptor.storage)

    def test_template_id_attr_derives_from_template_attr(self):
        self.assertEqual(
            reward_descriptor(ShopOffer.RewardKind.INGREDIENT).template_id_attr,
            "ingredient_template_id",
        )
