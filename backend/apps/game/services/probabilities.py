from __future__ import annotations

import random
from typing import Any


def weighted_choice(weighted_items: list[tuple[Any, float]]) -> Any:
    """Выбирает элемент из списка пар (элемент, вес) случайным взвешенным броском."""

    total = sum(float(value) for _, value in weighted_items)
    roll = random.uniform(0, total)
    upto = 0.0
    for item, value in weighted_items:
        upto += float(value)
        if roll <= upto:
            return item
    return weighted_items[-1][0]
