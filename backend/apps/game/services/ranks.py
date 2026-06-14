from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RankConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    min_level: int
    max_level: int
    stat_multiplier: float
    economy_multiplier: str
    min_stats_count: int
    max_stats_count: int


RANKS: tuple[RankConfig, ...] = (
    RankConfig(
        key="f",
        label="F",
        min_level=1,
        max_level=10,
        stat_multiplier=1.0,
        economy_multiplier="1.00",
        min_stats_count=1,
        max_stats_count=1,
    ),
    RankConfig(
        key="e",
        label="E",
        min_level=11,
        max_level=20,
        stat_multiplier=1.15,
        economy_multiplier="1.25",
        min_stats_count=1,
        max_stats_count=2,
    ),
    RankConfig(
        key="d",
        label="D",
        min_level=21,
        max_level=30,
        stat_multiplier=1.35,
        economy_multiplier="1.60",
        min_stats_count=2,
        max_stats_count=2,
    ),
    RankConfig(
        key="c",
        label="C",
        min_level=31,
        max_level=40,
        stat_multiplier=1.6,
        economy_multiplier="2.00",
        min_stats_count=2,
        max_stats_count=3,
    ),
    RankConfig(
        key="b",
        label="B",
        min_level=41,
        max_level=50,
        stat_multiplier=1.9,
        economy_multiplier="2.50",
        min_stats_count=3,
        max_stats_count=3,
    ),
    RankConfig(
        key="a",
        label="A",
        min_level=51,
        max_level=60,
        stat_multiplier=2.25,
        economy_multiplier="3.10",
        min_stats_count=3,
        max_stats_count=4,
    ),
    RankConfig(
        key="s",
        label="S",
        min_level=61,
        max_level=70,
        stat_multiplier=2.65,
        economy_multiplier="3.80",
        min_stats_count=4,
        max_stats_count=4,
    ),
    RankConfig(
        key="ex",
        label="EX",
        min_level=71,
        max_level=80,
        stat_multiplier=3.1,
        economy_multiplier="4.60",
        min_stats_count=4,
        max_stats_count=5,
    ),
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
