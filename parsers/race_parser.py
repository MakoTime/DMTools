from __future__ import annotations

from typing import Any


def parse_race(element: dict[str, Any]) -> dict[str, Any]:
    """Parse a normalized XML race element without schema interpretation."""
    if element.get("tag") != "race":
        raise ValueError("Expected a race element")

    return {
        "name": get_text(element, "name"),
        "size": get_text(element, "size"),
        "speed": get_text(element, "speed"),
        "ability": get_text(element, "ability"),
        "spellAbility": get_text(element, "spellAbility"),
        "proficiency": get_text(element, "proficiency"),
        "traits": [parse_trait(trait) for trait in find_children(element, "trait")],
    }


def parse_trait(element: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": get_text(element, "name"),
        "text": get_text_elements(element, "text"),
        "special": get_text_elements(element, "special"),
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
    return [
        child
        for child in element.get("children", [])
        if child.get("tag") == tag
    ]