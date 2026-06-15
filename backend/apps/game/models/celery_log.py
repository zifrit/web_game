from django.conf import settings
from django.db import models

from .base import TimestampedModel


class CeleryTaskLog(TimestampedModel):
    """История ручных запусков Celery-задач через админку."""

    class Status(models.TextChoices):
        DISPATCHED = "dispatched", "Отправлена"
        SUCCESS = "success", "Успешно"
        FAILURE = "failure", "Ошибка"

    task_name = models.CharField("Задача", max_length=255)
    celery_task_id = models.CharField("ID задачи Celery", max_length=255, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Запущена пользователем",
        null=True,
        on_delete=models.SET_NULL,
        related_name="celery_task_logs",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DISPATCHED,
    )
    result = models.TextField("Результат", blank=True)

    class Meta:
        verbose_name = "Лог задачи"
        verbose_name_plural = "Логи задач"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.task_name} — {self.get_status_display()} ({self.created_at:%d.%m.%Y %H:%M})"
