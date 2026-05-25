from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.game.models import MediaAsset, User
from apps.game.serializers import LoginSerializer, RegisterSerializer, media_payload, token_response


class RegisterView(APIView):
    """API-ручка регистрации пользователя и выдачи JWT-токенов."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Создаёт аккаунт по email и паролю, затем возвращает токены авторизации."""

        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(token_response(user, context={"request": request}), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """API-ручка входа пользователя по email и паролю."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Проверяет учётные данные и возвращает новую пару JWT-токенов."""

        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(token_response(serializer.validated_data["user"], context={"request": request}))


class MeView(APIView):
    """API-ручка получения краткой информации о текущем пользователе."""

    def get(self, request):
        """Возвращает профиль, баланс и признак наличия созданного героя."""

        user = User.objects.select_related("avatar_media").get(pk=request.user.pk)
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "money_copper": user.money_copper,
                "has_character": hasattr(user, "character"),
                "avatar": media_payload(user.avatar_media, {"request": request}),
            }
        )


class UserAvatarUpdateView(APIView):
    """API-ручка смены аватара пользователя."""

    def patch(self, request):
        """Устанавливает пользователю аватар из переданного id медиа-ассета."""

        asset_id = request.data.get("avatar_media_id")
        if not asset_id:
            return Response({"detail": "avatar_media_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            asset = MediaAsset.objects.get(pk=asset_id, asset_type=MediaAsset.AssetType.ICONS)
        except MediaAsset.DoesNotExist:
            return Response({"detail": "Icon asset not found."}, status=status.HTTP_404_NOT_FOUND)
        request.user.avatar_media = asset
        request.user.save(update_fields=["avatar_media"])
        return Response({"avatar": media_payload(asset, {"request": request})})


class IconAssetsView(APIView):
    """API-ручка получения списка иконок для выбора аватара."""

    def get(self, request):
        """Возвращает все медиа-ассеты с типом ICONS."""

        assets = MediaAsset.objects.filter(asset_type=MediaAsset.AssetType.ICONS).order_by("name", "pk")
        ctx = {"request": request}
        return Response([
            {"id": a.pk, "name": a.name, **media_payload(a, ctx)}
            for a in assets
        ])


class LogoutView(APIView):
    """API-ручка выхода пользователя через блокировку refresh-токена."""

    def post(self, request):
        """Добавляет переданный refresh-токен в blacklist и завершает сессию."""

        token = request.data.get("refresh") or request.data.get("refresh_token")
        if token:
            RefreshToken(token).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
