"""Загрузка стартового набора SVG-лиц карт мини-игры из backend-каталога.

Файлы лежат в `apps/game/data/memory_faces/*.svg` и являются каноническим
источником сидов и data-миграции (backend-контейнер не имеет доступа к
`frontend/public`).
"""

from __future__ import annotations

from pathlib import Path

FACES_DIR = Path(__file__).resolve().parent.parent / "data" / "memory_faces"


def load_seed_card_faces() -> list[dict]:
    """Возвращает список лиц `{code, name, svg_markup, sort_order}` из каталога."""

    faces: list[dict] = []
    for index, path in enumerate(sorted(FACES_DIR.glob("*.svg"))):
        code = path.stem
        faces.append(
            {
                "code": code,
                "name": code.capitalize(),
                "svg_markup": path.read_text(encoding="utf-8").strip(),
                "sort_order": index,
            }
        )
    return faces
