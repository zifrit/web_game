from django.db.models import Q

from apps.game.i18n import DEFAULT_LOCALE
from apps.game.models import Character

from .common import localized_name, media_payload


class LeaderboardItemSerializer:
    """Рендер таблицы лидеров по уровню героя."""

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
                "avatar": media_payload(character.avatar_media, context),
            }
            for index, character in enumerate(items)
        ]

    @staticmethod
    def my_rank(my_character):
        """Вычисляет персональную позицию героя — считается на каждый запрос."""

        if not my_character:
            return None
        ahead = Character.objects.filter(
            Q(level__gt=my_character.level)
            | Q(level=my_character.level, experience__gt=my_character.experience)
        ).count()
        return {"rank": ahead + 1, "character_id": my_character.id, "level": my_character.level}

    @staticmethod
    def render(items, my_character, locale=DEFAULT_LOCALE, request=None):
        """Формирует топ героев и позицию текущего героя относительно топа."""

        return {
            "type": "level",
            "items": LeaderboardItemSerializer.render_items(items, locale=locale, request=request),
            "my_rank": LeaderboardItemSerializer.my_rank(my_character),
        }
