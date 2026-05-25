from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import Character, DungeonLocation, DungeonRun, DungeonRunStatus
from apps.game.serializers import (
    ClaimResponseSerializer,
    DungeonLocationSerializer,
    DungeonRunHistorySerializer,
    DungeonRunSerializer,
    DungeonRunStartSerializer,
)
from apps.game.services import DungeonRunService, GameFormulaService


class DungeonLocationListView(APIView):
    """API-ручка списка доступных подземелий."""

    def get(self, request):
        """Возвращает активные локации с расчётным шансом успеха для героя."""

        character = None
        character_power = None
        try:
            character = Character.objects.select_related("character_class").prefetch_related("equipped_items").get(user=request.user)
            character_power = GameFormulaService.character_stats(character)["power"]
        except Character.DoesNotExist:
            pass
        locations = DungeonLocation.objects.filter(is_active=True).select_related("media")
        return Response(DungeonLocationSerializer(locations, many=True, context={"request": request, "character": character, "character_power": character_power}).data)


class DungeonLocationDetailView(APIView):
    """API-ручка детальной информации о подземелье."""

    def get(self, request, pk):
        """Возвращает одну активную локацию подземелья по идентификатору."""

        character = None
        character_power = None
        try:
            character = Character.objects.select_related("character_class").prefetch_related("equipped_items").get(user=request.user)
            character_power = GameFormulaService.character_stats(character)["power"]
        except Character.DoesNotExist:
            pass
        location = get_object_or_404(DungeonLocation.objects.select_related("media"), pk=pk, is_active=True)
        return Response(DungeonLocationSerializer(location, context={"request": request, "character": character, "character_power": character_power}).data)


class DungeonRunStartView(APIView):
    """API-ручка запуска героя в подземелье."""

    def post(self, request):
        """Создаёт новый забег, если у героя нет активного забега и сломанных вещей."""

        serializer = DungeonRunStartSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        run = DungeonRunService.start_run(request.user, serializer.validated_data["location_id"], locale=locale)
        return Response(DungeonRunSerializer(run, context={"request": request}).data, status=status.HTTP_201_CREATED)


class DungeonRunCurrentView(APIView):
    """API-ручка текущего или ожидающего награды забега."""

    def get(self, request):
        """Возвращает активный забег и при необходимости завершает его на лету."""

        run = (
            DungeonRun.objects.select_related("location", "character", "character__character_class")
            .filter(
                character__user=request.user,
                status__in=[
                    DungeonRunStatus.IN_PROGRESS,
                    DungeonRunStatus.SUCCESS_WAITING_CLAIM,
                    DungeonRunStatus.FAILED_WAITING_CLAIM,
                ],
            )
            .order_by("-started_at")
            .first()
        )
        if not run:
            return Response({"current_run": None})
        if run.status == DungeonRunStatus.IN_PROGRESS:
            DungeonRunService.finalize_due_run(run)
        return Response(DungeonRunSerializer(run, context={"request": request}).data)


class DungeonRunClaimView(APIView):
    """API-ручка получения наград за завершённый забег."""

    def post(self, request, pk):
        """Идемпотентно начисляет опыт, деньги, предметы и потерю прочности."""

        locale = request_locale(request)
        result = DungeonRunService.claim_run(request.user, pk, locale=locale)
        return Response(ClaimResponseSerializer.render(result, locale=locale))


class DungeonRunHistoryView(APIView):
    """API-ручка истории завершённых забегов героя."""

    def get(self, request):
        """Возвращает последние завершённые забеги без активных прохождений."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        runs = (
            DungeonRun.objects.filter(character__user=request.user)
            .select_related("location", "claim")
            .exclude(status=DungeonRunStatus.IN_PROGRESS)
            .order_by("-started_at")[:limit]
        )
        return Response(DungeonRunHistorySerializer(runs, many=True, context={"request": request}).data)
