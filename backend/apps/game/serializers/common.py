from urllib.parse import urlparse

from apps.game.i18n import request_locale, translate
from apps.game.models import UserItem
from apps.game.services import RarityConfigCache


def serializer_locale(context):
    """Определяет локаль сериализатора из контекста или HTTP-запроса."""

    return context.get("locale") or request_locale(context.get("request"))


def localized_name(obj, locale: str) -> str:
    """Возвращает локализованное имя объекта или базовое поле name."""

    return translate(getattr(obj, "name_i18n", None), locale, getattr(obj, "name", ""))


def localized_item_name(item: UserItem, locale: str, context: dict | None = None) -> str:
    """Собирает локализованное имя предмета из редкости и шаблона."""

    template_name = localized_name(item.template, locale) if getattr(item, "template", None) else item.name
    rarity_name = translate(getattr(getattr(item, "_rarity_config", None), "name_i18n", None), locale, "")
    if not rarity_name:
        rarity = RarityConfigCache.all_active().get(item.rarity)
        rarity_name = localized_name(rarity, locale) if rarity else item.rarity.replace("_", " ").title()
    if template_name.lower().startswith(f"{rarity_name.lower()} "):
        return template_name
    return f"{rarity_name} {template_name}".strip()


def _absolute_media_url(url: str, context) -> str:
    """Преобразует относительный storage URL в абсолютный, не трогая уже абсолютные ссылки."""

    if not url:
        return ""
    if urlparse(url).scheme:
        return url
    request = context.get("request") if context else None
    if request:
        return request.build_absolute_uri(url)
    return url


def media_payload(media, context=None):
    """Преобразует модель медиа в компактный API-словарь URL-адресов."""

    if not media:
        return None
    return {
        "large_url": _absolute_media_url(media.large_url, context),
        "medium_url": _absolute_media_url(media.medium_url, context),
        "small_url": _absolute_media_url(media.small_url, context),
    }
