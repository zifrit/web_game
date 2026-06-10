from __future__ import annotations

from django.db import models, transaction
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import (
    Character,
    HeroIngredientStorage,
    HeroPotionStorage,
)


class HeroStorage:
    """Единая точка изменения количества на складе героя (ингредиенты, зелья).

    Зеркалит дисциплину кошелька (apps.game.services.wallets), но склад — не
    валюта: леджера нет, движения не аудируются. От кошелька берём только
    самоблокировку строки склада и инвариант неотрицательности; глаголы —
    deposit/withdraw, а не grant/charge. Возвращаем строку склада с актуальным
    count, а не запись леджера.
    """

    def __init__(self, model: type[models.Model], fk_field: str):
        self._model = model
        self._fk = fk_field

    @transaction.atomic
    def deposit(self, character: Character, item_id: int, quantity: int):
        """Транзакционно кладёт предметы на склад героя, инкрементируя count."""

        quantity = max(int(quantity), 0)
        storage, _ = (
            self._model.objects.select_for_update()
            .get_or_create(character=character, **{f"{self._fk}_id": item_id})
        )
        if quantity:
            storage.count += quantity
            storage.save(update_fields=["count", "updated_at"])
        return storage

    @transaction.atomic
    def withdraw(
        self,
        character: Character,
        item_id: int,
        quantity: int,
        *,
        insufficient_message: str,
        missing_message: str | None = None,
        locale: str = DEFAULT_LOCALE,
    ):
        """Транзакционно списывает предметы со склада, проверяя достаточность.

        Если строки склада нет — бросает missing_message (или insufficient_message,
        если он не задан); если count меньше нужного — insufficient_message.
        Возвращает строку склада с предметом (select_related) и новым count.
        """

        quantity = max(int(quantity), 0)
        try:
            storage = (
                self._model.objects.select_for_update()
                .select_related(self._fk)
                .get(character=character, **{f"{self._fk}_id": item_id})
            )
        except self._model.DoesNotExist as exc:
            key = missing_message or insufficient_message
            raise serializers.ValidationError(message(key, locale)) from exc

        if storage.count < quantity:
            raise serializers.ValidationError(message(insufficient_message, locale))

        if quantity:
            storage.count -= quantity
            storage.save(update_fields=["count", "updated_at"])
        return storage

    def get_count(self, character: Character, item_id: int) -> int:
        """Возвращает актуальное количество предмета на складе героя (0, если нет)."""

        return (
            self._model.objects.filter(
                character=character, **{f"{self._fk}_id": item_id}
            )
            .values_list("count", flat=True)
            .first()
            or 0
        )


INGREDIENT_STORAGE = HeroStorage(HeroIngredientStorage, "ingredient")
POTION_STORAGE = HeroStorage(HeroPotionStorage, "potion")
