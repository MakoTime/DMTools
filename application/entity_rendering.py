from __future__ import annotations

from html import escape
import re
from collections.abc import Mapping
from typing import Any

from application.class_presentation import class_progression_rows
from application.entity_templates import render_entity_template, render_monster_template


RENDERER_VERSION = "3"
HTML_TEMPLATE_VERSION = "1"
CSS_VERSION = "1"

ENTITY_PRESENTATION_CONTRACT = {
    "item": (
        "name", "category", "weapon", "armor", "magic_item", "weight",
        "cost", "features", "description", "source", "image",
    ),
    "spell": (
        "name", "level", "school", "casting_time", "target", "components",
        "material", "duration", "effects", "description", "higher_level",
        "classes", "ritual", "concentration", "tags", "source",
    ),
    "race": (
        "name", "size", "speed", "ability_score_increase", "traits",
        "languages", "description", "source",
    ),
    "class": (
        "name", "hit_dice", "primary_abilities", "saving_throws",
        "armor_proficiencies", "weapon_proficiencies", "tool_proficiencies",
        "skill_choices", "spellcasting", "subclass_level", "features",
        "description", "tags", "source",
    ),
    "subclass": ("name", "class_name", "features", "description", "source"),
    "monster": (
        "name", "size", "creature_type", "alignment", "armor_class",
        "hit_points", "hit_dice", "movement", "ability_scores", "saving_throws",
        "skills", "senses", "passive_perception", "languages",
        "damage_resistances", "damage_immunities", "damage_vulnerabilities",
        "condition_immunities", "proficiency_bonus", "challenge_rating",
        "spell_casting", "features", "actions", "reactions", "legendary_actions",
        "description", "environments", "source", "image",
    ),
    "feat": (
        "name", "prerequisite", "ability_score_increase", "features",
        "description", "source",
    ),
    "background": (
        "name", "skill_proficiencies", "tool_proficiencies", "languages",
        "equipment", "features", "description", "source",
    ),
    "ability": ("name", "category", "effects", "description", "source"),
}


def presentation_contract(entity_type: str) -> tuple[str, ...]:
    """Return stable shared/type-specific field ordering for an entity type."""
    try:
        return ENTITY_PRESENTATION_CONTRACT[entity_type]
    except KeyError as error:
        raise ValueError(f"Unsupported entity type: {entity_type}") from error


def render_entity_markdown(entity) -> str:
    """Render one canonical entity record as a deterministic derived document."""
    lines = [
        f"<!-- dmtools-entity-uid: {entity.uid}; renderer: {RENDERER_VERSION} -->",
        f"# {entity.name}",
        "",
        f"> **Type:** {entity.entity_type}",
        f"> **Source:** {entity.source_namespace}",
        "",
    ]
    metadata = getattr(entity, "source_metadata", {}) or {}
    dedicated_monster = entity.entity_type == "monster" and (
        "ability_scores" in entity.payload or "hit_points" in entity.payload
    )
    if dedicated_monster:
        lines = [
            f"<!-- dmtools-entity-uid: {entity.uid}; renderer: {RENDERER_VERSION} -->",
            *render_monster_template(
                entity.payload, fallback_name=entity.name
            ).splitlines(),
        ]
    else:
        dedicated_payload = _with_progression_sections(
            entity.entity_type, entity.payload, metadata
        )
        dedicated_template = render_entity_template(
            entity.entity_type, dedicated_payload, fallback_name=entity.name
        )
        if dedicated_template is not None and _has_template_shape(entity.entity_type, entity.payload):
            lines = [
                f"<!-- dmtools-entity-uid: {entity.uid}; renderer: {RENDERER_VERSION} -->",
                *dedicated_template.splitlines(),
            ]
        else:
            presentation_payload = _ordered_payload(
                entity.entity_type, entity.payload, metadata
            )
            _remove_redundant_feature_sources(presentation_payload, entity, metadata)
            _append_markdown_value(lines, "Details", presentation_payload)
    references = metadata.get("entity_references", ())
    diagnostics = metadata.get("reference_diagnostics", ())
    lines = _replace_inline_spell_links(lines, references)
    other_references = [
        reference for reference in references if reference.get("entity_type") != "spell"
    ]
    if other_references:
        lines.extend(("", "## References"))
        for reference in other_references:
            label = reference.get("display_fallback", reference["target_uid"])
            lines.append(
                f"- [{label}](dmtools://entity/{reference['target_uid']}) "
                f"({reference['entity_type']}, {reference['source_namespace']})"
            )
    if diagnostics:
        lines.extend(("", "## Unresolved References"))
        for diagnostic in diagnostics:
            lines.append(
                f"- {diagnostic['display_fallback']} "
                f"({diagnostic['status']}; {diagnostic['path']})"
            )
    return "\n".join(lines).rstrip() + "\n"


def _replace_inline_spell_links(lines: list[str], references) -> list[str]:
    spell_references = [
        reference for reference in references
        if reference.get("entity_type") == "spell" and reference.get("display_fallback")
    ]
    if not spell_references:
        return lines
    replacements = sorted(
        ((reference["display_fallback"], reference["target_uid"]) for reference in spell_references),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    result = []
    for line in lines:
        for label, target_uid in replacements:
            link = f"[{label}](dmtools://entity/{target_uid})"
            line = re.sub(
                rf"(?<![\w\]]){re.escape(label)}(?!\w)",
                link,
                line,
                flags=re.IGNORECASE,
            )
        result.append(line)
    return result


def _has_template_shape(entity_type: str, payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    required = {
        "spell": {"level", "school", "casting_time"},
        "item": {"category", "weight"},
        "class": {"hit_dice", "features"},
        "subclass": {"features"},
        "race": {"size", "movement"},
        "feat": {"prerequisite", "features"},
        "background": {"skill_proficiencies", "features"},
        "ability": {"category", "effects"},
    }.get(entity_type)
    if not required or not required.issubset(payload):
        return False
    if entity_type == "subclass":
        return "class" in payload or "class_name" in payload
    return True


def render_entity_html(entity) -> str:
    """Render generated Markdown through the safe inspection HTML pipeline."""
    markdown = render_entity_markdown(entity)
    body = _markdown_to_html(markdown)
    return (
        '<article class="dmtools-inspection" '
        f'data-entity-uid="{escape(entity.uid, quote=True)}" '
        f'data-template-version="{HTML_TEMPLATE_VERSION}" '
        f'data-css-version="{CSS_VERSION}">{body}</article>'
    )


def _ordered_payload(
    entity_type: str, payload: Any, metadata: Mapping[str, Any] | None = None
) -> Any:
    if not isinstance(payload, dict):
        return payload
    payload = _with_progression_sections(entity_type, payload, metadata)
    ordered_fields = presentation_contract(entity_type)
    ordered = {}
    for field in ordered_fields:
        if field == "features" and "level_progression" in payload:
            ordered["level_progression"] = payload["level_progression"]
        if field in payload:
            ordered[field] = payload[field]
    ordered.update({
        field: value for field, value in payload.items()
        if field not in ordered
    })
    return {
        field: _order_nested_values(value)
        for field, value in ordered.items()
    }


def _order_nested_values(value: Any) -> Any:
    if isinstance(value, list):
        return [_order_nested_values(item) for item in value]
    if not isinstance(value, dict):
        return value
    ordered = {}
    for field in ("level", "name", "description", "effects", "source"):
        if field in value:
            ordered[field] = _order_nested_values(value[field])
    ordered.update(
        {
            field: _order_nested_values(item)
            for field, item in value.items()
            if field not in ordered
        }
    )
    return ordered


def _remove_redundant_feature_sources(
    payload: Any, entity: Any, metadata: Mapping[str, Any]
):
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        return
    identities = {
        str(value)
        for value in (
            getattr(entity, "source_namespace", None),
            metadata.get("source_identity"),
            metadata.get("provenance"),
        )
        if value
    }
    cleaned = []
    for feature in payload["features"]:
        if not isinstance(feature, dict):
            cleaned.append(feature)
            continue
        source = feature.get("source")
        source_identity = source.get("text") if isinstance(source, dict) else source
        if source_identity in identities:
            feature = {key: value for key, value in feature.items() if key != "source"}
        cleaned.append(feature)
    payload["features"] = cleaned


def _with_progression_sections(
    entity_type: str,
    payload: dict[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Add derived progression tables without changing the canonical payload."""
    if entity_type not in {"class", "subclass"}:
        return payload
    enriched = dict(payload)
    features = [feature for feature in payload.get("features", ()) if isinstance(feature, dict)]
    if entity_type == "class":
        enriched["level_progression"] = {
            "table": class_progression_rows(payload, metadata),
        }
        return enriched
    leveled = [feature for feature in features if isinstance(feature.get("level"), int)]
    if leveled:
        maximum = max(feature["level"] for feature in leveled)
        enriched["level_progression"] = {
            "table": [
                {
                    "level": level,
                    "features": ", ".join(
                        feature["name"]
                        for feature in leveled
                        if feature["level"] == level
                    ),
                }
                for level in range(1, maximum + 1)
            ]
        }
    if entity_type == "class" and payload.get("spellcasting"):
        spell_slots = payload.get("spell_slots")
        if isinstance(spell_slots, list) and spell_slots:
            enriched["spell_slot_progression"] = {"table": spell_slots}
        else:
            enriched["spell_slot_progression"] = {
                "callout": {
                    "title": "Spell slots",
                    "text": "Unavailable in the imported class data.",
                }
            }
    return enriched


def _append_markdown_value(lines: list[str], title: str, value: Any, level: int = 2):
    lines.append(f"{'#' * level} {title}")
    if isinstance(value, dict):
        for key, child in value.items():
            if child is None:
                continue
            if isinstance(child, (dict, list)):
                title = str(key).replace("_", " ").title()
                if (
                    isinstance(child, dict)
                    and str(key).casefold() in {"level_progression", "spell_slot_progression"}
                    and isinstance(child.get("table"), list)
                ):
                    _append_markdown_table(lines, title, child["table"], level)
                    continue
                normalized = _format_structured_value(str(key), child)
                if normalized is not None:
                    if isinstance(normalized, list):
                        lines.extend(f"- {_display_scalar(item)}" for item in normalized)
                    else:
                        lines.append(f"- **{_display_label(key)}:** {normalized}")
                elif str(key).casefold() in {"table", "tables"} and isinstance(child, list):
                    _append_markdown_table(lines, title, child, level + 1)
                elif str(key).casefold() in {"callout", "callouts"}:
                    _append_markdown_callouts(lines, child)
                else:
                    _append_markdown_value(lines, title, child, level + 1)
            else:
                lines.append(f"- **{_display_label(key)}:** {_display_scalar(child)}")
    elif isinstance(value, list):
        for child in value:
            if child is None:
                continue
            if isinstance(child, dict):
                _append_markdown_list_item(lines, child)
            elif isinstance(child, list):
                for nested in child:
                    if nested is not None:
                        lines.append(f"- {_display_scalar(nested)}")
            else:
                lines.append(f"- {_display_scalar(child)}")
    else:
        if value is not None:
            lines.append(str(value))


def _format_structured_value(key: str, value: Any) -> str | list[str] | None:
    """Format known typed records while leaving unknown data to the fallback renderer."""
    normalized_key = key.casefold()
    if normalized_key == "casting_time":
        values = value if isinstance(value, list) else [value]
        rendered = [
            _amount_with_unit(item.get("amount"), item.get("unit"))
            for item in values
            if isinstance(item, dict)
        ]
        return " or ".join(rendered) or None
    if normalized_key == "target" and isinstance(value, dict):
        targeting = str(value.get("targeting", "")).replace("_", " ").title()
        range_value = value.get("range")
        if isinstance(range_value, dict):
            distance = _amount_with_unit(
                range_value.get("amount"), range_value.get("unit")
            )
            return f"{targeting}: {distance}" if targeting else distance
        return targeting or value.get("description")
    if normalized_key in {"duration", "cost"} and isinstance(value, dict):
        if normalized_key == "duration":
            return _amount_with_unit(value.get("amount"), value.get("duration"))
        return _format_cost(value)
    if normalized_key in {"range", "ranges"} and isinstance(value, dict):
        normal = _amount_with_unit(value.get("normal"), "feet")
        long_range = value.get("long")
        if long_range is None:
            return normal
        return f"{normal} (long {long_range} ft)"
    if not isinstance(value, list) or normalized_key not in {
        "senses", "movement", "speeds", "ranges", "costs", "durations",
        "proficiencies", "skill_proficiencies", "damage_resistances",
        "damage_immunities", "damage_vulnerabilities", "condition_immunities",
    }:
        return None
    result = []
    for item in value:
        if not isinstance(item, dict):
            result.append(
                str(item).replace("_", " ").title()
                if normalized_key not in {"movement", "speeds"}
                else str(item)
            )
            continue
        if normalized_key == "senses":
            label = str(item.get("type", "Sense")).replace("_", " ").title()
            result.append(f"{label}: {_amount_with_unit(item.get('distance'), item.get('distance_type'))}")
        elif normalized_key in {"movement", "speeds"}:
            label = str(item.get("movement_type", item.get("type", "Speed"))).replace(
                "_", " "
            ).title()
            speed = item.get("speed", item)
            if isinstance(speed, dict):
                result.append(f"{label}: {_amount_with_unit(speed.get('distance'), speed.get('unit'))}")
            else:
                result.append(f"{label}: {speed}")
        elif normalized_key in {"ranges", "durations"}:
            if normalized_key == "ranges":
                result.append(_format_structured_value("range", item) or "Unavailable")
            else:
                result.append(_format_structured_value("duration", item) or "Unavailable")
        elif normalized_key == "proficiencies" or normalized_key == "skill_proficiencies":
            result.append(str(item.get("name", item.get("type", "Unavailable"))).replace("_", " ").title())
        else:
            result.append(
                str(item.get("name", item.get("type", item.get("value", "Unavailable"))))
                .replace("_", " ")
                .title()
            )
    if not result:
        return ["Unavailable"]
    return result


def _amount_with_unit(amount: Any, unit: Any) -> str:
    if amount is None:
        return str(unit or "Unavailable")
    label = {
        "feet": "ft",
        "foot": "ft",
        "miles": "mi",
        "mile": "mi",
    }.get(str(unit).casefold(), str(unit or "").replace("_", " "))
    return f"{amount} {label}".strip()


def _format_cost(value: dict[str, Any]) -> str:
    amount = value.get("amount", value.get("value"))
    unit = value.get("currency", value.get("unit"))
    return _amount_with_unit(amount, unit)


def _append_markdown_list_item(lines: list[str], value: dict[str, Any]):
    if "name" in value:
        lines.append(f"- **{value['name']}**  ")
        description = value.get("description")
        if description is not None:
            if isinstance(description, list):
                lines.extend(f"  {_display_scalar(item)}" for item in description)
            else:
                lines.append(f"  {_display_scalar(description)}")
        entries = value.get("entries")
        if isinstance(entries, list):
            lines.extend(f"  - {_display_scalar(item)}" for item in entries if item is not None)
        value = {
            key: child for key, child in value.items()
            if key not in {"name", "description", "entries"}
        }
        if not value:
            return
        lines.append("")
    scalar_items = [(key, child) for key, child in value.items()
                    if child is not None and not isinstance(child, (dict, list))]
    nested_items = [(key, child) for key, child in value.items()
                    if child is not None and isinstance(child, (dict, list))]
    if scalar_items:
        lines.append("- " + "; ".join(
            f"**{_display_label(key)}:** {_display_scalar(child)}" for key, child in scalar_items
        ))
    else:
        lines.append("-")
    for key, child in nested_items:
        label = str(key).replace("_", " ").title()
        if isinstance(child, list):
            lines.append(f"  **{label}:**")
            for nested in child:
                if nested is not None:
                    lines.append(f"  - {_display_scalar(nested)}")
        else:
            lines.append(f"  **{_display_label(label)}:** {_display_scalar(child)}")


def _display_scalar(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(_display_scalar(item) for item in value if item is not None)
    if isinstance(value, dict):
        if "text" in value and value["text"] is not None:
            return str(value["text"])
        return "; ".join(
            f"{_display_label(key)}: {_display_scalar(child)}" for key, child in value.items()
            if child is not None
        )
    if isinstance(value, str) and "_" in value:
        return value.replace("_", " ").title()
    return str(value)


def _display_label(value: Any) -> str:
    return str(value).replace("_", " ").title()


def _append_markdown_table(
    lines: list[str], title: str, rows: list[Any], level: int
):
    mappings = [row for row in rows if isinstance(row, dict)]
    if not mappings:
        _append_markdown_value(lines, title, rows, level)
        return
    lines.append(f"{'#' * level} {title}")
    columns = list(dict.fromkeys(key for row in mappings for key in row))
    labels = _table_column_labels(title, columns)
    lines.append("| " + " | ".join(labels) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in mappings:
        values = [
            "" if row.get(column) is None else _display_scalar(row.get(column))
            for column in columns
        ]
        lines.append("| " + " | ".join(values) + " |")


def _table_column_labels(title: str, columns: list[str]) -> list[str]:
    if title.casefold() != "level progression":
        return [str(column) for column in columns]
    labels = {
        "level": "Level",
        "proficiency_bonus": "Proficiency Bonus",
        "features": "Features",
        "cantrips_known": "Cantrips Known",
    }
    result = []
    for column in columns:
        if column in labels:
            result.append(labels[column])
        else:
            result.append(_ordinal(int(column.removeprefix("slot_"))))
    return result


def _ordinal(value: int) -> str:
    suffix = "th" if 10 < value % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def _append_markdown_callouts(lines: list[str], value: Any):
    values = value if isinstance(value, list) else [value]
    for callout in values:
        if isinstance(callout, dict):
            label = callout.get("title", callout.get("name", "Note"))
            text = callout.get("text", callout.get("description", ""))
        else:
            label, text = "Note", callout
        if text is not None:
            lines.append(f"> **{label}:** {text}")


def _markdown_to_html(markdown: str) -> str:
    """Convert only the Markdown constructs emitted by this module."""
    html: list[str] = []
    in_list = False
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("<!--"):
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            if in_list:
                html.append("</ul>")
                in_list = False
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            html.append(_markdown_table_to_html(table_lines))
            continue
        if not line.strip():
            if in_list:
                html.append("</ul>")
                in_list = False
            index += 1
            continue
        if line.strip() == "---":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append("<hr>")
            index += 1
            continue
        if line.startswith("#"):
            if in_list:
                html.append("</ul>")
                in_list = False
            level = len(line) - len(line.lstrip("#"))
            html.append(f"<h{level}>{_markdown_inline(line[level + 1:])}</h{level}>")
        elif line.startswith("> "):
            html.append(f"<blockquote>{_markdown_inline(line[2:])}</blockquote>")
        elif line.startswith("  ") and in_list:
            continuation = f"<br>{_markdown_inline(line.strip())}"
            if html and html[-1].endswith("</li>"):
                html[-1] = html[-1][:-5] + continuation + "</li>"
        elif line.lstrip().startswith("-"):
            if not in_list:
                html.append("<ul>")
                in_list = True
            content = line.lstrip()[1:].strip()
            html.append(f"<li>{_markdown_inline(content)}</li>")
        else:
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{_markdown_inline(line)}</p>")
        index += 1
    if in_list:
        html.append("</ul>")
    return "".join(html)


def _markdown_table_to_html(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    if len(rows) < 2:
        return f"<p>{_markdown_inline(lines[0])}</p>"
    header = rows[0]
    body = [row for row in rows[2:] if not all(set(cell) <= {"-", ":", " "} for cell in row)]
    result = ["<table><thead><tr>"]
    result.extend(f"<th>{_markdown_inline(cell)}</th>" for cell in header)
    result.append("</tr></thead><tbody>")
    for row in body:
        result.append("<tr>")
        result.extend(f"<td>{_markdown_inline(cell)}</td>" for cell in row)
        result.append("</tr>")
    return "".join(result) + "</tbody></table>"


def _markdown_inline(value: str) -> str:
    escaped = escape(value)
    escaped = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return re.sub(
        r"\[([^\]]+)\]\(dmtools://entity/([A-Za-z0-9._:-]+)\)",
        r'<a class="entity-link" href="dmtools://entity/\2">\1</a>',
        escaped,
    )
