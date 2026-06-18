from __future__ import annotations

from dataclasses import dataclass

from apps.game.models import ShopOffer

from .storages import HeroStorage, INGREDIENT_STORAGE, POTION_STORAGE


@dataclass(frozen=True)
class RewardKindDescriptor:
    """Единое описание вида награды магазина: связи, шаблоны, способ выдачи.

    Один дескриптор на RewardKind — единственное место, где объявляется, какой
    related-набор у предложения, как достаётся шаблон, и как награда выдаётся
    (стек на склад героя либо уникальный предмет пользователя).
    """

    related_name: str            # related-набор записей на ShopOffer
    template_attr: str           # FK-атрибут шаблона на записи (объект)
    type_label: str              # презентационная метка ("ingredient"/"potion"/"item")
    payload_key: str             # ключ результата выдачи в result_payload
    stackable: bool              # True → склад героя; False → уникальный UserItem
    storage: HeroStorage | None = None  # шов склада героя (только для stackable)

    @property
    def template_id_attr(self) -> str:
        """Атрибут *_id шаблона на записи (для группировки прокаток по id)."""

        return f"{self.template_attr}_id"


REWARD_KINDS: dict[str, RewardKindDescriptor] = {
    ShopOffer.RewardKind.INGREDIENT: RewardKindDescriptor(
        related_name="ingredient_entries",
        template_attr="ingredient_template",
        type_label="ingredient",
        payload_key="ingredients",
        stackable=True,
        storage=INGREDIENT_STORAGE,
    ),
    ShopOffer.RewardKind.POTION: RewardKindDescriptor(
        related_name="potion_entries",
        template_attr="potion_template",
        type_label="potion",
        payload_key="potions",
        stackable=True,
        storage=POTION_STORAGE,
    ),
    ShopOffer.RewardKind.ITEM: RewardKindDescriptor(
        related_name="item_entries",
        template_attr="item_template",
        type_label="item",
        payload_key="items",
        stackable=False,
    ),
}


def reward_descriptor(reward_kind: str) -> RewardKindDescriptor | None:
    """Возвращает дескриптор вида награды или None для неизвестного вида."""

    return REWARD_KINDS.get(reward_kind)
