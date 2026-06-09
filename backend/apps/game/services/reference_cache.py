"""Кэш ответов для справочных (admin-only) и тяжёлых на чтение ручек.

Инвалидация построена на версии-счётчике: при изменении любой справочной
модели версия увеличивается, и все ключи со старой версией перестают
использоваться (истекают по TTL). Так одним сигналом инвалидируется сразу
весь набор справочных ответов без перебора отдельных ключей.
"""

from __future__ import annotations

from typing import Any, Callable

from django.conf import settings
from django.core.cache import cache

_VERSION_KEY = "ref:version"

# Запас по времени на случай, если сигнал инвалидации не сработал.
LEADERBOARD_TIMEOUT = 60
REFERENCE_TIMEOUT = 6 * 60 * 60


def reference_version() -> int:
    """Возвращает текущую версию справочного кэша, инициализируя её при первом доступе."""

    version = cache.get(_VERSION_KEY)
    if version is None:
        cache.add(_VERSION_KEY, 1)
        version = cache.get(_VERSION_KEY) or 1
    return int(version)


def request_host_part(request) -> str:
    """Часть ключа кэша, учитывающая схему+хост запроса.

    Ответы с абсолютными URL (media_payload → build_absolute_uri) зависят от
    хоста и схемы запроса. Без этой части первый запрос «запекает» свой хост в
    значение, и остальные хосты/схемы получают чужие ссылки до истечения TTL.
    """

    if request is None:
        return ""
    return f"{request.scheme}://{request.get_host()}"


def bump_reference_cache(*_args, **_kwargs) -> None:
    """Инвалидирует весь справочный кэш, увеличивая версию (обработчик сигналов)."""

    try:
        cache.incr(_VERSION_KEY)
    except ValueError:
        # Ключа ещё нет в кэше — создаём его сразу со второй версией.
        cache.set(_VERSION_KEY, 2)


def cached_response(
    name: str,
    builder: Callable[[], Any],
    *,
    parts: tuple[Any, ...] = (),
    timeout: int = REFERENCE_TIMEOUT,
) -> Any:
    """Возвращает закэшированный результат builder() с ключом, привязанным к версии.

    `name` — логическое имя ресурса, `parts` — дополнительные части ключа
    (например локаль или pk). Значение хранится JSON-совместимым.
    """

    # В тестах кэш не используется: LocMemCache не откатывается между тестами
    # и мог бы возвращать данные, не соответствующие состоянию БД.
    if getattr(settings, "TESTING", False):
        return builder()

    key_tail = ":".join(str(part) for part in parts)
    key = f"resp:{name}:{reference_version()}:{key_tail}" if key_tail else f"resp:{name}:{reference_version()}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = builder()
    cache.set(key, value, timeout)
    return value
