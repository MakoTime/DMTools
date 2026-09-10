from __future__ import annotations

from typing import Any


def parse_background(element: dict[str, Any]) -> dict[str, Any]:
    """Parse a normalized XML background element without schema interpretation."""
    if element.get("tag") != "background":
        raise ValueError("Expected a background element")

    return {
        "name": get_text(element, "name"),
        "proficiency": get_text(element, "proficiency"),
        "traits": [
            {
                "name": get_text(trait, "name"),
                "text": get_text_elements(trait, "text"),
            }
            for trait in find_children(element, "trait")
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