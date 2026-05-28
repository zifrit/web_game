from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RankConfig:
    key: str
    label: str
    min_level: int
    max_level: int
    stat_multiplier: float
    economy_multiplier: str
    min_stats_count: int
    max_stats_count: int


RANKS: tuple[RankConfig, ...] = (
    RankConfig("f", "F", 1, 10, 1.0, "1.00", 1, 1),
    RankConfig("e", "E", 11, 20, 1.25, "1.25", 1, 2),
    RankConfig("d", "D", 21, 30, 1.6, "1.60", 2, 2),
    RankConfig("c", "C", 31, 40, 2.0, "2.00", 2, 3),
    RankConfig("b", "B", 41, 50, 2.5, "2.50", 3, 3),
    RankConfig("a", "A", 51, 60, 3.1, "3.10", 3, 4),
    RankConfig("s", "S", 61, 70, 3.8, "3.80", 4, 4),
    RankConfig("ex", "EX", 71, 80, 4.6, "4.60", 4, 5),
)

RANK_BY_KEY = {rank.key: rank for rank in RANKS}
MAX_RANK_LEVEL = RANKS[-1].max_level


def rank_for_level(level: int) -> RankConfig:
    """Return the rank bucket for a numeric hero or item level."""

    normalized = max(1, min(int(level), MAX_RANK_LEVEL))
    for rank in RANKS:
        if rank.min_level <= normalized <= rank.max_level:
            return rank
    return RANKS[-1]
