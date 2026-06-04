from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.game.i18n import request_locale
from apps.game.models import Character, CharacterClass
from apps.game.serializers import CharacterClassSerializer, CharacterCreateSerializer, CharacterMeSerializer
from apps.game.services import cached_response


class CharacterClassListView(APIView):
    """API-ручка списка доступных классов героев."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Возвращает активные классы героев (кэшируется, admin-only данные)."""

        def build():
            classes = CharacterClass.objects.filter(is_active=True).select_related("male_media", "female_media").order_by("sort_order", "key")
            return CharacterClassSerializer(classes, many=True, context={"request": request}).data

        return Response(cached_response("character_classes", build, parts=(request_locale(request),)))


class CharacterCreateView(APIView):
    """API-ручка создания единственного героя пользователя."""

    def post(self, request):
        """Создаёт героя выбранного класса, если у аккаунта ещё нет героя."""

        serializer = CharacterCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        character = serializer.save()
        return Response(CharacterCreateSerializer(character).data, status=status.HTTP_201_CREATED)


class CharacterMeView(APIView):
    """API-ручка получения текущего героя пользователя."""

    def get(self, request):
        """Возвращает героя с классом, характеристиками и экипировкой."""

        character = get_object_or_404(
            Character.objects.select_related(
                "character_class",
                "character_class__male_media",
                "character_class__female_media",
                "avatar_media",
            ).prefetch_related("equipped_items__template__media"),
            user=request.user,
        )
        self.check_object_permissions(request, character)
        return Response(CharacterMeSerializer(character, context={"request": request}).data)
