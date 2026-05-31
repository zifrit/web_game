from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0009_location_item_template_chance"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserTwoFactor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("totp_protection", models.BooleanField(default=False, verbose_name="TOTP-защита включена")),
                ("active_secret_ciphertext", models.TextField(blank=True, default="", verbose_name="Активный TOTP-секрет")),
                ("pending_secret_ciphertext", models.TextField(blank=True, default="", verbose_name="Ожидающий TOTP-секрет")),
                ("pending_started_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата начала настройки")),
                ("confirmed_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата подтверждения")),
                ("last_verified_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата последней проверки")),
                ("last_timecode", models.BigIntegerField(blank=True, null=True, verbose_name="Последний использованный TOTP timecode")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="two_factor",
                        to="game.user",
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Двухфакторная защита",
                "verbose_name_plural": "Двухфакторная защита",
            },
        ),
    ]
