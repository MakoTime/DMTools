from dataclasses import asdict, dataclass, replace
import json
from functools import lru_cache
from pathlib import Path
import re
from typing import Literal

from application.rules_catalog import _RULE_DESCRIPTIONS


EntityNamespace = Literal["compendium", "homebrew", "collection"]

_SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
_RULE_SCHEMA_CATEGORIES = {
    "ability_score": "ability_score",
    "alignment": "alignment",
    "class_name": "class_name",
    "condition": "conditions",
    "creature_type": "creature_type",
    "damage_type": "damage_type",
    "language": "proficiencies-languages",
    "skill": "proficiencies-skills",
    "tool": "proficiencies-tools",
    "armor_proficiency": "proficiencies-armor",
    "armor_category": "proficiencies-armor",
    "armor_type": "proficiencies-armor",
    "instrument": "proficiencies-instruments",
    "gaming_set": "proficiencies-gaming_sets",
    "vehicle": "proficiencies-vehicles",
    "weapon_category": "weapons-groups",
    "weapon_tag": "weapons-tags",
    "weapon_property": "weapons-tags",
    "weapon_type": "weapons-types",
    "item_category": "item_category",
    "size": "size",
    "sense_type": "sense",
    "spell_component": "spell_component",
    "spell_school": "spell_school",
    "movement_type": "movement_type",
    "spellcasting_progression": "spellcasting_progression",
    "target_zone": "target_zone",
    "action_type": "action_type",
    "currency": "currency",
    "rarity": "rarity",
    "spell_level": "spell_level",
}
DISABLED_RULE_CATEGORIES = frozenset(
    {
        "ability_kind",
        "attack_type",
        "bonus_type",
        "casting_time",
        "distance_type",
        "duration",
        "recharge",
        "target_type",
        "targeting",
    }
)
_RULE_METADATA_KEYS = {"description", "handbook_reference"}
_RULE_CATEGORY_SCHEMA_NAMES = {
    "ability_score": ("ability_score",),
    "alignment": ("alignment",),
    "conditions": ("condition",),
    "creature_type": ("creature_type",),
    "damage_type": ("damage_type",),
    "proficiencies-languages": ("language",),
    "proficiencies-skills": ("skill",),
    "proficiencies-tools": ("tool",),
    "proficiencies-armor": ("armor_proficiency", "armor_category", "armor_type"),
    "proficiencies-instruments": ("instrument",),
    "proficiencies-gaming_sets": ("gaming_set",),
    "proficiencies-vehicles": ("vehicle",),
    "weapons-groups": ("weapon_category",),
    "weapons-tags": ("weapon_property", "weapon_tag"),
    "weapons-types": ("weapon_type",),
    "item_category": ("item_category",),
    "size": ("size",),
    "sense": ("sense_type",),
    "spell_component": ("spell_component",),
    "spell_school": ("spell_school",),
    "movement_type": ("movement_type",),
    "spellcasting_progression": ("spellcasting_progression",),
    "target_zone": ("target_zone",),
    "action_type": ("action_type",),
    "currency": ("currency",),
    "rarity": ("rarity",),
}
_RULE_CONTEXTS = {
    "ability_score": r"\b(?:saving throw|save|ability|check|modifier|score)s?\b",
    "alignment": (
        r"\balign(?:ed|ment)\b|\b{value}\s+alignment\b|"
        r"\b{value}\s+aligned\b|\bcreature\s+of\s+{value}\b|"
        r"\b(?:detect|detects|detected|detecting)\s+{value}\b|"
        r"\bprotection\s+from\s+{value}\b|"
        r"\b(?:damage|immune|immunity|resistance|resistant)\s+(?:to\s+)?"
        r"{value}\b"
    ),
    "conditions": r"\bcondition\b|\b(?:becomes?|is|are|while)\s+{value}\b",
    "damage_type": (
        r"\b{value}\s+damage\b|\bdamage\s+{value}\b|"
        r"\b(?:resistance|resistant|immunity|immune|vulnerability|vulnerable)"
        r"\s+(?:to\s+)?{value}\b|"
        r"\b(?:deal|deals|dealing|take|takes|taking)\s+{value}\s+damage\b"
    ),
    "spell_school": (
        r"\bspell\s+school\b|\bschool\s+of\s+magic\b|"
        r"\b{value}\s+(?:school|spell)\b"
    ),
    "spellcasting_progression": r"\bspellcasting\b|\bspell slots?\b",
    "spell_component": (
        r"\bcomponents?\b|\b{value}\s+component\b|"
        r"\b(?:speak|spoken|gesture|focus|subtle)\b"
    ),
    "proficiencies-languages": r"\blanguages?\b|\blanguage proficien(?:cy|cies)\b",
    "proficiencies-skills": r"\bskills?\b|\bskill proficien(?:cy|cies)\b",
    "proficiencies-tools": r"\btools?\b|\btool proficien(?:cy|cies)\b|\bkits?\b",
    "proficiencies-armor": r"\b(?:armor|armour)\b|\barmor proficien(?:cy|cies)\b",
    "proficiencies-instruments": r"\binstruments?\b|\binstrument proficien(?:cy|cies)\b",
    "proficiencies-gaming_sets": r"\bgaming sets?\b|\bgaming[- ]set proficien(?:cy|cies)\b",
    "proficiencies-vehicles": r"\bvehicles?\b|\bvehicle proficien(?:cy|cies)\b",
    "weapons-tags": r"\bweapon\b|\battack\b",
    "weapons-groups": r"\bweapon\b|\bproficien(?:cy|cies)\b",
    "weapons-types": r"\bweapon\b|\battack\b",
    "action_type": (
        r"\b(?:action|bonus action|reaction|legendary action|lair action|"
        r"mythic action)\b|\b(?:take|takes|use|uses|using|spend|spends)\s+"
        r"(?:an?\s+)?{value}\b"
    ),
    "movement_type": (
        r"\b(?:movement|movement speed|speed)\b|"
        r"\b(?:can|cannot|can't|gains?|loses?|grants?|reduces?|increases?)\s+"
        r"(?:a\s+)?{value}\b|\b{value}\s+(?:speed|movement)\b"
    ),
    "target_zone": r"\b(?:area|zone|shape)\b",
    "currency": r"\b(?:cost|price|value|currency|coins?|pieces?)\b",
    "rarity": r"\b(?:rarity|magic item)\b",
    "sense": (
        r"\bsenses?\b|\bvision\b|\bperceiv(?:e|es|ed|ing)\b|"
        r"\bsee\s+through\b|\bblind(?:ed|ness)?\b|"
        r"\b(?:has|have|gains?|grants?|loses?|without)\s+{value}\b|"
        r"\b{value}\s+(?:vision|sense|range)\b"
    ),
    "size": r"\b(?:size|creature)\b",
    "creature_type": (
        r"\bcreature\s+type\b|\btype\s+of\s+creature\b|"
        r"\b{value}\s+(?:creature|monsters?)\b|"
        r"\b(?:creature|monsters?)\s+(?:of|with)\s+{value}\b|"
        r"\b(?:affect|affects|affected|affecting|target|targets|targeted|"
        r"exclude|excludes|excluded|excluding)\s+(?:a\s+|an\s+|the\s+)?"
        r"{value}\b|\b(?:to|against|at)\s+(?:a\s+|an\s+|the\s+)?{value}\b"
    ),
    "item_category": r"\b(?:item|equipment|gear)\b",
}
_PROSE_REFERENCE_FIELDS = {
    "action",
    "description",
    "effect",
    "effects",
    "entries",
    "feature",
    "grant",
    "higher_level",
    "notes",
    "prerequisite",
    "requirements",
    "reaction",
    "special",
    "summary",
    "text",
    "trait",
}


@dataclass(frozen=True)
class EntityReference:
    target_uid: str
    entity_type: str
    source_namespace: EntityNamespace
    display_fallback: str | None = None


@dataclass(frozen=True)
class ReferenceDiagnostic:
    path: str
    entity_type: str
    display_fallback: str
    status: Literal["missing", "ambiguous"]
    candidate_uids: tuple[str, ...] = ()


def normalize_entity_references(
    records,
    existing_entities=(),
    *,
    source_namespace="compendium",
    is_cancelled=None,
    progress_callback=None,
):
    """Attach UID references for known structured links without changing payloads."""
    records = tuple(records)
    index = {}
    for entity in (*tuple(existing_entities), *records):
        key = (entity.entity_type, _reference_key(_entity_name(entity)))
        index.setdefault(key, {})[entity.uid] = entity
    spell_index = {}
    spell_names = {}
    spell_pattern_names = []
    for entity in (*tuple(existing_entities), *records):
        if entity.entity_type != "spell" or not _entity_name(entity):
            continue
        display_name = _entity_name(entity)
        for form in _spell_reference_forms(display_name):
            spell_names[_reference_key(form)] = display_name
            spell_index.setdefault(_reference_key(form), {})[entity.uid] = entity
            spell_pattern_names.append(form)
    item_names = {}
    item_pattern_names = []
    for entity in (*tuple(existing_entities), *records):
        if entity.entity_type != "item" or not _entity_name(entity):
            continue
        item_name = _entity_name(entity)
        for form in _reference_forms(item_name):
            item_names[_reference_key(form)] = item_name
            item_pattern_names.append(form)
    item_pattern = _compile_name_pattern(item_pattern_names)
    spell_pattern = _compile_name_pattern(spell_pattern_names)
    normalized = []
    for record in records:
        if is_cancelled is not None and is_cancelled():
            break
        references = []
        diagnostics = []
        candidates = list(extract_reference_candidates(record.entity_type, record.payload))
        rule_candidates = list(
            _extract_schema_rule_candidates(record.entity_type, record.payload)
        )
        rule_candidates.extend(_extract_text_rule_candidates(record.payload))
        candidates.extend(
            _extract_weak_item_candidates(
                record.entity_type, record.payload, item_names, item_pattern
            )
        )
        if record.entity_type != "spell":
            candidates.extend(
                _extract_text_spell_candidates(
                    record.payload, spell_names, spell_pattern, item_pattern
                )
            )
        seen_candidates = set()
        seen_rules = set()
        for path, category, value in rule_candidates:
            rule_key = (category, _reference_key(value))
            if rule_key in seen_rules:
                continue
            seen_rules.add(rule_key)
            references.append(
                {
                    "path": path,
                    "category": category,
                    "value": value,
                    "target_uid": f"dmtools-compendium-rules-{category}-{value}",
                    "entity_type": "rule",
                    "source_namespace": "compendium",
                    "display_fallback": _link_display_name(value),
                }
            )
        for path, entity_type, name in candidates:
            resolved_entity_type = entity_type
            lookup_name = name
            if entity_type == "spell":
                lookup_name = _normalize_spell_reference_name(name)
            elif entity_type == "class":
                subclass_match = re.fullmatch(r".+\s+\(([^()]+)\)", name.strip())
                if subclass_match:
                    resolved_entity_type = "subclass"
                    lookup_name = subclass_match.group(1).strip()
            candidate_key = (resolved_entity_type, _reference_key(lookup_name))
            if candidate_key in seen_candidates:
                continue
            seen_candidates.add(candidate_key)
            matches = tuple(
                (spell_index if resolved_entity_type == "spell" else index)
                .get(candidate_key[1] if resolved_entity_type == "spell" else candidate_key, {})
                .values()
            )
            canonical_spell_match = False
            if resolved_entity_type == "spell" and len(matches) > 1:
                canonical_matches = tuple(
                    match
                    for match in matches
                    if _entity_name(match).casefold()
                    == _spell_reference_forms(_entity_name(match))[-1].casefold()
                )
                if len(canonical_matches) == 1:
                    matches = canonical_matches
                    canonical_spell_match = True
            if len(matches) == 1:
                target = matches[0]
                namespace = getattr(target, "source_namespace", source_namespace)
                references.append(
                    {
                        "path": path,
                        **asdict(
                            EntityReference(
                                target_uid=target.uid,
                                entity_type=resolved_entity_type,
                                source_namespace=namespace,
                                display_fallback=(
                                    _link_display_name(_entity_name(target))
                                    if canonical_spell_match
                                    else _link_display_name(
                                        lookup_name if entity_type == "spell" else name
                                    )
                                ),
                            )
                        ),
                    }
                )
            else:
                diagnostics.append(
                    asdict(
                        ReferenceDiagnostic(
                            path=path,
                            entity_type=resolved_entity_type,
                            display_fallback=_link_display_name(name),
                            status="ambiguous" if matches else "missing",
                            candidate_uids=tuple(item.uid for item in matches),
                        )
                    )
                )
        metadata = dict(record.source_metadata)
        metadata.pop("entity_references", None)
        metadata.pop("reference_diagnostics", None)
        if references:
            metadata["entity_references"] = references
        if diagnostics:
            metadata["reference_diagnostics"] = diagnostics
        normalized.append(replace(record, source_metadata=metadata))
        if progress_callback is not None:
            progress_callback(len(normalized), len(records))
    if progress_callback is not None and not records:
        progress_callback(0, 0)
    return tuple(normalized)


@lru_cache(maxsize=None)
def _load_schema(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _schema_path(reference, current_path):
    if not isinstance(reference, str):
        return None
    if reference.startswith("#"):
        return current_path, reference[1:]
    return (current_path.parent / reference).resolve(), None


def _schema_fragment(schema, fragment):
    if not fragment:
        return schema
    value = schema
    for part in fragment.lstrip("/").split("/"):
        value = value.get(part.replace("~1", "/").replace("~0", "~"), {})
    return value


def _catalog_values(category):
    entry = _RULE_DESCRIPTIONS.get(category)
    values = {
        key for key in (entry or {}) if key not in _RULE_METADATA_KEYS
    }
    for schema_name in _RULE_CATEGORY_SCHEMA_NAMES.get(category, ()):
        schema = _load_schema(_SCHEMA_ROOT / "values" / f"{schema_name}.schema.json")
        values.update(_schema_enum_values(schema))
    return frozenset(values)


def _schema_enum_values(schema):
    if not isinstance(schema, dict):
        return set()
    values = set(schema.get("enum", ()))
    for key in ("anyOf", "oneOf", "allOf"):
        for child in schema.get(key, ()):
            values.update(_schema_enum_values(child))
    return values


def _category_for_schema(schema_path, property_name=None):
    stem = schema_path.stem.removesuffix(".schema")
    category = _RULE_SCHEMA_CATEGORIES.get(stem)
    if category is None:
        category = _RULE_SCHEMA_CATEGORIES.get(str(property_name or ""))
    if category not in _RULE_DESCRIPTIONS:
        return None
    return category


def _extract_schema_rule_candidates(entity_type, payload):
    entity_path = _SCHEMA_ROOT / "entities" / f"{entity_type.title()}.schema.json"
    schema = _load_schema(entity_path)
    if schema is None:
        return ()
    candidates = []

    def visit(current_schema, value, current_path, data_path, property_name=None):
        if not isinstance(current_schema, dict):
            return
        reference = current_schema.get("$ref")
        if reference:
            resolved = _schema_path(reference, current_path)
            if resolved is None:
                return
            referenced_path, fragment = resolved
            if referenced_path == current_path:
                referenced_schema = _schema_fragment(_load_schema(referenced_path), fragment)
                visit(referenced_schema, value, referenced_path, data_path, property_name)
                return
            referenced_schema = _load_schema(referenced_path)
            if referenced_schema is None:
                return
            referenced_schema = _schema_fragment(referenced_schema, fragment)
            category = _category_for_schema(referenced_path, property_name)
            if category and isinstance(value, str):
                enum_values = _schema_enum_values(referenced_schema)
                canonical_value = value
                if category == "proficiencies-armor" and value.casefold() == "shields":
                    canonical_value = "shield"
                if (
                    canonical_value in enum_values or category == "alignment"
                ) and canonical_value in _catalog_values(category):
                    candidates.append((data_path, category, canonical_value))
                if category == "damage_type":
                    candidates.extend(
                        (data_path, category, embedded_value)
                        for embedded_value in _embedded_rule_values(category, value)
                    )
            visit(referenced_schema, value, referenced_path, data_path, property_name)
            return
        for key in ("allOf", "anyOf", "oneOf"):
            for alternative in current_schema.get(key, ()):
                visit(alternative, value, current_path, data_path, property_name)
        if isinstance(value, dict):
            properties = current_schema.get("properties", {})
            for name, child in value.items():
                visit(properties.get(name), child, current_path, f"{data_path}.{name}", name)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(current_schema.get("items"), child, current_path, f"{data_path}[{index}]", property_name)

        if isinstance(value, str):
            enum_values = set(current_schema.get("enum", ()))
            category = _category_for_schema(current_path, property_name)
            if (
                category
                and (value in enum_values or category == "alignment")
                and value in _catalog_values(category)
            ):
                candidates.append((data_path, category, value))

    visit(schema, payload, entity_path, "payload")
    return tuple(dict.fromkeys(candidates))


def _text_rule_value_pattern(category):
    values = _catalog_values(category)
    names = {value.replace("_", " "): value for value in values}
    if category == "creature_type":
        names.update({f"{name}s": value for name, value in tuple(names.items())})
    if not names:
        return None, {}
    pattern = _compile_name_pattern(names)
    return pattern, {match_key.casefold(): value for match_key, value in names.items()}


def _embedded_rule_values(category, text):
    pattern, values = _text_rule_value_pattern(category)
    if pattern is None:
        return ()
    return tuple(
        dict.fromkeys(
            values[match.group(0).casefold()]
            for match in pattern.finditer(text)
        )
    )


def _extract_text_rule_candidates(payload):
    candidates = []
    for path, text in _text_values(payload):
        field_name = re.sub(r"\[\d+\]", "", path.rsplit(".", 1)[-1]).casefold()
        if field_name not in _PROSE_REFERENCE_FIELDS:
            continue
        for category, context_pattern in _RULE_CONTEXTS.items():
            pattern, values = _text_rule_value_pattern(category)
            if pattern is None:
                continue
            for match in pattern.finditer(text):
                value = values.get(match.group(0).casefold())
                if value is None:
                    continue
                context = text[max(0, match.start() - 80):match.end() + 80]
                if _rule_context_matches(
                    category, match.group(0), context, context_pattern
                ):
                    candidates.append((f"{path}:text", category, value))
    return tuple(dict.fromkeys(candidates))


def _rule_context_matches(category, matched_value, context, context_pattern):
    escaped_value = re.escape(matched_value)
    if category == "weapons-tags":
        return re.search(
            rf"\b{escaped_value}\s+(?:melee\s+|ranged\s+)?weapon\b|"
            rf"\bweapon\s+(?:with\s+)?{escaped_value}\b",
            context,
            re.IGNORECASE,
        ) is not None
    if category == "action_type" and matched_value.casefold() == "action" and re.search(
        r"\b(?:cast|casts|casting|spell|spells)\b", context, re.IGNORECASE
    ):
        return False
    context_source = context_pattern.replace("{value}", escaped_value)
    return re.search(context_source, context, re.IGNORECASE) is not None


def _normalize_spell_reference_name(name: str) -> str:
    value = re.sub(r"^(?:and|or)\s+", "", name.strip(), flags=re.IGNORECASE)
    value = re.sub(r"\s*\*.*$", "", value).strip()
    return re.sub(r"[.,;:!?]+$", "", value).strip()


_LINK_DISPLAY_CONNECTORS = frozenset(
    {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "nor", "of", "on", "or", "the", "to", "with"}
)


def _link_display_name(value: str) -> str:
    """Format link labels while keeping natural-language connector words lowercase."""
    text = str(value).replace("_", " ").strip()
    words = list(re.finditer(r"[A-Za-z]+(?:['’][A-Za-z]+)?", text))
    if not words:
        return text
    last_index = len(words) - 1
    result = []
    cursor = 0
    for index, match in enumerate(words):
        result.append(text[cursor:match.start()])
        word = match.group(0)
        lowered = word.casefold()
        if 0 < index < last_index and lowered in _LINK_DISPLAY_CONNECTORS:
            result.append(lowered)
        else:
            result.append(word[:1].upper() + word[1:].lower())
        cursor = match.end()
    result.append(text[cursor:])
    return "".join(result)


def _spell_reference_forms(name: str):
    forms = [name]
    cleaned = re.sub(r"[*\u2020\u2021]+", "", name).strip()
    cleaned = re.sub(r"\s*\([^()]*\)\s*$", "", cleaned).strip()
    if cleaned and cleaned.casefold() != name.casefold():
        forms.append(cleaned)
    return tuple(forms)


def _reference_key(name: str) -> str:
    value = name.casefold().replace("_", " ")
    return re.sub(r"[^\w]+", " ", value).strip()


def _compile_name_pattern(names):
    names = sorted(set(names), key=lambda name: (-len(name), name.casefold()))
    if not names:
        return None
    return re.compile(
        rf"(?<!\w)(?:{'|'.join(re.escape(name) for name in names)})(?!\w)",
        re.IGNORECASE,
    )


def _reference_forms(name):
    forms = [name]
    words = name.split()
    if words:
        last = words[-1]
        if last.endswith("y") and len(last) > 1 and last[-2].lower() not in "aeiou":
            plural = f"{last[:-1]}ies"
        elif last.endswith(("s", "x", "z", "ch", "sh")):
            plural = f"{last}es"
        else:
            plural = f"{last}s"
        forms.append(" ".join((*words[:-1], plural)))
    return tuple(forms)


def _extract_weak_item_candidates(entity_type, payload, item_names, item_pattern):
    candidates = []
    if entity_type in {"class", "background", "race", "feat"}:
        for field in ("tool_proficiencies", "weapon_proficiencies", "armor_proficiencies"):
            for index, value in enumerate(payload.get(field) or []):
                if not isinstance(value, str):
                    continue
                if field == "tool_proficiencies" and len(_reference_key(value).split()) < 2:
                    continue
                if _reference_key(value) in item_names:
                    candidates.append((f"{field}[{index}]", "item", item_names[_reference_key(value)]))
    if entity_type in {"class", "background", "character"} and item_pattern is not None:
        descriptions = []
        if isinstance(payload.get("description"), str):
            descriptions.extend(
                ("payload.description:text", section)
                for section in _equipment_reference_sections(payload["description"])
            )
        for index, feature in enumerate(payload.get("features") or []):
            if not isinstance(feature, dict) or not isinstance(feature.get("description"), str):
                continue
            sections = _equipment_reference_sections(feature["description"])
            feature_name = str(feature.get("name", "")).casefold()
            if "equipment" in feature_name and not sections:
                sections = (feature["description"],)
            descriptions.extend(
                (f"features[{index}].description:text", section)
                for section in sections
            )
        for path, description in descriptions:
            for match in item_pattern.finditer(description):
                item_name = item_names.get(_reference_key(match.group(0)))
                if item_name is not None:
                    candidates.append((path, "item", item_name))
    return candidates


def _equipment_reference_sections(text):
    return tuple(
        text[start:end]
        for start, end in _equipment_reference_ranges(text)
    )


def _equipment_reference_ranges(text):
    ranges = [
        (match.start(), match.end())
        for match in re.finditer(
            r"(?im)^[ \t]*(?:[-*]|\u2022)?[ \t]*(?:armor|armour|equipment|tools?|weapons?)\s*:[^\n]*$",
            text,
        )
    ]
    equipment_start = re.search(
        r"\b(?:following\s+(?:equipment|items|proficiencies)|proficiencies\s+gained)\b",
        text,
        re.IGNORECASE,
    )
    if equipment_start is not None:
        equipment_end = re.search(
            r"\bAlternatively\b", text[equipment_start.end():], re.IGNORECASE
        )
        end = (
            equipment_start.end() + equipment_end.start()
            if equipment_end is not None
            else len(text)
        )
        ranges.append((equipment_start.start(), end))
    return tuple(ranges)


def _extract_text_spell_candidates(
    payload, spell_names, spell_pattern, item_pattern=None
):
    candidates = []
    if spell_pattern is None:
        return candidates
    for path, text in _text_values(payload):
        field_name = re.sub(r"\[\d+\]$", "", path.rsplit(".", 1)[-1]).casefold()
        if field_name not in _PROSE_REFERENCE_FIELDS:
            continue
        item_section_ranges = _equipment_reference_ranges(text)
        for section_start, section_end in _spell_reference_ranges(text):
            section = text[section_start:section_end]
            for match in spell_pattern.finditer(section):
                absolute_start = section_start + match.start()
                absolute_end = section_start + match.end()
                if any(
                    item_start < absolute_end and absolute_start < item_end
                    for item_start, item_end in item_section_ranges
                ):
                    continue
                if item_pattern is not None and any(
                    item_match.start() < absolute_end
                    and absolute_start < item_match.end()
                    for item_match in item_pattern.finditer(text)
                ):
                    continue
                name = spell_names.get(_reference_key(match.group(0)))
                if name is None:
                    continue
                if _is_choice_list_false_positive(text, absolute_start, absolute_end, name):
                    continue
                if len(name.split()) == 1 and not re.search(
                    r"\b(?:cast|casts|casting|spell|spells|learn|learns|prepare|prepared|known|invoke|invokes|conjure|conjures)\b",
                    f"{_local_reference_context(text, absolute_start, absolute_end)} {section}",
                    re.IGNORECASE,
                ) and not re.search(
                    r"\b\d{1,2}(?:st|nd|rd|th)\s*[—-]", section, re.IGNORECASE
                ):
                    continue
                candidates.append((f"{path}:text", "spell", name))
    return candidates


def _local_reference_context(text, start, end):
    paragraph_start = text.rfind("\n\n", 0, start) + 2
    paragraph_end = text.find("\n\n", end)
    if paragraph_end == -1:
        paragraph_end = len(text)
    return text[paragraph_start:paragraph_end][:]


def _spell_reference_ranges(text):
    paragraphs = [
        (paragraph.start(), paragraph.end(), paragraph.group(0).strip())
        for paragraph in re.finditer(r"(?s).*?(?:\n\s*\n|\Z)", text)
    ]
    ranges = []
    index = 0
    while index < len(paragraphs):
        start, end, content = paragraphs[index]
        if not content or not re.search(
            r"\b(?:cast|casts|casting|cantrip|cantrips|spell|spells|prepared|prepare|learn|learns|known|invoke|invokes|conjure|conjures|"
            r"choose|chooses|choice|choices|option|options|available|granted|grant|gained)\b|"
            r"\b(?:following\s+spells|spell\s+list|spells?\s+table|domain\s+spells|on\s+spell\s+lists?)\b|"
            r"\b\d{1,2}(?:st|nd|rd|th)\s*[—-]",
            content,
            re.IGNORECASE,
        ):
            index += 1
            continue

        range_end = end
        next_index = index + 1
        while next_index < len(paragraphs):
            continuation_start, continuation_end, continuation = paragraphs[next_index]
            if not re.match(
                r"(?:[-*\u2022]\s*)?(?:\d+\s*/\s*day\b|\d{1,2}(?:st|nd|rd|th)\s+level\b|"
                r"cantrips?\b|at\s+will\b)",
                continuation,
                re.IGNORECASE,
            ):
                break
            range_end = continuation_end
            next_index += 1
        ranges.append((start, range_end))
        index = next_index
    return tuple(ranges)


def _is_choice_list_false_positive(text, start, end, name):
    if len(name.split()) != 1:
        return False
    context = _local_reference_context(text, start, end)
    if not re.search(r"\b(?:choose|choice|domain|school|college|circle|oath|path)\b", context, re.IGNORECASE):
        return False
    return not re.search(
        r"\b(?:cast|casting|cantrip|learn|learns|prepare|prepared|spell\s+slot|spell\s+list|known)\b",
        context,
        re.IGNORECASE,
    )


def _text_values(value, path="payload"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _text_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _text_values(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def extract_reference_candidates(entity_type, payload):
    """Yield schema-backed reference paths, target types, and display names."""
    candidates = []
    if entity_type == "item":
        spells = (payload.get("magic_item") or {}).get("spells") or []
        candidates.extend(
            (f"magic_item.spells[{index}].spell", "spell", item["spell"])
            for index, item in enumerate(spells)
            if isinstance(item, dict) and isinstance(item.get("spell"), str)
        )
    if entity_type in {"feat", "race"}:
        for grant_index, grant in enumerate(payload.get("spell_grants") or []):
            for spell_index, spell in enumerate(grant.get("spells") or []):
                if isinstance(spell, str):
                    candidates.append(
                        (
                            f"spell_grants[{grant_index}].spells[{spell_index}]",
                            "spell",
                            spell,
                        )
                    )
    if entity_type == "class":
        grants = ((payload.get("spellcasting") or {}).get("spells") or [])
        candidates.extend(_spell_grant_names(grants, "spellcasting.spells"))
    if entity_type == "subclass":
        if isinstance(payload.get("class"), str):
            candidates.append(("class", "class", payload["class"]))
        candidates.extend(_spell_grant_names(payload.get("spells") or [], "spells"))
    if entity_type == "monster":
        known = (payload.get("spell_casting") or {}).get("spells_known") or {}
        candidates.extend(_spell_names(known, "spell_casting.spells_known"))
    if entity_type in {"spell", "ability"}:
        for index, class_name in enumerate(payload.get("classes") or []):
            if isinstance(class_name, str):
                candidates.append((f"classes[{index}]", "class", class_name))
    if entity_type == "race":
        for index, feat_name in enumerate(payload.get("feats") or []):
            if isinstance(feat_name, str):
                candidates.append((f"feats[{index}]", "feat", feat_name))
    if entity_type == "character":
        race = payload.get("race") or {}
        if isinstance(race, dict) and isinstance(race.get("name"), str):
            candidates.append(("race.name", "race", race["name"]))
        if isinstance(payload.get("background"), str):
            candidates.append(("background", "background", payload["background"]))
        for index, class_data in enumerate(payload.get("classes") or []):
            if not isinstance(class_data, dict):
                continue
            if isinstance(class_data.get("name"), str):
                candidates.append((f"classes[{index}].name", "class", class_data["name"]))
            if isinstance(class_data.get("subclass"), str):
                candidates.append(
                    (f"classes[{index}].subclass", "subclass", class_data["subclass"])
                )
    if entity_type in {"background", "character"}:
        for index, equipment in enumerate(payload.get("equipment") or []):
            if not isinstance(equipment, dict):
                continue
            item = equipment.get("item")
            item_name = item.get("name") if isinstance(item, dict) else item
            if isinstance(item_name, str):
                candidates.append((f"equipment[{index}].item", "item", item_name))
    return tuple(candidates)


def _spell_grant_names(grants, path):
    candidates = []
    if isinstance(grants, dict):
        grants = [grants]
    for grant_index, grant in enumerate(grants):
        if not isinstance(grant, dict):
            continue
        for spell_index, spell in enumerate(grant.get("spells") or []):
            if isinstance(spell, str):
                candidates.append(
                    (f"{path}[{grant_index}].spells[{spell_index}]", "spell", spell)
                )
    return candidates


def _spell_names(value, path):
    candidates = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"spells", "cantrips", "at_will"} and isinstance(child, list):
                candidates.extend(
                    (f"{child_path}[{index}]", "spell", name)
                    for index, name in enumerate(child)
                    if isinstance(name, str)
                )
            else:
                candidates.extend(_spell_names(child, child_path))
    return candidates


def _entity_name(entity):
    return getattr(entity, "display_name", getattr(entity, "name", ""))


class EntityNavigationController:
    """Resolve canonical references while retaining reversible navigation context."""

    def __init__(self, project_controller, on_open=None):
        self.project_controller = project_controller
        self.on_open = on_open
        self._history = []
        self._cache = {}

    def open(self, reference, *, origin_uid=None):
        if reference.target_uid in self._history:
            raise ValueError(f"Circular entity navigation: {reference.target_uid}")
        entity = self._cache.get(reference.target_uid)
        if entity is None:
            entity = self.project_controller.resolve_entity_reference(reference)
            self._cache[reference.target_uid] = entity
        if origin_uid is not None:
            self._history.append(origin_uid)
        if self.on_open is not None:
            self.on_open(entity)
        return entity

    def back(self):
        if not self._history:
            return None
        entity_uid = self._history.pop()
        entity = self._cache.get(entity_uid)
        if entity is None:
            entity = self.project_controller.resolve_entity(entity_uid)
            self._cache[entity_uid] = entity
        if self.on_open is not None:
            self.on_open(entity)
        return entity