from django.db.models import Q

from apps.game.i18n import DEFAULT_LOCALE
from apps.game.models import Character

from .common import localized_name, media_payload


class LeaderboardItemSerializer:
    """Рендер таблицы лидеров по уровню героя."""

    @staticmethod
    def render(items, my_character, locale=DEFAULT_LOCALE, request=None):
        """Формирует топ героев и позицию текущего героя относительно топа."""

        context = {"request": request} if request else None
        payload = [
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
        my_rank = None
        if my_character:
            ahead = Character.objects.filter(
                Q(level__gt=my_character.level)
                | Q(level=my_character.level, experience__gt=my_character.experience)
            ).count()
            my_rank = {"rank": ahead + 1, "character_id": my_character.id, "level": my_character.level}
        return {"type": "level", "items": payload, "my_rank": my_rank}
