from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from .base import MediaAsset, TimestampedModel


class UserManager(BaseUserManager):
    """Менеджер пользователей с авторизацией по email вместо username."""

    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Создаёт обычного пользователя с нормализованным email и паролем."""

        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Создаёт администратора с правами staff и superuser."""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Игровой аккаунт пользователя с балансом меди и аватаром."""

    email = models.EmailField("Email", unique=True)
    money_copper = models.PositiveIntegerField("Баланс в медных монетах", default=0)
    avatar_media = models.ForeignKey(MediaAsset, verbose_name="Аватар", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Доступ в админку", default=False)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        """Возвращает email как человекочитаемое имя аккаунта."""

        return self.email


class UserTwoFactor(TimestampedModel):
    """Настройки двухфакторной TOTP-защиты игрового аккаунта."""

    user = models.OneToOneField(User, verbose_name="Пользователь", related_name="two_factor", on_delete=models.CASCADE)
    totp_protection = models.BooleanField("TOTP-защита включена", default=False)
    active_secret_ciphertext = models.TextField("Активный TOTP-секрет", blank=True, default="")
    pending_secret_ciphertext = models.TextField("Ожидающий TOTP-секрет", blank=True, default="")
    pending_started_at = models.DateTimeField("Дата начала настройки", null=True, blank=True)
    confirmed_at = models.DateTimeField("Дата подтверждения", null=True, blank=True)
    last_verified_at = models.DateTimeField("Дата последней проверки", null=True, blank=True)
    last_timecode = models.BigIntegerField("Последний использованный TOTP timecode", null=True, blank=True)

    class Meta:
        verbose_name = "Двухфакторная защита"
        verbose_name_plural = "Двухфакторная защита"

    def __str__(self) -> str:
        """Возвращает краткое описание настройки 2FA."""

        return f"2FA for {self.user.email}"
