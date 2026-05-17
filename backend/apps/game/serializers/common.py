from apps.game.i18n import request_locale, translate
from apps.game.models import RarityConfig, UserItem


def serializer_locale(context):
    """Определяет локаль сериализатора из контекста или HTTP-запроса."""

    return context.get("locale") or request_locale(context.get("request"))


def localized_name(obj, locale: str) -> str:
    """Возвращает локализованное имя объекта или базовое поле name."""

    return translate(getattr(obj, "name_i18n", None), locale, getattr(obj, "name", ""))


def localized_item_name(item: UserItem, locale: str) -> str:
    """Собирает локализованное имя предмета из редкости и шаблона."""

    template_name = localized_name(item.template, locale) if getattr(item, "template", None) else item.name
    rarity_name = translate(getattr(getattr(item, "_rarity_config", None), "name_i18n", None), locale, "")
    if not rarity_name:
        rarity = RarityConfig.objects.filter(key=item.rarity).first()
        rarity_name = localized_name(rarity, locale) if rarity else item.rarity.replace("_", " ").title()
    return f"{rarity_name} {template_name}".strip()


def media_payload(media):
    """Преобразует модель медиа в компактный API-словарь URL-адресов."""

    if not media:
        return None
    return {
        "icon_url": media.icon_url,
        "small_url": media.small_url,
        "medium_url": media.medium_url,
        "large_url": media.large_url,
    }
