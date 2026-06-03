from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import message, request_locale
from apps.game.models import Character
from apps.game.serializers import LeaderboardItemSerializer
from apps.game.services import LEADERBOARD_TIMEOUT, cached_response


class LeaderboardView(APIView):
    """API-ручка таблицы лидеров по уровню героя."""

    def get(self, request):
        """Возвращает топ героев и позицию текущего героя, если он создан."""

        leaderboard_type = request.query_params.get("type", "level")
        locale = request_locale(request)
        if leaderboard_type != "level":
            return Response({"detail": message("leaderboard_level_only", locale)}, status=status.HTTP_400_BAD_REQUEST)

        def build_items():
            items = list(
                Character.objects.select_related("character_class", "avatar_media")
                .order_by("-level", "-experience", "created_at")[:100]
            )
            return LeaderboardItemSerializer.render_items(items, locale=locale, request=request)

        # Общий топ кэшируется на минуту, персональная позиция считается на лету.
        items = cached_response("leaderboard", build_items, parts=(locale,), timeout=LEADERBOARD_TIMEOUT)
        return Response(
            {
                "type": "level",
                "items": items,
                "my_rank": LeaderboardItemSerializer.my_rank(getattr(request.user, "character", None)),
            }
        )
