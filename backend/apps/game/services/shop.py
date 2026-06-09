from __future__ import annotations

import random
from collections import Counter
from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    HeroIngredientStorage,
    HeroPotionStorage,
    MoneyTransaction,
    ShopOffer,
    ShopPurchase,
    UserItem,
)

from .loot import generate_item_instance
from .wallets import all_balances, get_wallet


def _weighted_choice(weighted_items: list[tuple[Any, float]]) -> Any:
    """Выбирает элемент из списка пар (элемент, вес) взвешенным случайным броском."""

    total = sum(float(value) for _, value in weighted_items)
    roll = random.uniform(0, total)
    upto = 0.0
    for item, value in weighted_items:
        upto += float(value)
        if roll <= upto:
            return item
    return weighted_items[-1][0]


class ShopService:
    """Сервис покупок в системном магазине: оплата, прокатка наград, история."""

    @classmethod
    @transaction.atomic
    def buy_offer(cls, *, user, offer_id: int, purchase_count: int = 1, payment_currency: str, locale=DEFAULT_LOCALE) -> dict:
        """Покупает предложение выбранной валютой, выдаёт награды, пишет историю."""

        # 1. Валидация количества покупок.
        purchase_count = int(purchase_count)
        if purchase_count < 1:
            raise serializers.ValidationError(message("shop_invalid_purchase_count", locale))

        # 2. Блокировка активного предложения.
        try:
            offer = ShopOffer.objects.select_for_update().get(id=offer_id, is_active=True)
        except ShopOffer.DoesNotExist as exc:
            raise serializers.ValidationError(message("shop_offer_not_found", locale)) from exc

        # 3. Блокировка героя (баланс валюты блокирует её кошелёк при списании).
        try:
            character = Character.objects.select_for_update().get(user=user)
        except Character.DoesNotExist as exc:
            raise serializers.ValidationError(message("no_character", locale)) from exc

        # 4. Валидация валюты и расчёт цены.
        unit_price = cls._resolve_unit_price(offer, payment_currency, locale)
        total_price = unit_price * purchase_count

        # 5. Подготовка записей наград и валидация конфигурации предложения.
        entries = cls._offer_entries(offer, locale)

        total_rewards = offer.quantity * purchase_count

        # 6. Списание через кошелёк выбранной валюты (значение reason общее для леджеров).
        get_wallet(payment_currency).charge(
            user,
            amount=total_price,
            reason=MoneyTransaction.Reason.SHOP_PURCHASE,
            metadata={"offer_id": offer.id, "purchase_count": purchase_count},
            insufficient_message="shop_not_enough_money",
            locale=locale,
        )

        # 7. Выдача наград.
        result_payload = cls._grant_rewards(
            offer=offer,
            entries=entries,
            character=character,
            user=user,
            total_rewards=total_rewards,
        )

        # 8. История покупки со снимком условий.
        purchase = ShopPurchase.objects.create(
            user=user,
            character=character,
            offer=offer,
            purchase_count=purchase_count,
            payment_currency=payment_currency,
            unit_price_snapshot=unit_price,
            total_price_snapshot=total_price,
            reward_kind_snapshot=offer.reward_kind,
            delivery_mode_snapshot=offer.delivery_mode,
            quantity_snapshot=offer.quantity,
            result_payload=result_payload,
        )

        return {
            "purchase": purchase,
            "balances": all_balances(user),
        }

    # --- внутренние помощники ---

    # Поле цены предложения для каждой валюты оплаты.
    _PRICE_FIELD = {
        ShopPurchase.PaymentCurrency.MONEY_COPPER: "price_money_copper",
        ShopPurchase.PaymentCurrency.PREMIUM_CURRENCY: "price_premium_currency",
    }

    @classmethod
    def _resolve_unit_price(cls, offer: ShopOffer, payment_currency: str, locale: str) -> int:
        """Возвращает цену предложения в выбранной валюте или бросает ошибку."""

        field = cls._PRICE_FIELD.get(payment_currency)
        price = getattr(offer, field) if field else None
        if price is None:
            raise serializers.ValidationError(message("shop_price_unavailable", locale))
        return price

    @staticmethod
    def _offer_entries(offer: ShopOffer, locale: str) -> list:
        """Возвращает список записей-наград и проверяет правила количества записей."""

        if offer.reward_kind == ShopOffer.RewardKind.INGREDIENT:
            entries = list(offer.ingredient_entries.select_related("ingredient_template").all())
        elif offer.reward_kind == ShopOffer.RewardKind.POTION:
            entries = list(offer.potion_entries.select_related("potion_template").all())
        elif offer.reward_kind == ShopOffer.RewardKind.ITEM:
            entries = list(offer.item_entries.select_related("item_template").all())
        else:
            raise serializers.ValidationError(message("shop_offer_misconfigured", locale))

        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            if len(entries) != 1:
                raise serializers.ValidationError(message("shop_offer_misconfigured", locale))
        else:  # chest
            if len(entries) < 1:
                raise serializers.ValidationError(message("shop_offer_misconfigured", locale))
        return entries

    @classmethod
    def _grant_rewards(cls, *, offer, entries, character, user, total_rewards) -> dict:
        """Прокатывает и выдаёт награды в зависимости от вида и режима предложения."""

        if offer.reward_kind == ShopOffer.RewardKind.INGREDIENT:
            return cls._grant_storage(
                offer=offer,
                entries=entries,
                character=character,
                total_rewards=total_rewards,
                template_attr="ingredient_template_id",
                storage_model=HeroIngredientStorage,
                storage_fk="ingredient_id",
                payload_key="ingredients",
            )
        if offer.reward_kind == ShopOffer.RewardKind.POTION:
            return cls._grant_storage(
                offer=offer,
                entries=entries,
                character=character,
                total_rewards=total_rewards,
                template_attr="potion_template_id",
                storage_model=HeroPotionStorage,
                storage_fk="potion_id",
                payload_key="potions",
            )
        return cls._grant_items(
            offer=offer,
            entries=entries,
            character=character,
            user=user,
            total_rewards=total_rewards,
        )

    @staticmethod
    def _roll_counter(offer, entries, total_rewards, template_attr) -> Counter:
        """Группирует прокатки наград в Counter по идентификатору шаблона."""

        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            return Counter({getattr(entries[0], template_attr): total_rewards})
        weighted = [(entry, entry.chance) for entry in entries]
        rolls = [_weighted_choice(weighted) for _ in range(total_rewards)]
        return Counter(getattr(entry, template_attr) for entry in rolls)

    @classmethod
    def _grant_storage(cls, *, offer, entries, character, total_rewards, template_attr, storage_model, storage_fk, payload_key) -> dict:
        """Выдаёт стекируемые награды (ингредиенты/зелья) на склад героя."""

        counter = cls._roll_counter(offer, entries, total_rewards, template_attr)

        existing = {
            getattr(row, storage_fk): row
            for row in storage_model.objects.select_for_update().filter(
                character=character, **{f"{storage_fk}__in": list(counter.keys())}
            )
        }

        to_update = []
        to_create = []
        for template_id, qty in counter.items():
            row = existing.get(template_id)
            if row is not None:
                row.count += qty
                to_update.append(row)
            else:
                to_create.append(storage_model(character=character, count=qty, **{storage_fk: template_id}))

        if to_update:
            storage_model.objects.bulk_update(to_update, ["count", "updated_at"])
        if to_create:
            storage_model.objects.bulk_create(to_create)

        return {
            payload_key: [
                {"template_id": template_id, "quantity": qty}
                for template_id, qty in counter.items()
            ]
        }

    @classmethod
    def _grant_items(cls, *, offer, entries, character, user, total_rewards) -> dict:
        """Прокатывает и создаёт уникальные предметы пользователя одним bulk_create."""

        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            templates = [entries[0].item_template for _ in range(total_rewards)]
        else:
            weighted = [(entry, entry.chance) for entry in entries]
            templates = [_weighted_choice(weighted).item_template for _ in range(total_rewards)]

        drafts = [generate_item_instance(template) for template in templates]
        items = [
            UserItem(
                owner_user=user,
                source_character=character,
                template_id=draft["template_id"],
                name=draft["name"],
                slot=draft["slot"],
                item_type=draft["item_type"],
                rarity=draft["rarity"],
                item_level=draft["item_level"],
                stats=draft["stats"],
                durability_current=draft["durability_current"],
                durability_max=draft["durability_max"],
            )
            for draft in drafts
        ]
        created = UserItem.objects.bulk_create(items)

        return {
            "items": [
                {
                    "user_item_id": item.id,
                    "template_id": item.template_id,
                    "rarity_key": item.rarity,
                }
                for item in created
            ]
        }
