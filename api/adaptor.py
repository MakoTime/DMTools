from __future__ import annotations

import re
from typing import Any

from parsers.monster_adaptor import MonsterAdaptor as XMLMonsterAdaptor
from parsers.spell_adaptor import SpellAdaptor as XMLSpellAdaptor


COLLECTION_TYPES = {
    "monsters": "monster",
    "spells": "spell",
    "classes": "class",
    "races": "race",
    "backgrounds": "background",
    "feats": "feat",
    "equipment": "item",
    "subclasses": "subclass",
}


class SRDAdaptor:
    """Translate 5eSRD responses into the project's canonical payloads."""

    def adapt(self, collection: str, source: dict[str, Any]) -> dict[str, Any]:
        entity_type = COLLECTION_TYPES.get(collection)
        if entity_type is None:
            raise ValueError(f"Unsupported 5eSRD collection: {collection}")
        method = getattr(self, f"_{entity_type}", None)
        if method is None:
            raise ValueError(f"No 5eSRD adaptor exists for {collection}")
        return method(source)

    def record(self, collection: str, source: dict[str, Any], *, parent=None) -> dict[str, Any]:
        payload = self.adapt(collection, source)
        if collection == "subclasses" and parent:
            payload["class_name"] = payload.get("class_name") or parent.get("name")
        name = payload.get("name")
        return {
            "entity_type": COLLECTION_TYPES[collection],
            "display_name": name,
            "payload": payload,
            "source_identity": f"5esrd:{collection}:{source.get('index', name)}",
            "source_metadata": {
                "api_url": source.get("url", ""),
                "api_source": source,
            },
            "provenance": "5eSRD Online",
        }

    @staticmethod
    def _monster(source):
        armor_class = source.get("armor_class", [])
        armor = armor_class[0] if isinstance(armor_class, list) and armor_class else armor_class
        armor_text = None
        if isinstance(armor, dict):
            armor_text = str(armor.get("value", ""))
            armor_types = ", ".join(
                item.get("name", "") for item in armor.get("armor", []) if item.get("name")
            )
            if armor.get("desc") or armor_types:
                armor_text += f" ({armor.get('desc') or armor_types})"
        elif armor is not None:
            armor_text = str(armor)

        speed = source.get("speed", {})
        speed_text = ", ".join(
            f"{key} {value}" for key, value in speed.items() if key != "hover" and value
        )
        proficiencies = source.get("proficiencies", [])
        saving_throws = []
        skills = []
        for proficiency in proficiencies:
            name = proficiency.get("proficiency", {}).get("name", "")
            value = proficiency.get("value")
            if value is None:
                continue
            if name.startswith("Saving Throw:"):
                saving_throws.append(f"{name.rsplit(':', 1)[1].strip()} {value:+d}")
            elif name.startswith("Skill:"):
                skills.append(f"{name.rsplit(':', 1)[1].strip()} {value:+d}")

        def descriptions(items):
            return [
                {"name": item.get("name"), "text": [item.get("desc", "")]}
                for item in items
                if item.get("name") and item.get("desc")
            ]

        intermediate = {
            "name": source.get("name"),
            "size": source.get("size"),
            "type": source.get("type"),
            "alignment": source.get("alignment"),
            "ability_scores": {
                abbreviation: source.get(ability)
                for abbreviation, ability in {
                    "str": "strength",
                    "dex": "dexterity",
                    "con": "constitution",
                    "int": "intelligence",
                    "wis": "wisdom",
                    "cha": "charisma",
                }.items()
            },
            "ac": armor_text,
            "hp": f"{source.get('hit_points', 0)} ({source.get('hit_dice', '')})",
            "speed": speed_text,
            "saves": ", ".join(saving_throws),
            "skills": ", ".join(skills),
            "resistances": ", ".join(source.get("damage_resistances", [])),
            "vulnerabilities": ", ".join(source.get("damage_vulnerabilities", [])),
            "immunities": ", ".join(source.get("damage_immunities", [])),
            "condition_immunities": ", ".join(
                _unique_names(
                    item.get("name", item) if isinstance(item, dict) else item
                    for item in source.get("condition_immunities", [])
                )
            ),
            "senses": ", ".join(
                f"{name} {value}" for name, value in source.get("senses", {}).items()
            ),
            "passive": source.get("senses", {}).get("passive_perception"),
            "languages": source.get("languages"),
            "proficiency_bonus": source.get("proficiency_bonus"),
            "traits": descriptions(source.get("special_abilities", [])),
            "actions": descriptions(source.get("actions", [])),
            "reactions": descriptions(source.get("reactions", [])),
            "legendary_actions": descriptions(source.get("legendary_actions", [])),
            "cr": source.get("challenge_rating", 0),
            "environment": source.get("environment", []),
        }
        payload = XMLMonsterAdaptor().adapt(intermediate)
        if source.get("image"):
            payload["image"] = {
                "uri": source["image"],
                "alt": source.get("name", "Monster"),
            }
        if source.get("proficiency_bonus") is not None:
            payload["proficiency_bonus"] = source["proficiency_bonus"]
        return payload

    @staticmethod
    def _class(source):
        proficiencies = _names(source.get("proficiencies"))
        levels = source.get("class_levels", [])
        result = {
            "name": source["name"],
            "hit_dice": source.get("hit_die", 1),
            "description": _description(source.get("desc")),
            "saving_throws": _ability_names(source.get("saving_throws")),
            "armor_proficiencies": [
                _proficiency_name(name)
                for name in proficiencies
                if "armor" in name.lower() or "shield" in name.lower()
            ] or None,
            "weapon_proficiencies": [
                _proficiency_name(name)
                for name in proficiencies
                if not any(
                    term in name.lower()
                    for term in ("armor", "shield", "saving throw", "skill:", "tool:")
                )
            ] or None,
            "tool_proficiencies": [
                _proficiency_name(name)
                for name in proficiencies
                if "tool" in name.lower()
            ] or None,
            "skill_choices": _choice(source.get("proficiency_choices")),
            "features": _class_features(source),
            "required_stats": _ability_names(
                prerequisite.get("ability_score")
                for prerequisite in (source.get("multi_classing") or {}).get("prerequisites", [])
            ),
            "ability_score_increase": [
                level.get("level")
                for previous, level in zip(
                    [0, *[item.get("ability_score_bonuses", 0) for item in levels]],
                    levels,
                )
                if level.get("ability_score_bonuses", 0) > previous
            ] or None,
        }
        spellcasting = source.get("spellcasting") or {}
        ability = _ability_name(spellcasting.get("spellcasting_ability"))
        if ability:
            result["spellcasting"] = {
                "ability": ability,
                "progression": _class_progression(source),
            }
            spellcasting_text = " ".join(
                _description(feature.get("desc") or feature.get("description")) or ""
                for level in levels
                for feature in level.get("features", [])
                if isinstance(feature, dict)
                and feature.get("name", "").casefold() == "spellcasting"
            ).casefold()
            if "ritual" in spellcasting_text:
                result["spellcasting"]["ritual"] = True
            if "prepare" in spellcasting_text:
                result["spellcasting"]["prepared"] = True
            spells = _spell_grants(source.get("spells"))
            if spells:
                result["spellcasting"]["spells"] = spells[0]
        return {key: value for key, value in result.items() if value is not None}

    @staticmethod
    def _spell(source):
        xml_adaptor = XMLSpellAdaptor()
        duration = source.get("duration", "Instantaneous")
        casting_time = source.get("casting_time", "1 action")
        components = source.get("components", [])
        component_text = ", ".join(components) if isinstance(components, list) else components
        school = source.get("school")
        school = school.get("name") if isinstance(school, dict) else school
        range_value = source.get("range")
        if isinstance(range_value, dict):
            range_value = range_value.get("text") or range_value.get("normal")
        result = {
            "name": source["name"],
            "description": "\n\n".join(source.get("desc", [])) if isinstance(source.get("desc"), list) else source.get("desc", ""),
            "higher_level": "\n\n".join(source.get("higher_level", [])) if isinstance(source.get("higher_level"), list) else source.get("higher_level"),
            "level": source.get("level", 0),
            "school": xml_adaptor.school(school),
            "classes": [
                str(item.get("name", item) if isinstance(item, dict) else item)
                .strip()
                .casefold()
                for item in source.get("classes", [])
            ] or None,
            "casting_time": xml_adaptor.casting_time(casting_time),
            "target": xml_adaptor.target(range_value),
            "components": xml_adaptor.components(component_text),
            "material": _spell_material(source, component_text),
            "duration": xml_adaptor.duration(duration),
            "ritual": source.get("ritual", False),
            "concentration": source.get("concentration", xml_adaptor.concentration(duration)),
        }
        description = result["description"]
        effects = xml_adaptor.effects(description)
        if effects:
            result["effects"] = effects
        if source.get("url"):
            result["source"] = {"href": source["url"]}
        return result

    @staticmethod
    def _background(source):
        feature = source.get("feature") or {}
        result = {
            "name": source["name"],
            "description": _description(source.get("desc")),
            "skill_proficiencies": _proficiency_names(source.get("starting_proficiencies")),
            "languages": _lower_names(source.get("languages")),
            "features": _features([feature]) if feature else None,
            "source": _source(source),
        }
        return {key: value for key, value in result.items() if value is not None}

    @staticmethod
    def _feat(source):
        result = {
            "name": source["name"],
            "description": _description(source.get("desc")),
            "prerequisite": _prerequisite(source.get("prerequisites")),
            "ability_score_increases": _ability_increases(source.get("ability_score_bonuses")),
            "weapon_proficiencies": _names(source.get("proficiencies")) or None,
            "source": _source(source),
        }
        return {key: value for key, value in result.items() if value is not None}

    @staticmethod
    def _race(source):
        speed = source.get("speed") or {}
        result = {
            "name": source["name"],
            "subtype": source.get("subrace") or None,
            "size": str(source["size"]).strip().casefold() if source.get("size") else None,
            "movement": _race_movement(speed),
            "languages": _lower_names(source.get("languages")),
            "ability_score_increases": _ability_increases(source.get("ability_bonuses")),
            "skill_proficiencies": _lower_names(source.get("starting_proficiencies")),
            "weapon_proficiencies": _names(source.get("starting_proficiencies")) or None,
            "features": _race_features(source),
            "senses": _race_senses(source.get("traits")),
            "spell_grants": _spell_grants(source.get("spellcasting")),
            "source": _source(source),
        }
        return {key: value for key, value in result.items() if value is not None}

    @staticmethod
    def _item(source):
        category = source.get("equipment_category")
        result = {
            "name": source["name"],
            "description": _description(source.get("desc")),
            "category": _item_category(category)
            or ("armor" if source.get("armor_category") else None),
            "weight": source.get("weight"),
            "cost": _cost(source.get("cost")),
            "weapon": _weapon(source),
            "armor": _armor(source),
            "magic_item": _magic_item(source),
            "features": _features([
                {"name": "Special", "desc": "\n\n".join(source.get("special", []))}
            ]) if source.get("special") else None,
            "source": _source(source),
        }
        if source.get("image"):
            result["image"] = {"uri": source["image"], "alt": source["name"]}
        return {key: value for key, value in result.items() if value is not None}

    @staticmethod
    def _subclass(source):
        parent = source.get("class", {})
        result = {
            "name": source["name"],
            "class_name": parent.get("name") if isinstance(parent, dict) else parent,
            "description": _description(source.get("desc")),
            "features": _features(
                feature
                for level in source.get("subclass_levels", [])
                for feature in level.get("features", [])
            ),
            "spells": _spell_grants(source.get("spells")),
            "tags": [source["subclass_flavor"]] if source.get("subclass_flavor") else None,
            "source": _source(source),
        }
        return {key: value for key, value in result.items() if value is not None}

    def _unsupported(self, source):
        raise ValueError("This 5eSRD entity type is not mapped to a project model yet")


def _description(value):
    if isinstance(value, list):
        return "\n\n".join(str(item) for item in value) or None
    return value


def _item_category(value):
    value = _name(value)
    return str(value).strip().casefold().replace(" ", "_") if value else None


def _name(value):
    if isinstance(value, dict):
        return (
            value.get("name")
            or value.get("string")
            or _name(value.get("item"))
            or _name(value.get("of"))
        )
    return value


def _names(values):
    if not values:
        return []
    return [_name(value) for value in values if _name(value)]


def _proficiency_name(value):
    name = str(value).strip().casefold()
    for prefix in ("skill:", "saving throw:", "tool:"):
        if name.startswith(prefix):
            name = name.removeprefix(prefix).strip()
            break
    return name.replace(" ", "_") if "tool:" in str(value).casefold() else name


def _proficiency_names(values):
    names = [_proficiency_name(value) for value in _names(values)]
    return list(dict.fromkeys(names)) or None


def _unique_names(values):
    result = []
    seen = set()
    for value in values:
        normalized = str(value).strip().casefold()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(str(value).strip())
    return result


def _lower_names(values):
    names = _names(values)
    return [str(value).lower() for value in names] or None


def _ability_name(value):
    value = _name(value)
    if not value:
        return None
    return {
        "str": "strength",
        "dex": "dexterity",
        "con": "constitution",
        "int": "intelligence",
        "wis": "wisdom",
        "cha": "charisma",
    }.get(str(value).strip().lower(), str(value).strip().lower())


def _ability_names(values):
    names = [_ability_name(value) for value in values or []]
    return [name for name in names if name] or None


def _choice(choices):
    for choice in choices or []:
        options = choice.get("from", {}).get("options", [])
        names = [
            _proficiency_name(_name(option))
            for option in options
            if _name(option)
        ]
        if names and choice.get("choose"):
            return {"choose": choice["choose"], "from": names}
    return None


def _class_progression(source):
    level = (source.get("spellcasting") or {}).get("level")
    if level == 1:
        return "full"
    if level == 2:
        return "half"
    if level == 3:
        return "third"
    return "full"


def _ability_increases(values):
    result = []
    for value in values or []:
        if isinstance(value, dict):
            ability = _name(value.get("ability_score")) or value.get("ability")
            amount = value.get("bonus", value.get("amount"))
        else:
            continue
        if ability and amount:
            result.append({"ability": _ability_name(ability), "amount": amount})
    return result or None


def _prerequisite(values):
    if not values:
        return None
    parts = []
    for value in values:
        if isinstance(value, dict):
            ability = _name(value.get("ability_score"))
            if ability and value.get("minimum") is not None:
                parts.append(f"{ability} {value['minimum']}")
            elif value.get("proficiency"):
                parts.append(str(_name(value["proficiency"])))
            elif value.get("spell"):
                parts.append(str(value["spell"]))
    return ", ".join(parts) or None


def _features(values):
    result = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        name = value.get("name")
        description = _description(value.get("desc") or value.get("description"))
        if name and description:
            feature = {"name": name, "description": description}
            if value.get("level") is not None:
                feature["level"] = value["level"]
            result.append(feature)
    return result or None


def _race_movement(speed):
    if isinstance(speed, (int, float)) and not isinstance(speed, bool):
        return [{
            "movement_type": "walk",
            "speed": {"distance": int(speed), "unit": "feet"},
        }]
    if isinstance(speed, str):
        match = re.fullmatch(r"\s*(\d+)\s*", speed)
        if match:
            return [{
                "movement_type": "walk",
                "speed": {"distance": int(match.group(1)), "unit": "feet"},
            }]
    result = []
    for movement_type, value in speed.items() if isinstance(speed, dict) else ():
        if movement_type == "hover":
            continue
        if isinstance(value, int):
            distance = value
        else:
            match = re.match(r"\s*(\d+)", str(value))
            if not match:
                continue
            distance = int(match.group(1))
        result.append({
            "movement_type": movement_type,
            "speed": {"distance": distance, "unit": "feet"},
            "hover": bool(speed.get("hover", False)),
        })
    return result or None


def _race_senses(traits):
    result = []
    for trait in traits or []:
        name = str(trait.get("name", "")).casefold()
        if name not in {"darkvision", "superior darkvision"}:
            continue
        description = " ".join(
            str(value) for value in trait.get("desc", []) if value
        )
        match = re.search(r"within (\d+) feet", description, re.IGNORECASE)
        if match:
            result.append({
                "type": "darkvision",
                "distance": int(match.group(1)),
                "distance_type": "feet",
            })
    return result or None


def _race_features(source):
    values = list(source.get("traits") or [])
    for label, text in (("Age", source.get("age")), ("Alignment", source.get("alignment"))):
        if text:
            values.append({"name": label, "desc": [text]})
    return _features(values)


def _class_features(source):
    result = []
    for level_data in source.get("class_levels", []):
        if not isinstance(level_data, dict):
            continue
        level = level_data.get("level")
        for feature in level_data.get("features", []):
            if not isinstance(feature, dict):
                continue
            name = str(feature.get("name", "")).strip()
            if name.casefold().endswith(" feature"):
                continue
            enriched = dict(feature)
            if name.casefold().startswith("spellcasting:"):
                enriched["name"] = "Spellcasting"
            if level is not None:
                enriched.setdefault("level", level)
            result.extend(_features([enriched]) or [])
    return result or None


def _spell_grants(values):
    if not isinstance(values, (list, tuple)):
        return None
    names = [name for name in (_name(value) for value in values or []) if name]
    return [{"spells": names}] if names else None


def _spell_material(source, component_text):
    if "M" not in str(component_text).upper():
        return None
    description = source.get("material")
    if description is None:
        return XMLSpellAdaptor().material(component_text)
    description = str(description).strip()
    result = {"description": description}
    if "consumed" in description.lower() or "must be consumed" in description.lower():
        result["consumed"] = True
    import re
    cost = re.search(r"(?:worth|costs?)\s+(?:at least\s+)?(\d+(?:\.\d+)?)\s*gp", description, re.IGNORECASE)
    if cost:
        result["cost"] = float(cost.group(1))
    return result


def _cost(value):
    if not isinstance(value, dict) or value.get("quantity") is None:
        return None
    return {"amount": max(1, int(value["quantity"])), "currency": value.get("unit", "gp")}


def _weapon(source):
    if not source.get("weapon_category"):
        return None
    damage = source.get("damage") or {}
    damage_type = _name(damage.get("damage_type"))
    effects = None
    if damage.get("damage_dice") and damage_type:
        import re
        match = re.fullmatch(r"(\d+)d(\d+)", damage["damage_dice"])
        if match:
            effects = [{"damage": {"type": damage_type.lower(), "roll": {"count": int(match[1]), "dice": int(match[2])}}}]
    range_value = source.get("range") or {}
    throw_range = source.get("throw_range")
    if isinstance(throw_range, dict):
        range_value = throw_range
    result = {"type": source.get("weapon_category"), "properties": _names(source.get("properties")) or None,
              "range": {key: range_value[key] for key in ("normal", "long") if range_value.get(key) is not None} or None,
              "effects": effects}
    result["type"] = _slug(source.get("name"))
    result["properties"] = [
        str(value).strip().casefold() for value in result["properties"] or []
    ] or None
    return {key: value for key, value in result.items() if value is not None}


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_") if value else None


def _armor(source):
    armor_class = source.get("armor_class")
    if not isinstance(armor_class, dict):
        return None
    armor_category = str(source.get("armor_category", "armor")).strip().casefold()
    result = {
        "category": "shield" if armor_category == "shield" else armor_category,
        "type": _slug(source.get("name")),
        "armor_class": armor_class.get("base"),
        "stealth_disadvantage": bool(source.get("stealth_disadvantage", False)),
    }
    strength_requirement = source.get("str_minimum")
    if strength_requirement:
        result["strength_requirement"] = strength_requirement
    if source.get("dex_bonus") is not None:
        result["add_dexterity"] = {
            "enabled": bool(source["dex_bonus"]),
            "maximum": source.get("max_bonus"),
        }
    return {key: value for key, value in result.items() if value is not None}


def _magic_item(source):
    if not source.get("rarity") and not source.get("requires_attunement"):
        return None
    return {"rarity": source.get("rarity"), "attunement": bool(source.get("requires_attunement"))}


def _source(source):
    if source.get("url"):
        return {"href": source["url"]}
    return None
