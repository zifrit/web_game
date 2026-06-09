from rest_framework import serializers


class CurrencyExchangeOfferSerializer(serializers.Serializer):
    """Сериализатор предложения обмена премиум-валюты на монеты."""

    id = serializers.IntegerField()
    premium_cost = serializers.IntegerField()
    money_copper_reward = serializers.IntegerField()


class CurrencyExchangeOfferDetailSerializer(CurrencyExchangeOfferSerializer):
    """Детальный сериализатор предложения обмена с признаком активности."""

    is_active = serializers.BooleanField()


class CurrencyExchangeTransactionSerializer(serializers.Serializer):
    """Сериализатор записи обмена валюты для истории."""

    id = serializers.IntegerField()
    premium_spent = serializers.IntegerField()
    money_copper_received = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class PremiumCurrencyTransactionSerializer(serializers.Serializer):
    """Сериализатор записи леджера премиум-валюты для истории."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()
    reason = serializers.CharField()
    balance_after = serializers.IntegerField()
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()
