from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.game.i18n import message
from apps.game.models import User

from .common import serializer_locale


def token_response(user):
    """Формирует ответ авторизации с access/refresh токенами и данными пользователя."""

    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "has_character": hasattr(user, "character"),
        },
    }


class RegisterSerializer(serializers.Serializer):
    """Сериализатор регистрации нового пользователя."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        """Проверяет уникальность email перед созданием аккаунта."""

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(message("email_already_registered", serializer_locale(self.context)))
        return value

    def create(self, validated_data):
        """Создаёт пользователя через менеджер модели."""

        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Сериализатор входа пользователя."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Проверяет email и пароль, затем кладёт пользователя в validated_data."""

        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError(message("invalid_credentials", serializer_locale(self.context)))
        attrs["user"] = user
        return attrs
