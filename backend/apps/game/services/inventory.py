from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, message
from apps.game.models import Character, RepairTransaction, UserItem

from .dungeon_runs import DungeonRunService
from .formulas import GameFormulaService, STAT_KEYS
from .loot import item_allowed_for_character


EQUIPMENT_SLOTS = ("weapon", "helmet", "armor", "boots", "ring")


class InventoryService:
    """Сервис правил инвентаря, экипировки и ремонта предметов."""

    @staticmethod
    def can_equip(item: UserItem, character: Character) -> bool:
        """Проверяет владение, прочность, слот и классовые ограничения предмета."""

        if item.owner_user_id != character.user_id:
            return False
        if item.is_broken:
            return False
        if item.slot not in EQUIPMENT_SLOTS:
            return False
        return item_allowed_for_character(item, character)

    @staticmethod
    def equipment_summary(character: Character) -> dict[str, float]:
        """Суммирует вклад несломанной экипировки в характеристики героя."""

        stats = {key: 0.0 for key in STAT_KEYS}
        for item in character.equipped_items.all():
            if item.is_broken:
                continue
            for key, value in (item.stats or {}).items():
                if key in stats:
                    stats[key] += float(value)
        stats["power"] = GameFormulaService.power_from_stats(stats)
        return {key: round(value, 2) for key, value in stats.items()}

    @classmethod
    def _owned_items(cls, user, item_ids: list[int] | tuple[int, ...], for_update: bool = False) -> QuerySet[UserItem]:
        """Возвращает queryset выбранных предметов текущего пользователя."""

        qs = UserItem.objects.filter(owner_user=user, pk__in=item_ids).select_related("template")
        if for_update:
            qs = qs.select_for_update()
        return qs

    @staticmethod
    def _repair_preview_payload(user, items: list[UserItem]) -> dict[str, Any]:
        repairable = [item for item in items if item.durability_current < item.durability_max]
        total_missing = sum(max(item.durability_max - item.durability_current, 0) for item in repairable)
        total_cost = sum(GameFormulaService.repair_cost(item) for item in repairable)
        return {
            "item_ids": [item.id for item in repairable],
            "items_count": len(repairable),
            "durability_missing": total_missing,
            "repair_cost_copper": total_cost,
            "user_money_copper": user.money_copper,
            "can_repair": len(repairable) > 0 and user.money_copper >= total_cost,
        }

    @staticmethod
    def _destroy_preview_payload(user, items: list[UserItem]) -> dict[str, Any]:
        refund = sum(GameFormulaService.destroy_refund(item) for item in items)
        return {
            "item_ids": [item.id for item in items],
            "items_count": len(items),
            "refund_copper": refund,
            "user_money_copper": user.money_copper,
            "can_destroy": len(items) > 0,
        }

    @classmethod
    def repair_preview(cls, user, item_ids: list[int] | tuple[int, ...]) -> dict[str, Any]:
        """Возвращает массовый расчёт ремонта без изменения баланса и прочности."""

        qs = cls._owned_items(user, item_ids)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", DEFAULT_LOCALE))
        return cls._repair_preview_payload(user, items)

    @classmethod
    def destroy_preview(cls, user, item_ids: list[int] | tuple[int, ...]) -> dict[str, Any]:
        """Возвращает массовый расчёт возврата за уничтожение предметов."""

        qs = cls._owned_items(user, item_ids)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", DEFAULT_LOCALE))
        return cls._destroy_preview_payload(user, items)

    @classmethod
    @transaction.atomic
    def repair_items(cls, user, item_ids: list[int] | tuple[int, ...], locale=DEFAULT_LOCALE) -> dict[str, Any]:
        """Транзакционно ремонтирует выбранные предметы и списывает общую стоимость."""

        user = type(user).objects.select_for_update().get(pk=user.pk)
        qs = cls._owned_items(user, item_ids, for_update=True)
        items = list(qs)
        repairable = [item for item in items if item.durability_current < item.durability_max]
        if not repairable:
            raise serializers.ValidationError(message("no_repair_needed", locale))
        cost = sum(GameFormulaService.repair_cost(item) for item in repairable)
        if user.money_copper < cost:
            raise serializers.ValidationError(message("not_enough_money_repair", locale))

        user.money_copper -= cost
        user.save(update_fields=["money_copper", "updated_at"])
        repair_transactions = []
        for item in repairable:
            before = item.durability_current
            item_cost = GameFormulaService.repair_cost(item)
            item.durability_current = item.durability_max
            item.save(update_fields=["durability_current", "updated_at"])
            repair_transactions.append(
                RepairTransaction(
                    user=user,
                    item=item,
                    cost_copper=item_cost,
                    durability_before=before,
                    durability_after=item.durability_current,
                )
            )
        RepairTransaction.objects.bulk_create(repair_transactions)
        return {
            "success": True,
            "item_ids": [item.id for item in repairable],
            "items_count": len(repairable),
            "repair_cost_copper": cost,
            "remaining_money_copper": user.money_copper,
        }

    @classmethod
    def repair(cls, user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, int, int]:
        """Совместимая одиночная обёртка поверх массового ремонта."""

        result = cls.repair_items(user, [item_id], locale=locale)
        item = UserItem.objects.get(pk=item_id, owner_user=user)
        return item, result["repair_cost_copper"], result["remaining_money_copper"]

    @classmethod
    @transaction.atomic
    def destroy_items(cls, user, item_ids: list[int] | tuple[int, ...], locale=DEFAULT_LOCALE) -> dict[str, Any]:
        """Транзакционно удаляет выбранные предметы и начисляет возврат."""

        user = type(user).objects.select_for_update().get(pk=user.pk)
        qs = cls._owned_items(user, item_ids, for_update=True)
        items = list(qs)
        if not items:
            raise serializers.ValidationError(message("no_items_selected", locale))
        refund = sum(GameFormulaService.destroy_refund(item) for item in items)
        destroyed_ids = [item.id for item in items]
        user.money_copper += refund
        user.save(update_fields=["money_copper", "updated_at"])
        UserItem.objects.filter(pk__in=destroyed_ids, owner_user=user).delete()
        return {
            "success": True,
            "item_ids": destroyed_ids,
            "items_count": len(destroyed_ids),
            "refund_copper": refund,
            "remaining_money_copper": user.money_copper,
        }

    @staticmethod
    @transaction.atomic
    def equip(user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, UserItem | None, Character]:
        """Транзакционно экипирует предмет и возвращает снятый предмет слота."""

        character = DungeonRunService._get_character(user, locale)
        character = Character.objects.select_for_update().select_related("character_class").get(pk=character.pk)
        item = UserItem.objects.select_for_update().select_related("template").get(pk=item_id, owner_user=user)
        if item.is_broken:
            raise serializers.ValidationError(message("broken_item_equip", locale))
        if not item_allowed_for_character(item, character):
            raise serializers.ValidationError(message("class_not_allowed", locale))

        replaced_item = (
            UserItem.objects.select_for_update()
            .select_related("template")
            .filter(equipped_character=character, slot=item.slot)
            .exclude(pk=item.pk)
            .first()
        )
        if replaced_item:
            replaced_item.equipped_character = None
            replaced_item.save(update_fields=["equipped_character", "updated_at"])

        item.equipped_character = character
        try:
            item.save(update_fields=["equipped_character", "updated_at"])
        except IntegrityError as exc:
            raise serializers.ValidationError(message("equip_failed", locale)) from exc
        return item, replaced_item, character

    @staticmethod
    @transaction.atomic
    def unequip(user, item_id: int, locale=DEFAULT_LOCALE) -> tuple[UserItem, Character]:
        """Транзакционно снимает предмет с героя и возвращает предмет с героем."""

        character = DungeonRunService._get_character(user, locale)
        item = UserItem.objects.select_for_update().select_related("template").get(pk=item_id, owner_user=user)
        if item.equipped_character_id == character.id:
            item.equipped_character = None
            item.save(update_fields=["equipped_character", "updated_at"])
        character = Character.objects.select_related("character_class").get(pk=character.pk)
        return item, character
