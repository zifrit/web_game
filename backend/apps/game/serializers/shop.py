from rest_framework import serializers

from apps.game.models import ShopOffer

from .common import localized_name, media_payload, serializer_locale


def _localized(mapping: dict, locale: str) -> str:
    """Возвращает значение из i18n-словаря по локали с запасными вариантами."""

    if not mapping:
        return ""
    return mapping.get(locale) or mapping.get("en") or mapping.get("ru") or ""


def _offer_prices(offer: ShopOffer) -> dict:
    """Собирает словарь доступных цен предложения, опуская отсутствующие."""

    prices = {}
    if offer.price_money_copper is not None:
        prices["money_copper"] = offer.price_money_copper
    if offer.price_premium_currency is not None:
        prices["premium_currency"] = offer.price_premium_currency
    return prices


class ShopOfferListSerializer(serializers.Serializer):
    """Лёгкий сериализатор карточки магазина без возможных наград."""

    id = serializers.IntegerField()
    reward_kind = serializers.CharField()
    delivery_mode = serializers.CharField()
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    quantity = serializers.IntegerField()
    prices = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        return _localized(obj.name_i18n, serializer_locale(self.context))

    def get_description(self, obj) -> str:
        return _localized(obj.description_i18n, serializer_locale(self.context))

    def get_prices(self, obj) -> dict:
        return _offer_prices(obj)

    def get_media(self, obj):
        return media_payload(obj.media, self.context)


class ShopOfferDetailSerializer(ShopOfferListSerializer):
    """Подробный сериализатор предложения с возможными наградами и шансами."""

    possible_rewards = serializers.SerializerMethodField()

    def get_possible_rewards(self, obj) -> list:
        locale = serializer_locale(self.context)
        if obj.reward_kind == ShopOffer.RewardKind.INGREDIENT:
            entries = list(obj.ingredient_entries.all())
            template_attr, type_label = "ingredient_template", "ingredient"
        elif obj.reward_kind == ShopOffer.RewardKind.POTION:
            entries = list(obj.potion_entries.all())
            template_attr, type_label = "potion_template", "potion"
        else:
            entries = list(obj.item_entries.all())
            template_attr, type_label = "item_template", "item"

        total = sum(entry.chance for entry in entries) or 1
        rewards = []
        for entry in entries:
            template = getattr(entry, template_attr)
            reward = {
                "type": type_label,
                "template_id": template.id,
                "name": localized_name(template, locale),
                "chance": entry.chance,
                "chance_percent": round(entry.chance / total * 100, 1),
                "media": media_payload(getattr(template, "media", None), self.context),
            }
            if type_label == "item":
                reward["rarity_key"] = template.rarity_key
            rewards.append(reward)
        return rewards


class BuyShopOfferRequestSerializer(serializers.Serializer):
    """Сериализатор тела запроса покупки: только количество и валюта."""

    purchase_count = serializers.IntegerField(min_value=1, default=1)
    payment_currency = serializers.ChoiceField(choices=["money_copper", "premium_currency"])


class ShopPurchaseSerializer(serializers.Serializer):
    """Сериализатор записи истории покупки в магазине."""

    id = serializers.IntegerField()
    offer_id = serializers.IntegerField()
    offer_name = serializers.SerializerMethodField()
    purchase_count = serializers.IntegerField()
    payment_currency = serializers.CharField()
    unit_price = serializers.IntegerField(source="unit_price_snapshot")
    total_price = serializers.IntegerField(source="total_price_snapshot")
    reward_kind = serializers.CharField(source="reward_kind_snapshot")
    delivery_mode = serializers.CharField(source="delivery_mode_snapshot")
    quantity = serializers.IntegerField(source="quantity_snapshot")
    result = serializers.JSONField(source="result_payload")
    created_at = serializers.DateTimeField()

    def get_offer_name(self, obj) -> str:
        return _localized(obj.offer.name_i18n, serializer_locale(self.context))
