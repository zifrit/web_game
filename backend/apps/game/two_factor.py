import base64
import hmac
from io import BytesIO
import time

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core import signing
from django.utils import timezone
import pyotp
import qrcode

from apps.game.models import User, UserTwoFactor


TOTP_INTERVAL_SECONDS = 30
TOTP_VALID_WINDOW = 1
LOGIN_CHALLENGE_MAX_AGE_SECONDS = 300
LOGIN_CHALLENGE_SALT = "apps.game.auth.totp-login"
TOTP_ISSUER = "VultWake"


def _fernet() -> Fernet:
    key = getattr(settings, "TOTP_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured("TOTP_ENCRYPTION_KEY must be configured for two-factor secret encryption.")
    try:
        return Fernet(key.encode())
    except ValueError as exc:
        raise ImproperlyConfigured("TOTP_ENCRYPTION_KEY must be a valid Fernet key.") from exc


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


def ensure_two_factor(user: User) -> UserTwoFactor:
    two_factor, _ = UserTwoFactor.objects.get_or_create(user=user)
    return two_factor


def two_factor_payload(user: User) -> dict:
    two_factor = getattr(user, "two_factor", None)
    return {"totp_protection": bool(two_factor and two_factor.totp_protection)}


def two_factor_status_payload(two_factor: UserTwoFactor) -> dict:
    return {
        "totp_protection": two_factor.totp_protection,
        "setup_pending": bool(two_factor.pending_secret_ciphertext),
    }


def create_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(user: User, secret: str) -> str:
    return pyotp.TOTP(secret, interval=TOTP_INTERVAL_SECONDS).provisioning_uri(
        name=user.email,
        issuer_name=TOTP_ISSUER,
    )


def qr_data_url(uri: str) -> str:
    image = qrcode.make(uri)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def create_login_challenge(user: User) -> str:
    signer = signing.TimestampSigner(salt=LOGIN_CHALLENGE_SALT)
    return signer.sign_object({"user_id": user.pk})


def verify_login_challenge(challenge_token: str) -> User:
    signer = signing.TimestampSigner(salt=LOGIN_CHALLENGE_SALT)
    payload = signer.unsign_object(challenge_token, max_age=LOGIN_CHALLENGE_MAX_AGE_SECONDS)
    return User.objects.get(pk=payload["user_id"])


def current_timecode() -> int:
    return int(time.time()) // TOTP_INTERVAL_SECONDS


def matching_timecode(secret: str, code: str) -> int | None:
    value = "".join(str(code or "").split())
    if not value.isdigit() or len(value) != 6:
        return None

    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL_SECONDS)
    current = current_timecode()
    for offset in range(-TOTP_VALID_WINDOW, TOTP_VALID_WINDOW + 1):
        timecode = current + offset
        expected = totp.at(timecode * TOTP_INTERVAL_SECONDS)
        if hmac.compare_digest(expected, value):
            return timecode
    return None


def verify_totp_secret(secret: str, code: str) -> bool:
    return matching_timecode(secret, code) is not None


def verify_active_totp(two_factor: UserTwoFactor, code: str) -> bool:
    if not two_factor.totp_protection or not two_factor.active_secret_ciphertext:
        return False

    secret = decrypt_secret(two_factor.active_secret_ciphertext)
    timecode = matching_timecode(secret, code)
    if timecode is None:
        return False
    if two_factor.last_timecode is not None and timecode <= two_factor.last_timecode:
        return False

    two_factor.last_timecode = timecode
    two_factor.last_verified_at = timezone.now()
    two_factor.save(update_fields=["last_timecode", "last_verified_at", "updated_at"])
    return True
