"""Dedicated reader-facing entity presentation templates."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from application.class_presentation import class_progression_rows


ABILITY_ORDER = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
ABILITY_LABELS = {
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA",
}
CR_XP = {
    0.0: 10,
    0.125: 25,
    0.25: 50,
    0.5: 100,
}

ENTITY_TEMPLATE_FIELDS = {
    "spell": ("level", "school", "casting_time", "target", "components", "material", "duration", "ritual", "concentration", "effects", "description", "higher_level", "classes"),
    "item": ("category", "weapon", "armor", "magic_item", "weight", "cost", "features", "description"),
    "class": ("hit_dice", "primary_abilities", "saving_throws", "armor_proficiencies", "weapon_proficiencies", "tool_proficiencies", "skill_choices", "spellcasting", "level_progression", "features", "description"),
    "subclass": ("class_name", "level_progression", "features", "description"),
    "race": ("size", "movement", "ability_score_increases", "senses", "skill_proficiencies", "languages", "features", "description"),
    "feat": ("prerequisite", "ability_score_increases", "weapon_proficiencies", "features", "description"),
    "background": ("skill_proficiencies", "tool_proficiencies", "languages", "equipment", "features", "description"),
    "ability": ("category", "class_name", "level", "prerequisite", "effects", "description"),
}

SUPPLEMENTARY_CLASS_FEATURES = {
    "starting bard",
    "multiclass bard",
    "additional bard spells",
    "magical inspiration",
    "bardic versatility",
}
def readonly_payload(payload: dict[str, Any]) -> MappingProxyType:
    """Expose a detached, shallow immutable view to presentation code."""
    return MappingProxyType(dict(payload))


@dataclass(frozen=True)
class MonsterPresentation:
    name: str
    identity: str
    armor_class: str | None
    hit_points: str | None
    speed: str | None
    ability_scores: tuple[tuple[str, str, str], ...]
    saving_throws: str | None
    skills: str | None
    damage_vulnerabilities: str | None
    damage_resistances: str | None
    damage_immunities: str | None
    condition_immunities: str | None
    senses: str | None
    languages: str | None
    challenge: str | None
    proficiency_bonus: str | None
    traits: tuple[dict[str, Any], ...]
    actions: tuple[dict[str, Any], ...]
    reactions: tuple[dict[str, Any], ...]
    legendary_actions: tuple[dict[str, Any], ...]


def _modifier(score: int) -> int:
    return (score - 10) // 2


def _signed(value: int) -> str:
    return f"{value:+d}"


def _label(value: Any) -> str:
    return str(value).replace("_", " ").title()


def _identity_part(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(
            _label(value[key])
            for key in ("order", "morality")
            if value.get(key) is not None
        )
    if value is None:
        return ""
    return _label(value)


def _join_mapping(values: Any, *, signed: bool = False) -> str | None:
    if not isinstance(values, dict) or not values:
        return None
    result = []
    for key, value in values.items():
        rendered = _signed(int(value)) if signed else str(value)
        result.append(f"{_label(key)} {rendered}")
    return ", ".join(result)


def _join_list(values: Any) -> str | None:
    if not isinstance(values, list) or not values:
        return None
    return ", ".join(_label(value) for value in values)


def _speed(payload: dict[str, Any]) -> str | None:
    values = []
    for movement in payload.get("movement", ()):
        if not isinstance(movement, dict):
            continue
        movement_type = movement.get("movement_type")
        speed = movement.get("speed", {})
        if movement_type is None or not isinstance(speed, dict):
            continue
        distance = speed.get("distance")
        unit = speed.get("unit", "feet")
        if distance is not None:
            values.append(f"{_label(movement_type)} {distance} {_label(unit).lower()}")
    return ", ".join(values) or None


def _armor_class(payload: dict[str, Any]) -> str | None:
    armor = payload.get("armor_class")
    if not isinstance(armor, dict) or armor.get("value") is None:
        return None
    description = armor.get("description")
    return f"{armor['value']} ({description})" if description else str(armor["value"])


def _hit_points(payload: dict[str, Any]) -> str | None:
    hit_points = payload.get("hit_points")
    hit_dice = payload.get("hit_dice")
    if not isinstance(hit_points, dict) or hit_points.get("maximum") is None:
        return None
    maximum = hit_points["maximum"]
    if isinstance(hit_dice, dict) and hit_dice.get("count") is not None and hit_dice.get("dice") is not None:
        modifier = maximum - (int(hit_dice["count"]) * (int(hit_dice["dice"]) + 1) // 2)
        sign = f" {modifier:+d}" if modifier else ""
        return f"{maximum} ({hit_dice['count']}d{hit_dice['dice']}{sign})"
    return str(maximum)


def _senses(payload: dict[str, Any]) -> str | None:
    values = []
    for sense in payload.get("senses", ()):
        if not isinstance(sense, dict):
            continue
        distance = sense.get("distance")
        if distance is None:
            continue
        values.append(f"{_label(sense.get('type', 'sense'))} {distance} ft.")
    passive = payload.get("passive_perception")
    if passive is not None:
        values.append(f"passive Perception {passive}")
    return ", ".join(values) or None


def monster_presentation(payload: dict[str, Any], *, fallback_name: str | None = None) -> MonsterPresentation:
    scores = payload.get("ability_scores", {})
    ability_scores = tuple(
        (
            ABILITY_LABELS[ability],
            str(scores.get(ability, "-")),
            _signed(_modifier(int(scores[ability]))) if ability in scores else "-",
        )
        for ability in ABILITY_ORDER
    )
    challenge_rating = payload.get("challenge_rating")
    challenge = None
    if challenge_rating is not None:
        challenge_value = float(challenge_rating)
        challenge_number = int(challenge_value) if challenge_value.is_integer() else challenge_value
        experience = CR_XP.get(challenge_value)
        challenge = f"{challenge_number}" + (f" ({experience} XP)" if experience is not None else "")
    proficiency = None
    if challenge_rating is not None:
        proficiency = f"+{2 + max(0, (float(challenge_rating) - 1) // 4):.0f}"
    return MonsterPresentation(
        name=str(payload.get("name") or fallback_name or "Unnamed Monster"),
        identity=", ".join(
            part for part in (
                _identity_part(payload.get("size")),
                _identity_part(payload.get("creature_type")),
                _identity_part(payload.get("alignment")),
            ) if part
        ),
        armor_class=_armor_class(payload),
        hit_points=_hit_points(payload),
        speed=_speed(payload),
        ability_scores=ability_scores,
        saving_throws=_join_mapping(payload.get("saving_throws"), signed=True),
        skills=_join_mapping(payload.get("skills"), signed=True),
        damage_vulnerabilities=_join_list(payload.get("damage_vulnerabilities")),
        damage_resistances=_join_list(payload.get("damage_resistances")),
        damage_immunities=_join_list(payload.get("damage_immunities")),
        condition_immunities=_join_list(payload.get("condition_immunities")),
        senses=_senses(payload),
        languages=_join_list(payload.get("languages")),
        challenge=challenge,
        proficiency_bonus=proficiency,
        traits=tuple(value for value in payload.get("features", ()) if isinstance(value, dict)),
        actions=tuple(value for value in payload.get("actions", ()) if isinstance(value, dict)),
        reactions=tuple(value for value in payload.get("reactions", ()) if isinstance(value, dict)),
        legendary_actions=tuple(value for value in payload.get("legendary_actions", ()) if isinstance(value, dict)),
    )


def _named_blocks(title: str, values: tuple[dict[str, Any], ...]) -> list[str]:
    if not values:
        return []
    lines = [f"### {title}", ""]
    for value in values:
        name = value.get("name", "Unnamed")
        description = value.get("description", "")
        lines.append(f"***{name}.*** {description}".rstrip())
        lines.append("")
    return lines[:-1]


def render_monster_template(payload: dict[str, Any], *, fallback_name: str | None = None) -> str:
    view = monster_presentation(payload, fallback_name=fallback_name)
    lines = [f"# {view.name}", f"*{view.identity}*", "", "---", ""]
    for label, value in (
        ("Armor Class", view.armor_class),
        ("Hit Points", view.hit_points),
        ("Speed", view.speed),
    ):
        if value:
            lines.extend((f"**{label}** {value}", ""))
    lines.extend(
        [
            "| STR | DEX | CON | INT | WIS | CHA |",
            "|:---:|:---:|:---:|:---:|:---:|:---:|",
            "| " + " | ".join(f"{score} ({modifier})" for _, score, modifier in view.ability_scores) + " |",
            "",
        ]
    )
    for label, value in (
        ("Saving Throws", view.saving_throws),
        ("Skills", view.skills),
        ("Damage Vulnerabilities", view.damage_vulnerabilities),
        ("Damage Resistances", view.damage_resistances),
        ("Damage Immunities", view.damage_immunities),
        ("Condition Immunities", view.condition_immunities),
        ("Senses", view.senses),
        ("Languages", view.languages),
        ("Challenge", view.challenge),
        ("Proficiency Bonus", view.proficiency_bonus),
    ):
        if value:
            lines.extend((f"**{label}** {value}", ""))
    lines.append("---")
    lines.append("")
    for title, values in (
        ("Traits", view.traits),
        ("Actions", view.actions),
        ("Reactions", view.reactions),
        ("Legendary Actions", view.legendary_actions),
    ):
        block = _named_blocks(title, values)
        if block:
            lines.extend(block)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _feature_name(feature: dict[str, Any]) -> str:
    return str(feature.get("name") or "Unnamed Feature").strip()


def _feature_blocks(features: list[dict[str, Any]]) -> list[str]:
    lines = []
    for feature in features:
        name = _feature_name(feature)
        level = feature.get("level")
        heading = f"### {name}"
        if isinstance(level, int):
            heading += f" ({level}{'st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th'} level)"
        lines.extend((heading, "", str(feature.get("description") or "").strip(), ""))
    return lines


def _description_repeats_features(description: Any, features: list[dict[str, Any]]) -> bool:
    if not isinstance(description, str) or not description.strip():
        return False
    normalized = description.casefold()
    covered = 0
    for feature in features:
        feature_description = feature.get("description")
        if not isinstance(feature_description, str) or len(feature_description.strip()) < 20:
            continue
        if feature_description.strip()[:60].casefold() in normalized:
            covered += 1
    return covered >= 2


def _split_repeated_item_features(
    description: Any, features: list[dict[str, Any]]
) -> tuple[Any, list[dict[str, Any]]]:
    if not isinstance(description, str) or not description.strip():
        return description, features
    description_folded = description.casefold()
    split_at = None
    for feature in features:
        name = _feature_name(feature)
        feature_description = feature.get("description")
        if not isinstance(feature_description, str) or len(feature_description.strip()) < 20:
            continue
        marker = f"{name}:"
        marker_index = description_folded.find(marker.casefold())
        if marker_index < 0:
            continue
        content_start = marker_index + len(marker)
        feature_prefix = feature_description.strip()[:80].casefold()
        if feature_prefix in description_folded[content_start:]:
            split_at = marker_index if split_at is None else min(split_at, marker_index)
    if split_at is None:
        return description, features
    return description[:split_at].rstrip(), features


def _table_lines(title: str, rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    columns = list(rows[0])
    lines = [f"## {title}", "", "| " + " | ".join(_label(column) for column in columns) + " |"]
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    lines.append("")
    return lines


def render_class_template(
    payload: dict[str, Any], *, fallback_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render a populated class in the source's table-then-features order."""
    view = readonly_payload(payload)
    name = str(view.get("name") or fallback_name or "Unnamed Class")
    features = [feature for feature in view.get("features", ()) if isinstance(feature, dict)]
    core_features = [
        feature for feature in features
        if _feature_name(feature).casefold() not in SUPPLEMENTARY_CLASS_FEATURES
    ]
    ordered_features = sorted(
        enumerate(features),
        key=lambda item: (
            item[1].get("level") if isinstance(item[1].get("level"), int) else float("inf"),
            item[1] not in core_features,
            item[0],
        ),
    )
    ordered_features = [feature for _, feature in ordered_features]

    lines = [f"# {name}", ""]
    description = view.get("description")
    if description and not _description_repeats_features(description, features):
        lines.extend(("## Description", "", str(description), ""))
    progression_payload = dict(payload)
    progression_payload["features"] = core_features
    lines.extend(_table_lines("Level Progression", class_progression_rows(progression_payload, metadata)))
    lines.extend(("## Class Features", ""))
    for label, value in (
        ("Hit Die", view.get("hit_dice")),
        ("Primary Abilities", view.get("primary_abilities")),
        ("Saving Throws", view.get("saving_throws")),
        ("Armor Proficiencies", view.get("armor_proficiencies")),
        ("Weapon Proficiencies", view.get("weapon_proficiencies")),
        ("Tool Proficiencies", view.get("tool_proficiencies")),
        ("Skill Choices", view.get("skill_choices")),
    ):
        if value not in (None, [], {}, ""):
            lines.extend((f"**{label}:** {_render_value(value)}", ""))
    spellcasting = view.get("spellcasting")
    if isinstance(spellcasting, dict):
        lines.extend(("## Spellcasting Details", ""))
        for label, value in (
            ("Ability", _label(spellcasting.get("ability")) if spellcasting.get("ability") else None),
            ("Progression", _label(spellcasting.get("progression")) if spellcasting.get("progression") else None),
            ("Ritual Casting", "Yes" if spellcasting.get("ritual") else None),
            ("Prepared Spells", "Yes" if spellcasting.get("prepared") else None),
            ("Spells", spellcasting.get("spells")),
        ):
            if value not in (None, [], {}, "", False):
                lines.extend((f"**{label}:** {_render_value(value)}", ""))
    lines.extend(_feature_blocks(ordered_features))
    return "\n".join(lines).rstrip() + "\n"


def render_subclass_template(
    payload: dict[str, Any], *, fallback_name: str | None = None,
) -> str:
    """Render a subclass while preserving source-backed table-bearing features."""
    view = readonly_payload(payload)
    name = str(view.get("name") or fallback_name or "Unnamed Subclass")
    parent = view.get("class", view.get("class_name"))
    lines = [f"# {name}", ""]
    if parent:
        lines.extend((f"**Parent Class:** {_render_value(parent)}", ""))
    features = [feature for feature in view.get("features", ()) if isinstance(feature, dict)]
    overview = [feature for feature in features if _feature_name(feature).casefold().startswith(("bard college:", "martial archetype:"))]
    details = [feature for feature in features if feature not in overview]
    details = sorted(
        enumerate(details),
        key=lambda item: (
            item[1].get("level") if isinstance(item[1].get("level"), int) else float("inf"),
            item[0],
        ),
    )
    details = [feature for _, feature in details]
    if not overview:
        rows = []
        levels = sorted({feature.get("level") for feature in features if isinstance(feature.get("level"), int)})
        for level in range(1, (levels[-1] if levels else 0) + 1):
            rows.append({
                "level": level,
                "features": ", ".join(
                    _feature_name(feature) for feature in features if feature.get("level") == level
                ),
            })
        lines.extend(_table_lines("Level Progression", rows))
    if overview:
        lines.extend(("## Overview", ""))
        lines.extend(_feature_blocks(overview))
    lines.extend(("## Features", ""))
    lines.extend(_feature_blocks(details))
    if view.get("description"):
        lines.extend(("## Description", "", str(view["description"]), ""))
    return "\n".join(lines).rstrip() + "\n"


def render_race_template(
    payload: dict[str, Any], *, fallback_name: str | None = None,
) -> str:
    """Render a race with compact movement, ability, and sense summaries."""
    view = readonly_payload(payload)
    name = str(view.get("name") or fallback_name or "Unnamed Race")
    subtype = str(view.get("subtype") or "").strip()
    title = f"{name}, {subtype}" if subtype else name
    identity = ", ".join(
        part for part in (_label(view.get("size")),) if part
    )
    lines = [f"# {title}", ""]
    if identity:
        lines.extend((f"*{identity}*", ""))

    movement_values = []
    for movement in view.get("movement", ()):
        if not isinstance(movement, dict):
            continue
        movement_type = str(movement.get("movement_type") or "").casefold()
        speed = movement.get("speed")
        if not isinstance(speed, dict) or speed.get("distance") is None:
            continue
        unit = str(speed.get("unit") or "feet").casefold()
        unit_label = "ft" if unit in {"foot", "feet"} else _label(unit).lower()
        value = f"{speed['distance']}{unit_label}"
        if movement_type not in {"walk", "walking"}:
            value = f"{_label(movement_type)} {value}"
        movement_values.append(value)
    if movement_values:
        lines.extend((f"**Speed** {', '.join(movement_values)}", ""))

    ability_values = []
    for increase in view.get("ability_score_increases", ()):
        if not isinstance(increase, dict) or increase.get("ability") is None:
            continue
        if increase.get("amount") is None:
            continue
        ability_values.append(f"{_label(increase['ability'])} +{increase['amount']}")
    if ability_values:
        lines.extend((f"**Ability Score Increases** {', '.join(ability_values)}", ""))

    sense_values = []
    for sense in view.get("senses", ()):
        if not isinstance(sense, dict) or sense.get("distance") is None:
            continue
        sense_type = _label(sense.get("type", "sense"))
        distance = sense["distance"]
        distance_type = str(sense.get("distance_type") or "feet").casefold()
        unit = "ft." if distance_type in {"foot", "feet"} else f"{_label(distance_type)}."
        sense_values.append(f"{sense_type} {distance} {unit}")
    if sense_values:
        lines.extend((f"**Senses** {', '.join(sense_values)}", ""))

    for label, field in (
        ("Skill Proficiencies", "skill_proficiencies"),
        ("Languages", "languages"),
        ("Weapon Proficiencies", "weapon_proficiencies"),
    ):
        value = view.get(field)
        if value not in (None, [], {}, ""):
            lines.extend((f"**{label}** {_render_value(value)}", ""))
    if view.get("spell_grants"):
        lines.extend((f"**Spell Grants** {_render_value(view['spell_grants'])}", ""))
    if view.get("feats"):
        lines.extend((f"**Feats** {_render_value(view['feats'])}", ""))
    if view.get("description"):
        lines.extend(("## Description", "", str(view["description"]), ""))
    features = [feature for feature in view.get("features", ()) if isinstance(feature, dict)]
    if features:
        lines.extend(("## Racial Traits", ""))
        lines.extend(_feature_blocks(features))
    actions = [action for action in view.get("actions", ()) if isinstance(action, dict)]
    if actions:
        lines.extend(("## Racial Actions", ""))
        lines.extend(_feature_blocks(actions))
    return "\n".join(lines).rstrip() + "\n"


def render_item_template(
    payload: dict[str, Any], *, fallback_name: str | None = None,
) -> str:
    """Render an item as a compact reader-facing stat block."""
    view = readonly_payload(payload)
    name = str(view.get("name") or fallback_name or "Unnamed Item")
    armor = view.get("armor") if isinstance(view.get("armor"), dict) else {}
    weapon = view.get("weapon") if isinstance(view.get("weapon"), dict) else {}
    magic_item = view.get("magic_item") if isinstance(view.get("magic_item"), dict) else {}

    category = _label(view.get("category")) if view.get("category") else None
    subtype = armor.get("category") or weapon.get("type")
    rarity = magic_item.get("rarity")
    metadata = category or "Item"
    if subtype:
        metadata += f" ({_label(subtype).lower()})"
    if rarity:
        metadata += f", {_label(rarity).lower()}"

    features = [feature for feature in view.get("features", ()) if isinstance(feature, dict)]
    description, features = _split_repeated_item_features(
        view.get("description"), features
    )
    lines = [f"# {name}", "", f"*{metadata}*", ""]
    if description:
        lines.extend((str(description), ""))

    if armor:
        lines.extend((f"**AC:** {armor.get('armor_class')}", ""))
        if armor.get("strength_requirement") is not None:
            lines.extend((f"**Strength:** {armor['strength_requirement']}", ""))
        if armor.get("stealth_disadvantage"):
            lines.extend(("**Stealth:** Disadvantage", ""))
    if weapon:
        if weapon.get("effects"):
            lines.extend(("**Damage:**", "", _render_effects(weapon["effects"]), ""))
        if weapon.get("properties"):
            lines.extend((f"**Properties:** {_render_value(weapon['properties'])}", ""))
        if weapon.get("range"):
            lines.extend((f"**Range:** {_render_value(weapon['range'])}", ""))
    if magic_item.get("attunement") is not None:
        lines.extend((f"**Attunement:** {_render_value(magic_item['attunement'])}", ""))
    if magic_item.get("bonuses"):
        lines.extend((f"**Bonuses:** {_render_item_bonuses(magic_item['bonuses'])}", ""))
    if magic_item.get("charges"):
        lines.extend((f"**Charges:** {_render_item_charges(magic_item['charges'])}", ""))
    if magic_item.get("spells"):
        lines.extend(("**Spells:**", "", _render_item_spells(magic_item["spells"]), ""))
    if magic_item.get("grants"):
        lines.extend(("**Grants:**", "", _render_item_grants(magic_item["grants"]), ""))
    if magic_item.get("effects"):
        lines.extend(("**Effects:**", "", _render_effects(magic_item["effects"]), ""))
    if view.get("weight") is not None:
        lines.extend((f"**Weight:** {view['weight']}", ""))
    if view.get("cost") is not None:
        lines.extend((f"**Cost:** {_render_cost(view['cost'])}", ""))
    if features:
        lines.extend(("## Features", ""))
        lines.extend(_feature_blocks(features))
    return "\n".join(lines).rstrip() + "\n"


def _render_item_bonuses(bonuses: Any) -> str:
    rendered = []
    for bonus in bonuses if isinstance(bonuses, list) else ():
        if not isinstance(bonus, dict):
            rendered.append(_render_value(bonus))
            continue
        value = bonus.get("value")
        sign = f"{value:+}" if isinstance(value, (int, float)) else str(value)
        label = _label(bonus.get("type", "bonus"))
        if bonus.get("ability"):
            label = f"{label} ({_label(bonus['ability'])})"
        rendered.append(f"{sign} {label}")
    return ", ".join(rendered)


def _render_item_charges(charges: Any) -> str:
    if not isinstance(charges, dict):
        return _render_value(charges)
    maximum = charges.get("maximum")
    recharge = charges.get("recharge")
    duration = charges.get("recharge_duration")
    result = f"{maximum}" if maximum is not None else ""
    if recharge is not None:
        result += f", recharge {_render_value(recharge)}"
    if duration:
        result += f" per {_render_value(duration)}"
    return result


def _render_item_spells(spells: Any) -> str:
    values = []
    for entry in spells if isinstance(spells, list) else ():
        if isinstance(entry, dict):
            spell = entry.get("spell", "")
            charges = entry.get("charges")
            values.append(f"{spell} ({charges} charge{'s' if charges != 1 else ''})" if charges is not None else str(spell))
        else:
            values.append(str(entry))
    return ", ".join(values)


def _render_item_grants(grants: Any) -> str:
    values = []
    for grant in grants if isinstance(grants, list) else ():
        if isinstance(grant, dict):
            grant_type = _label(grant.get("type", "grant"))
            details = [
                _label(grant[key])
                for key in ("ability_check", "skill", "saving_throw", "condition", "damage_type", "sense")
                if grant.get(key) is not None
            ]
            values.append(f"{grant_type} ({', '.join(details)})" if details else grant_type)
        else:
            values.append(str(grant))
    return ", ".join(values)

def _render_cost(cost: Any) -> str:
    return "{amount}{currency}".format(amount=cost.get("amount"), currency=cost.get("currency"))


def _render_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(_render_value(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{_label(key)}: {_render_value(item)}" for key, item in value.items())
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _render_spell_value(field: str, value: Any) -> str:
    if field == "casting_time":
        values = value if isinstance(value, list) else [value]
        return " or ".join(
            _render_amount_unit(item.get("amount"), item.get("unit"))
            for item in values
            if isinstance(item, dict)
        )
    if field == "target" and isinstance(value, dict):
        targeting = _label(value.get("targeting", ""))
        range_value = value.get("range")
        if isinstance(range_value, dict):
            distance = _render_amount_unit(
                range_value.get("amount"), range_value.get("unit")
            )
            return f"{targeting}: {distance}" if targeting else distance
        return targeting or str(value.get("description", ""))
    if field == "duration" and isinstance(value, dict):
        return _render_amount_unit(value.get("amount"), value.get("duration"))
    if field == "effects" and isinstance(value, list):
        return _render_effects(value)
    if field == "material" and isinstance(value, dict):
        return value.get("description")
    return _render_value(value)


def _render_effects(effects: Any) -> str:
    return "\n".join(
        f"- {_render_effect(effect)}"
        for effect in effects if isinstance(effects, list)
    )


def _render_effect(effect: Any) -> str:
    if not isinstance(effect, dict):
        return _render_value(effect)
    if effect.get("attack_save"):
        return _render_attack_save(effect["attack_save"])
    if effect.get("attack_hit"):
        return _render_attack_hit(effect["attack_hit"])
    if effect.get("damage"):
        return _render_damage(effect["damage"])
    for key, label in (
        ("healing", "Healing"),
        ("max_hit_points", "Maximum hit points"),
        ("temporary_hit_points", "Temporary hit points"),
        ("ability_score", "Ability score"),
        ("exhaustion", "Exhaustion"),
    ):
        if effect.get(key):
            return f"{label}: {_render_roll(effect[key])}"
    if effect.get("condition"):
        return f"Condition: {_label(effect['condition'])}"
    if effect.get("grants"):
        return "; ".join(_render_item_grants([grant]) for grant in effect["grants"])
    return str(effect.get("description") or _render_value(effect))


def _render_attack_save(value: Any) -> str:
    if not isinstance(value, dict):
        return _render_value(value)
    result = f"{_label(value.get('ability', ''))} saving throw"
    if value.get("dc") is not None:
        result += f" (DC {value['dc']})"
       
    failure = value.get("failure") 
    if failure is not None:
        result += f"; On a failed save: " + ", ".join(_render_effect(item) for item in failure)
    success = value.get("success")
    if success is not None:
        halved = all(
            {k: v for k, v in s.items() if not (k == "description" and v == "(Halved)")} == f
            for s, f in zip(success, failure)
        )
        if halved:
            result += ", or half as much damage on a successful save"
        else:
            result += "; " + ", ".join(_render_effect(item) for item in success)
            result += " on a successful save"
    return result


def _render_attack_hit(value: Any) -> str:
    if not isinstance(value, dict):
        return _render_value(value)
    result = _label(value.get("type", "attack"))
    if value.get("bonus") is not None:
        result += f" (+{value['bonus']} to hit)"
    if value.get("effects"):
        result += ": " + ", ".join(_render_effect(item) for item in value["effects"])
    return result


def _render_damage(value: Any) -> str:
    if not isinstance(value, dict):
        return _render_value(value)
    roll = _render_roll(value.get("roll", {}))
    result = f"{roll} {str(value.get('type', 'damage')).replace('_', ' ')} damage"
    if value.get("modifier"):
        result += f" ({value['modifier']:+})"
    return result


def _render_roll(value: Any) -> str:
    if not isinstance(value, dict):
        return _render_value(value)
    parts = []
    dice = value.get("dice")
    count = value.get("count")
    if dice is not None:
        parts.append(f"{count or 1}d{dice}")
    if value.get("modifier") not in (None, 0):
        parts.append(f"{value['modifier']:+}")
    if value.get("ability"):
        parts.append(_label(value["ability"]))
    return " ".join(parts) or _render_value(value)


def _render_amount_unit(amount: Any, unit: Any) -> str:
    labels = {"feet": "ft", "foot": "ft", "miles": "mi", "mile": "mi"}
    rendered_unit = labels.get(str(unit).casefold(), str(unit or "").replace("_", " "))
    return f"{amount} {rendered_unit}".strip() if amount is not None else rendered_unit


def render_entity_template(
    entity_type: str, payload: dict[str, Any], *, fallback_name: str
) -> str | None:
    """Render populated non-monster records through their reader-facing contract."""
    if entity_type == "class":
        return render_class_template(payload, fallback_name=fallback_name)
    if entity_type == "subclass":
        return render_subclass_template(payload, fallback_name=fallback_name)
    if entity_type == "race":
        return render_race_template(payload, fallback_name=fallback_name)
    if entity_type == "item":
        return render_item_template(payload, fallback_name=fallback_name)
    fields = ENTITY_TEMPLATE_FIELDS.get(entity_type)
    if fields is None or len(payload) < 2 or not any(field in payload for field in fields):
        return None
    view = readonly_payload(payload)
    lines = [f"# {view.get('name') or fallback_name}", ""]
    for field in fields:
        value = view.get(field)
        if value is None or value == [] or value == {} or value == "":
            continue
        label = _label(field)
        if field == "effects" and isinstance(value, list):
            lines.extend(("## Effects", "", _render_effects(value), ""))
        elif field == "features" and isinstance(value, list):
            lines.extend((f"## {label}", ""))
            for entry in value:
                if isinstance(entry, dict) and entry.get("name"):
                    lines.append(f"***{entry['name']}.*** {entry.get('description', '')}".rstrip())
                else:
                    lines.append(f"- {_render_value(entry)}")
                lines.append("")
            lines.pop()
            lines.append("")
        elif field == "description":
            lines.extend(("## Description", "", _render_value(value), ""))
        else:
            rendered_value = (
                _render_spell_value(field, value)
                if entity_type == "spell"
                else _render_value(value)
            )
            lines.extend((f"**{label}:** {rendered_value}", ""))
    return "\n".join(lines).rstrip() + "\n"
