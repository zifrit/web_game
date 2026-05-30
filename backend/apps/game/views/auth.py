from django.contrib.auth import authenticate
from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.game.i18n import message, request_locale
from apps.game.models import MediaAsset, User, UserTwoFactor
from apps.game.serializers import (
    LoginSerializer,
    RegisterSerializer,
    TotpCodeSerializer,
    TotpDisableSerializer,
    TotpLoginSerializer,
    media_payload,
    token_response,
)
from apps.game.two_factor import (
    create_login_challenge,
    create_totp_secret,
    decrypt_secret,
    encrypt_secret,
    ensure_two_factor,
    provisioning_uri,
    qr_data_url,
    two_factor_status_payload,
    verify_active_totp,
    verify_login_challenge,
    verify_totp_secret,
)


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
        user = User.objects.select_related("two_factor", "avatar_media").get(pk=serializer.validated_data["user"].pk)
        two_factor = getattr(user, "two_factor", None)
        if two_factor and two_factor.totp_protection:
            return Response({"two_factor_required": True, "challenge_token": create_login_challenge(user)})
        return Response(token_response(user, context={"request": request}))


class TotpLoginView(APIView):
    """API-ручка второго шага входа с TOTP-кодом."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Проверяет login challenge и TOTP-код, затем выдаёт JWT-токены."""

        serializer = TotpLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        try:
            challenge_user = verify_login_challenge(serializer.validated_data["challenge_token"])
        except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist):
            return Response({"detail": message("invalid_totp_challenge", locale)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_related("avatar_media").get(pk=challenge_user.pk)
            two_factor = UserTwoFactor.objects.select_for_update().filter(user=user).first()
            if not two_factor or not verify_active_totp(two_factor, serializer.validated_data["code"]):
                return Response({"detail": message("invalid_totp_code", locale)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(token_response(user, context={"request": request}))


class MeView(APIView):
    """API-ручка получения краткой информации о текущем пользователе."""

    def get(self, request):
        """Возвращает профиль, баланс и признак наличия созданного героя."""

        user = User.objects.select_related("avatar_media", "character", "two_factor").get(pk=request.user.pk)
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "money_copper": user.money_copper,
                "has_character": hasattr(user, "character"),
                "avatar": media_payload(user.avatar_media, {"request": request}),
                "two_factor": {
                    "totp_protection": bool(getattr(user, "two_factor", None) and user.two_factor.totp_protection),
                },
            }
        )


class TwoFactorStatusView(APIView):
    """API-ручка состояния TOTP-защиты текущего пользователя."""

    def get(self, request):
        """Возвращает признак включения и наличие незавершённой настройки."""

        return Response(two_factor_status_payload(ensure_two_factor(request.user)))


class TwoFactorSetupView(APIView):
    """API-ручка запуска настройки TOTP-защиты."""

    def post(self, request):
        """Создаёт pending TOTP-секрет и возвращает QR + manual key."""

        locale = request_locale(request)
        two_factor = ensure_two_factor(request.user)
        if two_factor.totp_protection:
            return Response({"detail": message("totp_already_enabled", locale)}, status=status.HTTP_400_BAD_REQUEST)

        secret = create_totp_secret()
        uri = provisioning_uri(request.user, secret)
        two_factor.pending_secret_ciphertext = encrypt_secret(secret)
        two_factor.pending_started_at = timezone.now()
        two_factor.save(update_fields=["pending_secret_ciphertext", "pending_started_at", "updated_at"])
        return Response({"secret": secret, "otpauth_uri": uri, "qr_data_url": qr_data_url(uri)})


class TwoFactorConfirmView(APIView):
    """API-ручка подтверждения pending TOTP-секрета."""

    def post(self, request):
        """Проверяет код из pending секрета и включает TOTP-защиту."""

        serializer = TotpCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)

        with transaction.atomic():
            two_factor = UserTwoFactor.objects.select_for_update().filter(user=request.user).first()
            if not two_factor or not two_factor.pending_secret_ciphertext:
                return Response({"detail": message("totp_setup_required", locale)}, status=status.HTTP_400_BAD_REQUEST)

            secret = decrypt_secret(two_factor.pending_secret_ciphertext)
            if not verify_totp_secret(secret, serializer.validated_data["code"]):
                return Response({"detail": message("invalid_totp_code", locale)}, status=status.HTTP_400_BAD_REQUEST)

            two_factor.active_secret_ciphertext = two_factor.pending_secret_ciphertext
            two_factor.pending_secret_ciphertext = ""
            two_factor.pending_started_at = None
            two_factor.totp_protection = True
            two_factor.confirmed_at = timezone.now()
            two_factor.last_timecode = None
            two_factor.save(
                update_fields=[
                    "active_secret_ciphertext",
                    "pending_secret_ciphertext",
                    "pending_started_at",
                    "totp_protection",
                    "confirmed_at",
                    "last_timecode",
                    "updated_at",
                ]
            )

        return Response(two_factor_status_payload(two_factor))


class TwoFactorDisableView(APIView):
    """API-ручка отключения TOTP-защиты."""

    def post(self, request):
        """Отключает TOTP после проверки пароля и текущего TOTP-кода."""

        serializer = TotpDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        locale = request_locale(request)
        user = authenticate(email=request.user.email, password=serializer.validated_data["password"])
        if not user:
            return Response({"detail": message("invalid_credentials", locale)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            two_factor = UserTwoFactor.objects.select_for_update().filter(user=request.user).first()
            if not two_factor or not two_factor.totp_protection:
                return Response({"detail": message("totp_not_configured", locale)}, status=status.HTTP_400_BAD_REQUEST)
            if not verify_active_totp(two_factor, serializer.validated_data["code"]):
                return Response({"detail": message("invalid_totp_code", locale)}, status=status.HTTP_400_BAD_REQUEST)

            two_factor.totp_protection = False
            two_factor.active_secret_ciphertext = ""
            two_factor.pending_secret_ciphertext = ""
            two_factor.pending_started_at = None
            two_factor.confirmed_at = None
            two_factor.last_verified_at = None
            two_factor.last_timecode = None
            two_factor.save(
                update_fields=[
                    "totp_protection",
                    "active_secret_ciphertext",
                    "pending_secret_ciphertext",
                    "pending_started_at",
                    "confirmed_at",
                    "last_verified_at",
                    "last_timecode",
                    "updated_at",
                ]
            )

        return Response(two_factor_status_payload(two_factor))


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

        assets = MediaAsset.objects.filter(asset_type=MediaAsset.AssetType.ICONS).only("id", "name", "large", "medium", "small").order_by("name", "pk")
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
