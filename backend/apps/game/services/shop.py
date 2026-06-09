from __future__ import annotations

from collections import Counter

from django.db import transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    MoneyTransaction,
    ShopOffer,
    ShopPurchase,
    UserItem,
)

from .loot import generate_item_instance
from .probabilities import weighted_choice
from .shop_rewards import reward_descriptor
from .wallets import all_balances, get_wallet


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

        descriptor = reward_descriptor(offer.reward_kind)
        if descriptor is None:
            raise serializers.ValidationError(message("shop_offer_misconfigured", locale))

        entries = list(
            getattr(offer, descriptor.related_name).select_related(descriptor.template_attr).all()
        )

        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            if len(entries) != 1:
                raise serializers.ValidationError(message("shop_offer_misconfigured", locale))
        else:  # chest
            if len(entries) < 1:
                raise serializers.ValidationError(message("shop_offer_misconfigured", locale))
        return entries

    @classmethod
    def _grant_rewards(cls, *, offer, entries, character, user, total_rewards) -> dict:
        """Прокатывает и выдаёт награды по дескриптору вида (склад либо предмет)."""

        descriptor = reward_descriptor(offer.reward_kind)
        if descriptor.stackable:
            return cls._grant_storage(
                offer=offer,
                entries=entries,
                character=character,
                total_rewards=total_rewards,
                descriptor=descriptor,
            )
        return cls._grant_items(
            offer=offer,
            entries=entries,
            character=character,
            user=user,
            total_rewards=total_rewards,
            descriptor=descriptor,
        )

    @staticmethod
    def _roll_counter(offer, entries, total_rewards, template_attr) -> Counter:
        """Группирует прокатки наград в Counter по идентификатору шаблона."""

        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            return Counter({getattr(entries[0], template_attr): total_rewards})
        weighted = [(entry, entry.chance) for entry in entries]
        rolls = [weighted_choice(weighted) for _ in range(total_rewards)]
        return Counter(getattr(entry, template_attr) for entry in rolls)

    @classmethod
    def _grant_storage(cls, *, offer, entries, character, total_rewards, descriptor) -> dict:
        """Выдаёт стекируемые награды (ингредиенты/зелья) на склад героя."""

        storage_model = descriptor.storage_model
        storage_fk = descriptor.storage_fk
        payload_key = descriptor.payload_key
        counter = cls._roll_counter(offer, entries, total_rewards, descriptor.template_id_attr)

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
    def _grant_items(cls, *, offer, entries, character, user, total_rewards, descriptor) -> dict:
        """Прокатывает и создаёт уникальные предметы пользователя одним bulk_create."""

        template_attr = descriptor.template_attr
        if offer.delivery_mode == ShopOffer.DeliveryMode.SINGLE:
            templates = [getattr(entries[0], template_attr) for _ in range(total_rewards)]
        else:
            weighted = [(entry, entry.chance) for entry in entries]
            templates = [getattr(weighted_choice(weighted), template_attr) for _ in range(total_rewards)]

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
            descriptor.payload_key: [
                {
                    "user_item_id": item.id,
                    "template_id": item.template_id,
                    "rarity_key": item.rarity,
                }
                for item in created
            ]
        }
