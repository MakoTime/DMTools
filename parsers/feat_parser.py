from __future__ import annotations

from typing import Any


def parse_feat(element: dict[str, Any]) -> dict[str, Any]:
    """Parse a normalized XML feat element without schema interpretation."""
    if element.get("tag") != "feat":
        raise ValueError("Expected a feat element")

    return {
        "name": get_text(element, "name"),
        "prerequisite": get_text(element, "prerequisite"),
        "text": get_text_elements(element, "text"),
        "modifiers": [
            {
                "category": modifier.get("attributes", {}).get("category"),
                "attributes": dict(modifier.get("attributes", {})),
                "text": modifier.get("text"),
            }
            for modifier in find_children(element, "modifier")
        ],
    }


def get_text(element: dict[str, Any], tag: str) -> str | None:
    for child in find_children(element, tag):
        return child.get("text")
    return None


def get_text_elements(element: dict[str, Any], tag: str) -> list[str | None]:
    return [child.get("text") for child in find_children(element, tag)]


def find_children(element: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    return [child for child in element.get("children", []) if child.get("tag") == tag]