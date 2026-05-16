from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Character, CharacterClass, DungeonLocation, DungeonRun, DungeonRunStatus, UserItem
from .serializers import (
    CharacterClassSerializer,
    CharacterCreateSerializer,
    CharacterMeSerializer,
    ClaimResponseSerializer,
    DungeonLocationSerializer,
    DungeonRunHistorySerializer,
    DungeonRunSerializer,
    DungeonRunStartSerializer,
    InventorySerializer,
    LeaderboardItemSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserItemDetailSerializer,
    token_response,
)
from .services import DungeonRunService, InventoryService


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(token_response(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(token_response(serializer.validated_data["user"]))


class MeView(APIView):
    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "email": request.user.email,
                "money_copper": request.user.money_copper,
                "has_character": hasattr(request.user, "character"),
            }
        )


class LogoutView(APIView):
    def post(self, request):
        token = request.data.get("refresh") or request.data.get("refresh_token")
        if token:
            RefreshToken(token).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CharacterClassListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        classes = CharacterClass.objects.filter(is_active=True).order_by("sort_order", "key")
        return Response(CharacterClassSerializer(classes, many=True).data)


class CharacterCreateView(APIView):
    def post(self, request):
        serializer = CharacterCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        character = serializer.save()
        return Response(CharacterCreateSerializer(character).data, status=status.HTTP_201_CREATED)


class CharacterMeView(APIView):
    def get(self, request):
        character = get_object_or_404(
            Character.objects.select_related("character_class").prefetch_related("equipped_items__template__media"),
            user=request.user,
        )
        return Response(CharacterMeSerializer(character).data)


class DungeonLocationListView(APIView):
    def get(self, request):
        character = getattr(request.user, "character", None)
        locations = DungeonLocation.objects.filter(is_active=True).select_related("media")
        return Response(DungeonLocationSerializer(locations, many=True, context={"character": character}).data)


class DungeonLocationDetailView(APIView):
    def get(self, request, pk):
        character = getattr(request.user, "character", None)
        location = get_object_or_404(DungeonLocation.objects.select_related("media"), pk=pk, is_active=True)
        return Response(DungeonLocationSerializer(location, context={"character": character}).data)


class DungeonRunStartView(APIView):
    def post(self, request):
        serializer = DungeonRunStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = DungeonRunService.start_run(request.user, serializer.validated_data["location_id"])
        run = DungeonRun.objects.select_related("location").get(pk=run.pk)
        return Response(DungeonRunSerializer(run).data, status=status.HTTP_201_CREATED)


class DungeonRunCurrentView(APIView):
    def get(self, request):
        character = getattr(request.user, "character", None)
        if not character:
            return Response({"current_run": None})
        run = (
            DungeonRun.objects.select_related("location", "character", "character__character_class")
            .filter(
                character=character,
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
        return Response(DungeonRunSerializer(run).data)


class DungeonRunClaimView(APIView):
    def post(self, request, pk):
        result = DungeonRunService.claim_run(request.user, pk)
        return Response(ClaimResponseSerializer.render(result))


class DungeonRunHistoryView(APIView):
    def get(self, request):
        character = getattr(request.user, "character", None)
        if not character:
            return Response([])
        limit = min(int(request.query_params.get("limit", 20)), 100)
        runs = (
            DungeonRun.objects.filter(character=character)
            .select_related("location", "claim")
            .exclude(status=DungeonRunStatus.IN_PROGRESS)
            .order_by("-started_at")[:limit]
        )
        return Response(DungeonRunHistorySerializer(runs, many=True).data)


class InventoryView(APIView):
    def get(self, request):
        character = get_object_or_404(
            Character.objects.select_related("character_class", "user").prefetch_related("equipped_items__template__media"),
            user=request.user,
        )
        return Response(InventorySerializer.render(character))


class InventoryItemDetailView(APIView):
    def get(self, request, item_id):
        item = get_object_or_404(UserItem.objects.select_related("template__media"), pk=item_id, owner_user=request.user)
        character = getattr(request.user, "character", None)
        return Response(UserItemDetailSerializer(item, context={"character": character}).data)


class InventoryItemRepairPreviewView(APIView):
    def get(self, request, item_id):
        item = get_object_or_404(UserItem, pk=item_id, owner_user=request.user)
        return Response(InventoryService.repair_preview(request.user, item))


class InventoryItemRepairView(APIView):
    def post(self, request, item_id):
        item, cost, remaining_money = InventoryService.repair(request.user, item_id)
        return Response(
            {
                "success": True,
                "repair_cost_copper": cost,
                "durability": {"current": item.durability_current, "max": item.durability_max},
                "remaining_money_copper": remaining_money,
            }
        )


class InventoryItemEquipView(APIView):
    def post(self, request, item_id):
        item, new_power = InventoryService.equip(request.user, item_id)
        return Response({"success": True, "equipped_slot": item.slot, "item_id": item.id, "new_power": new_power})


class InventoryItemUnequipView(APIView):
    def post(self, request, item_id):
        new_power = InventoryService.unequip(request.user, item_id)
        return Response({"success": True, "new_power": new_power})


class LeaderboardView(APIView):
    def get(self, request):
        leaderboard_type = request.query_params.get("type", "level")
        if leaderboard_type != "level":
            return Response({"detail": "Only level leaderboard is available in MVP."}, status=status.HTTP_400_BAD_REQUEST)
        items = list(
            Character.objects.select_related("character_class", "avatar_media")
            .order_by("-level", "-experience", "created_at")[:100]
        )
        return Response(LeaderboardItemSerializer.render(items, getattr(request.user, "character", None)))
