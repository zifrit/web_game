from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import (
    Character,
    CharacterClass,
    DungeonLocation,
    DungeonLocationItemTemplate,
    DungeonMiniGameAttempt,
    DungeonMiniGameConfig,
    DungeonRun,
    DungeonRunStatus,
    MiniGameCardFace,
)
from apps.game.serializers import (
    ClaimResponseSerializer,
    DungeonLootItemSerializer,
    localized_name,
    DungeonMiniGameAttemptHistorySerializer,
    DungeonMiniGameAttemptResponseSerializer,
    DungeonMiniGameMoveResponseSerializer,
    DungeonMiniGameMoveSerializer,
    DungeonMiniGameRevealSerializer,
    DungeonMiniGameStartSerializer,
    DungeonLocationSerializer,
    DungeonRunHistorySerializer,
    DungeonRunSerializer,
    DungeonRunStartSerializer,
)
from apps.game.services import (
    DungeonMiniGameService,
    DungeonRunService,
    GameFormulaService,
    cached_response,
    request_host_part,
)
from apps.game.services.reference_cache import reference_version


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


class DungeonLocationLootView(APIView):
    """API-ручка таблицы лута подземелья."""

    def get(self, request, pk):
        """Возвращает таблицу лута данжа (кэшируется, admin-only данные)."""

        get_object_or_404(DungeonLocation, pk=pk, is_active=True)
        locale = request_locale(request)

        def build():
            classes_map = {c.key: localized_name(c, locale) for c in CharacterClass.objects.all()}
            templates = (
                DungeonLocationItemTemplate.objects
                .filter(location_id=pk)
                .select_related("item_template")
                .order_by("item_template__slot")
            )
            return DungeonLootItemSerializer(
                templates, many=True,
                context={"request": request, "character_classes": classes_map},
            ).data

        return Response(cached_response("dungeon_loot", build, parts=(request_host_part(request), pk, locale)))


class DungeonRunStartView(APIView):
    """API-ручка запуска героя в подземелье."""

    throttle_scope = "dungeon_write"

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

    throttle_scope = "economy"

    def post(self, request, pk):
        """Идемпотентно начисляет опыт, деньги, предметы и потерю прочности."""

        locale = request_locale(request)
        result = DungeonRunService.claim_run(request.user, pk, locale=locale)
        return Response(ClaimResponseSerializer.render(result, locale=locale))


class DungeonMiniGameStartView(APIView):
    """API-ручка запуска мини-игры ускорения для активного забега."""

    throttle_scope = "mini_game"

    def post(self, request, pk):
        """Создаёт попытку memory-pairs мини-игры выбранной сложности или возвращает активную."""

        serializer = DungeonMiniGameStartSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        attempt = DungeonMiniGameService.start_attempt(
            request.user, pk, config_id=serializer.validated_data.get("config_id"), locale=locale
        )
        return Response(DungeonMiniGameAttemptResponseSerializer.render(attempt), status=status.HTTP_201_CREATED)


class MiniGameConfigCatalogView(APIView):
    """API-ручка каталога сложностей мини-игры для модалки выбора."""

    def get(self, request):
        """Возвращает активные сложности с процентом ускорения и параметрами."""

        configs = DungeonMiniGameConfig.objects.filter(is_active=True).order_by("sort_order", "pairs_count")
        return Response([DungeonMiniGameService.config_payload(config) for config in configs])


class MiniGameCardFaceCatalogView(APIView):
    """API-ручка каталога SVG-лиц карт: фронт грузит один раз и кеширует по версии."""

    def get(self, request):
        """Возвращает все активные лица с версией/ETag для инвалидации кеша."""

        version = reference_version()
        etag = f'W/"mini-faces-{version}"'
        if request.headers.get("If-None-Match") == etag:
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
            response["ETag"] = etag
            return response

        def build():
            faces = MiniGameCardFace.objects.filter(is_active=True).order_by("sort_order", "code")
            return [{"code": face.code, "name": face.name, "svg": face.svg_markup} for face in faces]

        faces = cached_response("mini_game_faces", build)
        response = Response({"version": version, "faces": faces})
        response["ETag"] = etag
        # private: ответ за аутентификацией, не должен попадать в общие прокси-кеши.
        response["Cache-Control"] = "private, max-age=60"
        return response


class DungeonMiniGameMoveView(APIView):
    """API-ручка серверной проверки хода мини-игры."""

    throttle_scope = "mini_game"

    def post(self, request, pk):
        """Принимает две карточки, проверяет пару и завершает игру только на backend."""

        serializer = DungeonMiniGameMoveSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        result = DungeonMiniGameService.make_move(
            request.user,
            pk,
            first_card_id=serializer.validated_data["first_card_id"],
            second_card_id=serializer.validated_data["second_card_id"],
            locale=locale,
        )
        return Response(DungeonMiniGameMoveResponseSerializer.render(result))


class DungeonMiniGameRevealView(APIView):
    """API-ручка открытия первой карточки мини-игры."""

    throttle_scope = "mini_game"

    def post(self, request, pk):
        """Возвращает лицо одной выбранной карточки без раскрытия всей доски."""

        serializer = DungeonMiniGameRevealSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        card = DungeonMiniGameService.reveal_card(
            request.user,
            pk,
            card_id=serializer.validated_data["card_id"],
            locale=locale,
        )
        return Response(card)


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


class DungeonMiniGameHistoryView(APIView):
    """API-ручка истории прохождений мини-игры."""

    def get(self, request):
        """Возвращает последние попытки memory-pairs мини-игры пользователя."""

        limit = min(int(request.query_params.get("limit", 20)), 100)
        attempts = (
            DungeonMiniGameAttempt.objects.filter(user=request.user)
            .select_related("config", "dungeon_run", "dungeon_run__location")
            .order_by("-started_at")[:limit]
        )
        for attempt in attempts:
            DungeonMiniGameService.expire_attempt_if_needed(attempt)
        return Response(DungeonMiniGameAttemptHistorySerializer(attempts, many=True, context={"request": request}).data)
