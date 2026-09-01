from __future__ import annotations

from typing import Any

def parse_spell(element: dict[str, Any]) -> dict[str, Any]:
    if element.get("tag") != "spell":
        raise ValueError("Element is not a spell")
    return {
        "name": get_text(element, "name"),
        "level": get_text(element, "level"),
        "school": get_text(element, "school"),
        "ritual": get_text(element, "ritual"),
        "time": get_text(element, "time"),
        "range": get_text(element, "range"),
        "components": get_text(element, "components"),
        "duration": get_text(element, "duration"),
        "classes": get_text(element, "classes"),
        "text": get_text_elements(element, "text"),
        "roll": get_text_elements(element, "roll"),
    }
    
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