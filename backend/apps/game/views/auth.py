from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.game.serializers import LoginSerializer, RegisterSerializer, token_response


class RegisterView(APIView):
    """API-ручка регистрации пользователя и выдачи JWT-токенов."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Создаёт аккаунт по email и паролю, затем возвращает токены авторизации."""

        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(token_response(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """API-ручка входа пользователя по email и паролю."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Проверяет учётные данные и возвращает новую пару JWT-токенов."""

        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(token_response(serializer.validated_data["user"]))


class MeView(APIView):
    """API-ручка получения краткой информации о текущем пользователе."""

    def get(self, request):
        """Возвращает профиль, баланс и признак наличия созданного героя."""

        return Response(
            {
                "id": request.user.id,
                "email": request.user.email,
                "money_copper": request.user.money_copper,
                "has_character": hasattr(request.user, "character"),
            }
        )


class LogoutView(APIView):
    """API-ручка выхода пользователя через блокировку refresh-токена."""

    def post(self, request):
        """Добавляет переданный refresh-токен в blacklist и завершает сессию."""

        token = request.data.get("refresh") or request.data.get("refresh_token")
        if token:
            RefreshToken(token).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
