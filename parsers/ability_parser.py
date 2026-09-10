from __future__ import annotations

from typing import Any

from .spell_parser import parse_spell


def parse_ability(element: dict[str, Any]) -> dict[str, Any]:
    """Preserve the spell-shaped XML fields used by custom abilities."""
    return parse_spell(element)