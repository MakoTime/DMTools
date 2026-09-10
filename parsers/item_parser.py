from __future__ import annotations

from typing import Any


def parse_item(element: dict[str, Any]) -> dict[str, Any]:
    """
    Parse a normalized XML item element into a structured dictionary.

    The parser preserves repeated descriptive text and modifier metadata. It
    does not interpret item categories, magical properties, or modifier text.
    """
    if element.get("tag") != "item":
        raise ValueError("Expected an item element")

    return {
        "name": get_text(element, "name"),
        "type": get_text(element, "type"),
        "magic": get_text(element, "magic"),
        "detail": get_text(element, "detail"),
        "weight": get_text(element, "weight"),
        "value": get_text(element, "value"),
        "ac": get_text(element, "ac"),
        "dmg1": get_text(element, "dmg1"),
        "dmg2": get_text(element, "dmg2"),
        "dmgType": get_text(element, "dmgType"),
        "range": get_text(element, "range"),
        "stealth": get_text(element, "stealth"),
        "strength": get_text(element, "strength"),
        "text": get_text_elements(element, "text"),
        "property": get_text_elements(element, "property"),
        "roll": get_text_elements(element, "roll"),
        "attributes": dict(element.get("attributes", {})),
        "modifiers": parse_modifiers(element),
    }


def parse_modifiers(element: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve item modifier attributes and source text."""
    return [
        {
            "category": modifier.get("attributes", {}).get("category"),
            "attributes": dict(modifier.get("attributes", {})),
            "text": modifier.get("text"),
        }
        for modifier in find_children(element, "modifier")
    ]


def get_text(element: dict[str, Any], tag: str) -> str | None:
    """Get the text of the first direct child with the given tag."""
    for child in find_children(element, tag):
        return child.get("text")

    return None


def get_text_elements(
    element: dict[str, Any],
    tag: str,
) -> list[str | None]:
    """Get the text from all direct children with the given tag."""
    return [
        child.get("text")
        for child in find_children(element, tag)
    ]


def find_children(
    element: dict[str, Any],
    tag: str,
) -> list[dict[str, Any]]:
    """Return all direct children with the given tag."""
    return [
        child
        for child in element.get("children", [])
        if child.get("tag") == tag
    ]