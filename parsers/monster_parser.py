from __future__ import annotations

from typing import Any


def parse_monster(element: dict[str, Any]) -> dict[str, Any]:
    """
    Parse a normalized XML monster element into a structured dictionary.
    """
    if element.get("tag") != "monster":
        raise ValueError("Expected a monster element")

    return {
        "name": get_text(element, "name"),
        "size": get_text(element, "size"),
        "type": get_text(element, "type"),
        "alignment": get_text(element, "alignment"),
        "ac": get_text(element, "ac"),
        "hp": get_text(element, "hp"),
        "speed": get_text(element, "speed"),
        "ability_scores": parse_ability_scores(element),
        "saves": get_text(element, "save"),
        "skills": get_text(element, "skill"),
        "resistances": get_text(element, "resist"),
        "vulnerabilities": get_text(element, "vulnerable"),
        "immunities": get_text(element, "immune"),
        "condition_immunities": get_text(element, "conditionImmune"),
        "senses": get_text(element, "senses"),
        "passive": get_text(element, "passive"),
        "languages": get_text(element, "languages"),
        "cr": get_text(element, "cr"),
        "traits": parse_named_entries(element, "trait"),
        "actions": parse_actions(element),
        "legendary_actions": parse_named_entries(element, "legendary"),
        "spells": parse_csv_text(element, "spells"),
        "slots": parse_slots(element),
        "environment": parse_csv_text(element, "environment"),
    }


def parse_ability_scores(element: dict[str, Any]) -> dict[str, str | None]:
    """
    Parse the six standard monster ability scores.
    """
    abilities = ("str", "dex", "con", "int", "wis", "cha")

    return {
        ability: get_text(element, ability)
        for ability in abilities
    }


def parse_named_entries(
    element: dict[str, Any],
    tag: str,
) -> list[dict[str, Any]]:
    """
    Parse entries such as traits and legendary actions.

    Each entry contains its name, text blocks, and any child data.
    """
    entries = []

    for child in find_children(element, tag):
        entries.append({
            "name": get_text_from_element(child, "name"),
            "text": get_text_elements(child, "text"),
            "children": [
                grandchild
                for grandchild in child.get("children", [])
                if grandchild.get("tag") not in {"name", "text"}
            ],
        })

    return entries


def parse_actions(element: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Parse monster actions, including optional attack data.
    """
    actions = []

    for action in find_children(element, "action"):
        attacks = []

        for attack in find_children(action, "attack"):
            attacks.append(parse_attack(attack))

        actions.append({
            "name": get_text_from_element(action, "name"),
            "text": get_text_elements(action, "text"),
            "attacks": attacks,
        })

    return actions


def parse_attack(element: dict[str, Any]) -> dict[str, Any]:
    """
    Parse an <attack> element.

    XML format:
        <attack>Name|bonus|damage</attack>
    """
    text = element.get("text")

    if not text:
        return {
            "name": None,
            "bonus": None,
            "damage": None,
        }

    parts = [part.strip() for part in text.split("|")]

    while len(parts) < 3:
        parts.append(None)

    return {
        "name": parts[0],
        "bonus": parts[1] or None,
        "damage": parts[2] or None,
    }


def parse_slots(element: dict[str, Any]) -> list[int]:
    """
    Parse spell slot data.

    XML format:
        <slots>4, 3, 3, 3, 3, 1, 1, 1, 1</slots>
    """
    text = get_text(element, "slots")

    if not text:
        return []

    return [int(value.strip()) for value in text.split(",")]


def parse_csv_text(
    element: dict[str, Any],
    tag: str,
) -> list[str]:
    """
    Parse comma-separated XML text into a list.

    Empty elements return an empty list.
    """
    text = get_text(element, tag)

    if not text:
        return []

    return [value.strip() for value in text.split(",") if value.strip()]


def get_text(
    element: dict[str, Any],
    tag: str,
) -> str | None:
    """
    Get the text of the first direct child with the given tag.
    """
    child = find_child(element, tag)

    if child is None:
        return None

    return child.get("text")


def get_text_from_element(
    element: dict[str, Any],
    tag: str,
) -> str | None:
    """
    Get the text of the first child with the given tag.
    """
    child = find_child(element, tag)

    if child is None:
        return None

    return child.get("text")


def get_text_elements(
    element: dict[str, Any],
    tag: str,
) -> list[str | None]:
    """
    Get the text from all direct children with the given tag.
    """
    return [
        child.get("text")
        for child in find_children(element, tag)
    ]


def find_child(
    element: dict[str, Any],
    tag: str,
) -> dict[str, Any] | None:
    """
    Find the first direct child with the given tag.
    """
    for child in element.get("children", []):
        if child.get("tag") == tag:
            return child

    return None


def find_children(
    element: dict[str, Any],
    tag: str,
) -> list[dict[str, Any]]:
    """
    Find all direct children with the given tag.
    """
    return [
        child
        for child in element.get("children", [])
        if child.get("tag") == tag
    ]