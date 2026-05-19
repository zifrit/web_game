from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import message, request_locale
from apps.game.models import Character
from apps.game.serializers import LeaderboardItemSerializer


class LeaderboardView(APIView):
    """API-ручка таблицы лидеров по уровню героя."""

    def get(self, request):
        """Возвращает топ героев и позицию текущего героя, если он создан."""

        leaderboard_type = request.query_params.get("type", "level")
        if leaderboard_type != "level":
            return Response({"detail": message("leaderboard_level_only", request_locale(request))}, status=status.HTTP_400_BAD_REQUEST)
        items = list(
            Character.objects.select_related("character_class", "avatar_media")
            .order_by("-level", "-experience", "created_at")[:100]
        )
        return Response(
            LeaderboardItemSerializer.render(
                items,
                getattr(request.user, "character", None),
                locale=request_locale(request),
                request=request,
            )
        )
