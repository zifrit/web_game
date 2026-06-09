from django.db.models import Q

from apps.game.i18n import DEFAULT_LOCALE
from apps.game.models import Character

from .common import localized_name, media_payload


class LeaderboardItemSerializer:
    """Рендер таблицы лидеров по уровню или силе героя."""

    @staticmethod
    def render_items(items, locale=DEFAULT_LOCALE, request=None):
        """Формирует общий (одинаковый для всех) топ героев — пригоден для кэша."""

        context = {"request": request} if request else None
        return [
            {
                "rank": index + 1,
                "character_id": character.id,
                "character_name": character.name,
                "class": {"key": character.character_class_id, "name": localized_name(character.character_class, locale)},
                "level": character.level,
                "power": character.power_cached or 0,
                "avatar": media_payload(character.avatar_media, context),
            }
            for index, character in enumerate(items)
        ]

    @staticmethod
    def my_rank(my_character, metric="level"):
        """Вычисляет персональную позицию героя — считается на каждый запрос.

        Тай-брейки совпадают с порядком списка (см. LeaderboardView), чтобы
        my_rank не расходился с фактической позицией героя в таблице.
        """

        if not my_character:
            return None
        if metric == "power":
            # Список: (power_cached desc nulls_last, -level, created_at).
            my_power = my_character.power_cached or 0
            ahead = Character.objects.filter(
                Q(power_cached__gt=my_power)
                | Q(power_cached=my_power, level__gt=my_character.level)
                | Q(
                    power_cached=my_power,
                    level=my_character.level,
                    created_at__lt=my_character.created_at,
                )
            ).count()
            return {"rank": ahead + 1, "character_id": my_character.id, "power": my_power}
        # Список: (-level, -experience, created_at).
        ahead = Character.objects.filter(
            Q(level__gt=my_character.level)
            | Q(level=my_character.level, experience__gt=my_character.experience)
            | Q(
                level=my_character.level,
                experience=my_character.experience,
                created_at__lt=my_character.created_at,
            )
        ).count()
        return {"rank": ahead + 1, "character_id": my_character.id, "level": my_character.level}
