from __future__ import annotations

from collections.abc import Iterable, Mapping

from django.db import models, transaction
from django.utils import timezone
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
    def deposit_many(
        self,
        character: Character,
        quantities_by_item_id: Mapping[int, int],
    ) -> dict[int, models.Model]:
        """Транзакционно кладёт несколько предметов одного вида склада герою."""

        quantities = {}
        for raw_item_id, raw_quantity in quantities_by_item_id.items():
            item_id = int(raw_item_id)
            quantity = max(int(raw_quantity), 0)
            if item_id > 0 and quantity > 0:
                quantities[item_id] = quantity
        if not quantities:
            return {}

        item_ids = list(quantities)
        id_field = f"{self._fk}_id"
        existing = {
            getattr(row, id_field): row
            for row in self._model.objects.select_for_update().filter(
                character=character,
                **{f"{id_field}__in": item_ids},
            )
        }

        now = timezone.now()
        to_update = []
        to_create = []
        for item_id, quantity in quantities.items():
            row = existing.get(item_id)
            if row is not None:
                row.count += quantity
                row.updated_at = now
                to_update.append(row)
            else:
                row = self._model(character=character, count=quantity, **{id_field: item_id})
                to_create.append(row)
                existing[item_id] = row

        if to_update:
            self._model.objects.bulk_update(to_update, ["count", "updated_at"])
        if to_create:
            self._model.objects.bulk_create(to_create)
        return existing

    @transaction.atomic
    def deposit_for_characters(
        self,
        characters: Iterable[Character],
        item_id: int,
        quantity: int,
    ) -> int:
        """Транзакционно кладёт один предмет склада нескольким героям."""

        item_id = int(item_id)
        quantity = max(int(quantity), 0)
        characters_by_id = {
            character.id: character
            for character in characters
            if character.id is not None
        }
        if item_id <= 0 or quantity == 0 or not characters_by_id:
            return 0

        character_ids = list(characters_by_id)
        id_field = f"{self._fk}_id"
        existing = {
            row.character_id: row
            for row in self._model.objects.select_for_update().filter(
                character_id__in=character_ids,
                **{id_field: item_id},
            )
        }

        now = timezone.now()
        to_update = []
        to_create = []
        for character_id in character_ids:
            row = existing.get(character_id)
            if row is not None:
                row.count += quantity
                row.updated_at = now
                to_update.append(row)
            else:
                to_create.append(
                    self._model(
                        character_id=character_id,
                        count=quantity,
                        **{id_field: item_id},
                    )
                )

        if to_update:
            self._model.objects.bulk_update(to_update, ["count", "updated_at"])
        if to_create:
            self._model.objects.bulk_create(to_create)
        return len(character_ids)

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
