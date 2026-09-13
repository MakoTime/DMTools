from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SPELL_LEVEL_COLUMNS = tuple(str(level) for level in range(1, 10))

FULL_SPELL_SLOTS = (
    (2,), (3,), (4, 2), (4, 3), (4, 3, 2), (4, 3, 3),
    (4, 3, 3, 1), (4, 3, 3, 2), (4, 3, 3, 3, 1),
    (4, 3, 3, 3, 2), (4, 3, 3, 3, 2, 1), (4, 3, 3, 3, 2, 1),
    (4, 3, 3, 3, 2, 1, 1), (4, 3, 3, 3, 2, 1, 1),
    (4, 3, 3, 3, 2, 1, 1, 1), (4, 3, 3, 3, 2, 1, 1, 1),
    (4, 3, 3, 3, 1, 1, 1, 1, 1), (4, 3, 3, 3, 1, 1, 1, 1, 1),
    (4, 3, 3, 3, 2, 1, 1, 1, 1), (4, 3, 3, 3, 2, 1, 1, 1, 1),
)

SUBCLASS_FEATURE_LABELS = {
    "barbarian": "Primal Path",
    "bard": "Bard College",
    "cleric": "Divine Domain",
    "druid": "Druid Circle",
    "fighter": "Martial Archetype",
    "monk": "Monastic Tradition",
    "paladin": "Sacred Oath",
    "ranger": "Ranger Archetype",
    "rogue": "Roguish Archetype",
    "sorcerer": "Sorcerous Origin",
    "warlock": "Otherworldly Patron",
    "wizard": "Arcane Tradition",
    "artificer": "Artificer Specialist",
}


def class_progression_rows(
    payload: Mapping[str, Any], metadata: Mapping[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Build PHB-style class rows from canonical data plus optional display metadata."""
    features_by_level: dict[int, list[str]] = {}
    for feature in payload.get("features", ()):
        if not isinstance(feature, Mapping) or not isinstance(feature.get("level"), int):
            continue
        features_by_level.setdefault(feature["level"], []).append(
            str(feature.get("name", "")).strip()
        )
    subclass_levels = {
        feature["level"]
        for feature in (metadata or {}).get("subclass_progression", ())
        if isinstance(feature, Mapping) and isinstance(feature.get("level"), int)
    }
    subclass_label = SUBCLASS_FEATURE_LABELS.get(
        str(payload.get("name", "")).casefold(), "Subclass"
    )
    for level in sorted(subclass_levels):
        features_by_level.setdefault(level, []).append(f"{subclass_label} Feature")

    progression = payload.get("presentation_progression")
    if not isinstance(progression, Mapping):
        progression = (metadata or {}).get("presentation_progression")
    if not isinstance(progression, Mapping):
        progression = {}
    cantrips = _level_values(progression.get("cantrips_known"))
    slots = progression.get("spell_slots")
    if not isinstance(slots, Mapping):
        slots = _standard_spell_slots(payload.get("spellcasting"))

    rows = []
    for level in range(1, 21):
        row = {
            "level": _ordinal(level),
            "proficiency_bonus": f"+{2 + (level - 1) // 4}",
            "features": ", ".join(features_by_level.get(level, ())) or "-",
            "cantrips_known": _display_value(cantrips.get(level)),
        }
        if slots:
            for spell_level in SPELL_LEVEL_COLUMNS:
                values = slots.get(spell_level, slots.get(int(spell_level), {}))
                if isinstance(values, Mapping):
                    values = values.get(level, values.get(str(level)))
                elif isinstance(values, list) and len(values) >= level:
                    values = values[level - 1]
                row[f"slot_{spell_level}"] = _display_value(values)
        rows.append(row)
    return rows


def _standard_spell_slots(spellcasting: Any) -> dict[str, dict[int, int]]:
    if not isinstance(spellcasting, Mapping):
        return {}
    progression = spellcasting.get("progression")
    divisor = {"full": 1, "half": 2, "third": 3}.get(progression)
    if divisor is None:
        return {}
    result = {level: {} for level in SPELL_LEVEL_COLUMNS}
    for level in range(1, 21):
        source_level = min(20, level // divisor)
        if source_level == 0:
            continue
        values = FULL_SPELL_SLOTS[source_level - 1]
        for spell_level, amount in enumerate(values, start=1):
            result[str(spell_level)][level] = amount
    return result


def _level_values(value: Any) -> dict[int, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {int(level): amount for level, amount in value.items() if str(level).isdigit()}


def _display_value(value: Any) -> Any:
    return "-" if value in (None, 0, "", False) else value


def _ordinal(value: int) -> str:
    suffix = "th" if 10 < value % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
