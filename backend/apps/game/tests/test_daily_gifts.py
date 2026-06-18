from django.test import TestCase

from apps.game.management.commands.seed_game import Command as SeedCommand
from apps.game.models import CharacterClass, HeroPotionStorage, PotionTemplate, User
from apps.game.services import GameBalanceService
from apps.game.tasks.daily_gifts import DAILY_POTION_GIFT, SMALL_POTION_CODE, _run


class DailyGiftTests(TestCase):
    def setUp(self):
        SeedCommand().handle()
        warrior = CharacterClass.objects.get(key="warrior")
        self.user = User.objects.create_user("daily-gift@example.com", "strongpass123")
        self.character = GameBalanceService.create_character(self.user, "Gifted", warrior)
        self.other_user = User.objects.create_user("daily-gift-other@example.com", "strongpass123")
        self.other = GameBalanceService.create_character(self.other_user, "Other", warrior)
        self.potion = PotionTemplate.objects.get(code=SMALL_POTION_CODE)

    def test_daily_gift_deposits_potions_and_heals_characters(self):
        HeroPotionStorage.objects.create(
            character=self.character,
            potion=self.potion,
            count=1,
        )
        self.character.current_hp = 1
        self.character.save(update_fields=["current_hp", "updated_at"])

        potion_count, heal_count = _run()

        self.assertEqual(potion_count, 2)
        self.assertEqual(heal_count, 1)
        self.assertEqual(
            HeroPotionStorage.objects.get(character=self.character, potion=self.potion).count,
            1 + DAILY_POTION_GIFT,
        )
        self.assertEqual(
            HeroPotionStorage.objects.get(character=self.other, potion=self.potion).count,
            DAILY_POTION_GIFT,
        )
        self.character.refresh_from_db()
        self.assertEqual(self.character.current_hp, self.character.max_hp)
