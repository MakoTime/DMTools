from __future__ import annotations

from typing import Any


def parse_class(element: dict[str, Any]) -> dict[str, Any]:
    """Parse class base fields while preserving autolevels for a later chunk."""
    if element.get("tag") != "class":
        raise ValueError("Expected a class element")

    return {
        "name": get_text(element, "name"),
        "hd": get_text(element, "hd"),
        "proficiency": get_text(element, "proficiency"),
        "numSkills": get_text(element, "numSkills"),
        "armor": get_text(element, "armor"),
        "weapons": get_text(element, "weapons"),
        "tools": get_text(element, "tools"),
        "spellAbility": get_text(element, "spellAbility"),
        "wealth": get_text(element, "wealth"),
        "autolevels": [parse_autolevel(level) for level in find_children(element, "autolevel")],
    }


def get_text(element: dict[str, Any], tag: str) -> str | None:
    for child in element.get("children", []):
        if child.get("tag") == tag:
            return child.get("text")
    return None


def parse_autolevel(element: dict[str, Any]) -> dict[str, Any]:
    return {
        "attributes": dict(element.get("attributes", {})),
        "children": [parse_nested(child) for child in element.get("children", [])],
    }


def parse_nested(element: dict[str, Any]) -> dict[str, Any]:
    return {
        "tag": element.get("tag"),
        "text": element.get("text"),
        "attributes": dict(element.get("attributes", {})),
        "children": [parse_nested(child) for child in element.get("children", [])],
    }


def find_children(element: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    return [child for child in element.get("children", []) if child.get("tag") == tag]