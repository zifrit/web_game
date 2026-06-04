from django.db.models import F
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import message, request_locale
from apps.game.models import Character
from apps.game.serializers import LeaderboardItemSerializer
from apps.game.services import LEADERBOARD_TIMEOUT, cached_response

LEADERBOARD_TYPES = ("level", "power")


class LeaderboardView(APIView):
    """API-ручка таблицы лидеров по уровню или силе героя."""

    def get(self, request):
        """Возвращает топ героев и позицию текущего героя, если он создан."""

        leaderboard_type = request.query_params.get("type", "level")
        locale = request_locale(request)
        if leaderboard_type not in LEADERBOARD_TYPES:
            return Response({"detail": message("leaderboard_type_invalid", locale)}, status=status.HTTP_400_BAD_REQUEST)

        if leaderboard_type == "power":
            ordering = (F("power_cached").desc(nulls_last=True), "-level", "created_at")
        else:
            ordering = ("-level", "-experience", "created_at")

        def build_items():
            items = list(
                Character.objects.select_related("character_class", "avatar_media").order_by(*ordering)[:100]
            )
            return LeaderboardItemSerializer.render_items(items, locale=locale, request=request)

        # Общий топ кэшируется на минуту, персональная позиция считается на лету.
        items = cached_response("leaderboard", build_items, parts=(locale, leaderboard_type), timeout=LEADERBOARD_TIMEOUT)
        return Response(
            {
                "type": leaderboard_type,
                "items": items,
                "my_rank": LeaderboardItemSerializer.my_rank(
                    getattr(request.user, "character", None), metric=leaderboard_type
                ),
            }
        )
