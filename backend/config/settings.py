from datetime import timedelta
from pathlib import Path
import os
import sys

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Тестовый прогон: pytest или manage.py test. В тестах не требуем Redis
# и не ограничиваем частоту запросов, чтобы наборы тестов не упирались в лимиты.
TESTING = "pytest" in sys.modules or "test" in sys.argv

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
TOTP_ENCRYPTION_KEY = os.getenv("TOTP_ENCRYPTION_KEY", "")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
SQL_DEBUG = True
POLZA_AI_API_KEY = os.getenv("POLZA_AI_API_KEY")
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,backend").split(",") if host.strip()]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "storages",
    "rest_framework_simplejwt.token_blacklist",
    "django_extensions",
    "apps.game",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "game.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000",
    ).split(",")
    if origin.strip()
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("apps.game.permissions.IsSuperuserOrOwner",),
    # ScopedRateThrottle применяется только к view с заданным throttle_scope,
    # поэтому высокочастотные игровые ручки без скоупа не ограничиваются.
    "DEFAULT_THROTTLE_CLASSES": () if TESTING else ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        # Аутентификация: ключ по IP (анонимные запросы) — защита от перебора.
        "auth_login": "10/min",
        "auth_register": "5/min",
        "auth_totp": "10/min",
        "auth_refresh": "30/min",
        # Чувствительные операции 2FA: ключ по пользователю.
        "two_factor": "10/min",
        # Игровая экономика и запись инвентаря — защита от фарма/эксплойтов.
        "economy": "60/min",
        "dungeon_write": "60/min",
        "inventory_write": "60/min",
        # Мини-игра допускает частые ходы, но всё же ограничена.
        "mini_game": "120/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=20),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Соль для детерминированной, но непредсказуемой раскладки карт мини-игры и
# буфер TTL для Redis-стейта активной партии сверх таймера попытки.
MINIGAME_BOARD_SALT = os.getenv("MINIGAME_BOARD_SALT", SECRET_KEY)
MINIGAME_STATE_TTL_BUFFER_SECONDS = int(os.getenv("MINIGAME_STATE_TTL_BUFFER_SECONDS", "60"))

# Кэш ответов и backend для DRF-троттлинга. По умолчанию берём тот же хост, что и
# брокер Celery (REDIS_URL), но отдельную базу (db 1), чтобы не смешивать ключи.
def _derive_cache_url(redis_url: str) -> str:
    """Возвращает URL Redis с подменой номера базы данных на 1."""

    base, _, _ = redis_url.rpartition("/")
    if base.startswith("redis://") or base.startswith("rediss://"):
        return f"{base}/1"
    return redis_url.rstrip("/") + "/1"


REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL") or _derive_cache_url(REDIS_URL)
if TESTING:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
            "KEY_PREFIX": "webgame",
            "TIMEOUT": 300,
        }
    }
CELERY_BEAT_SCHEDULE = {
    "complete-dungeon-runs": {
        "task": "apps.game.tasks.complete_due_dungeon_runs",
        "schedule": 5.0,
    }
}


# AWS настройки
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = os.environ.get("AWS_DEFAULT_ACL")
AWS_S3_ADDRESSING_STYLE = os.environ.get("AWS_S3_ADDRESSING_STYLE")
AWS_S3_SIGNATURE_VERSION = os.environ.get("AWS_S3_SIGNATURE_VERSION")
AWS_QUERYSTRING_AUTH = True

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage"
        if AWS_STORAGE_BUCKET_NAME
        else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if SQL_DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "django.db.backends": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
        },
    }
