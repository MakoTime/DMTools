from __future__ import annotations

import re
from typing import Any

from models.components import Effect


class ClassAdaptor:
    SUBCLASS_MARKERS = {
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
    ABILITIES = {
        "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
    }
    SKILLS = {
        "acrobatics", "animal_handling", "arcana", "athletics", "deception", "history",
        "insight", "intimidation", "investigation", "medicine", "nature", "perception",
        "performance", "persuasion", "religion", "sleight_of_hand", "stealth", "survival",
    }
    ARMOR = {"light", "medium", "heavy", "shields"}
    TOOLS = {"thieves_tools", "herbalism_kit", "musical_instrument"}
    PROGRESSION = {
        "bard": "full", "cleric": "full", "druid": "full", "sorcerer": "full",
        "wizard": "full", "paladin": "half", "ranger": "half", "artificer": "half",
        "warlock": "pact", "eldritch knight": "third", "arcane trickster": "third",
    }

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        name = self.normalize(source.get("name"))
        proficiency = self.parts(source.get("proficiency"))
        result = {
            "name": name,
            "hit_dice": self.hit_die(source.get("hd")),
            "description": self.base_description(source),
            "primary_abilities": self.abilities(proficiency[:2]),
            "saving_throws": self.abilities(proficiency[:2]),
            "armor_proficiencies": self.armor(source.get("armor")),
            "weapon_proficiencies": self.weapons(source.get("weapons")),
            "tool_proficiencies": self.tools(source.get("tools")),
            "skill_choices": self.skill_choices(source),
            "spellcasting": self.spellcasting(name, source.get("spellAbility")),
        }
        return {key: value for key, value in result.items() if value is not None}

    def normalize(self, value: Any) -> str | None:
        if not value:
            return None
        return str(value).strip().lower()

    def parts(self, value: Any) -> list[str]:
        if not value:
            return []
        return [part.strip() for part in re.split(r",|\band\b", str(value), flags=re.IGNORECASE) if part.strip()]

    def hit_die(self, value: Any) -> int | None:
        try:
            die = int(str(value))
        except (TypeError, ValueError):
            return None
        return die if die in {4, 6, 8, 10, 12} else None

    def abilities(self, values: list[str]) -> list[str] | None:
        result = [value.lower() for value in values if value.lower() in self.ABILITIES]
        return result or None

    def armor(self, value: Any) -> list[str] | None:
        if not value or str(value).strip().lower() == "none":
            return None
        result = [part.strip().lower() for part in str(value).split(",")]
        return result or None

    def weapons(self, value: Any) -> list[str] | None:
        if not value or str(value).strip().lower() == "none":
            return None
        return [part.strip().lower() for part in re.split(r",|\band\b", str(value), flags=re.IGNORECASE) if part.strip()]

    def tools(self, value: Any) -> list[str] | None:
        if not value or str(value).strip().lower() == "none":
            return None
        return [part.strip().lower().replace(" ", "_") for part in re.split(r",|\band\b", str(value), flags=re.IGNORECASE) if part.strip()]

    def skill_choices(self, source: dict[str, Any]) -> dict[str, Any] | None:
        count = source.get("numSkills")
        proficiency = self.parts(source.get("proficiency"))
        skills = [self.normalize(value).replace(" ", "_") for value in proficiency if self.normalize(value).replace(" ", "_") in self.SKILLS]
        try:
            choose = int(str(count))
        except (TypeError, ValueError):
            return None
        return {"choose": choose, "from": skills} if choose > 0 and skills else None

    def spellcasting(self, name: str | None, value: Any) -> dict[str, str] | None:
        ability = self.normalize(value)
        progression = self.PROGRESSION.get(name or "")
        if ability not in self.ABILITIES or progression is None:
            return None
        return {"ability": ability, "progression": progression}

    def base_description(self, source: dict[str, Any]) -> str | None:
        class_name = self.normalize(source.get("name"))
        marker = self.SUBCLASS_MARKERS.get(class_name or "")
        known = self.subclass_names(source, marker)
        descriptions = []
        for level in source.get("autolevels", []):
            for child in level.get("children", []):
                if child.get("tag") != "feature" or child.get("attributes", {}).get("optional") != "YES":
                    continue
                feature = self.feature(child, self.level(level.get("attributes", {}).get("level")))
                if not self.feature_owners(feature["name"], marker, known):
                    descriptions.append(f"{feature['name']}: {feature['description']}")
        return "\n\n".join(descriptions) or None

    def subclass_names(self, source: dict[str, Any], marker: str | None) -> dict[str, dict[str, Any]]:
        if marker is None:
            return {}
        known: dict[str, dict[str, Any]] = {}
        for level in source.get("autolevels", []):
            for child in level.get("children", []):
                if child.get("tag") != "feature" or child.get("attributes", {}).get("optional") != "YES":
                    continue
                name = self.text(child, "name") or ""
                prefix = f"{marker}: "
                if name.startswith(prefix):
                    owner = name[len(prefix):].strip()
                    if not owner.lower().startswith("replaces "):
                        known.setdefault(owner, {})
        return known

    def subclasses(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        class_name = self.normalize(source.get("name"))
        marker = self.SUBCLASS_MARKERS.get(class_name or "")
        if marker is None:
            return []

        grouped = {
            owner: {"name": owner, "class": class_name, "features": []}
            for owner in self.subclass_names(source, marker)
        }

        for level in source.get("autolevels", []):
            level_number = self.level(level.get("attributes", {}).get("level"))
            for child in level.get("children", []):
                if child.get("tag") != "feature" or child.get("attributes", {}).get("optional") != "YES":
                    continue
                feature = self.feature(child, level_number)
                owners = self.feature_owners(feature["name"], marker, grouped)
                for owner in owners:
                    grouped.setdefault(owner, {"name": owner, "class": class_name, "features": []})
                    grouped[owner]["features"].append(feature)

        return list(grouped.values())

    def level(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def feature(self, element: dict[str, Any], level: int | None) -> dict[str, Any]:
        name = self.text(element, "name") or "Unnamed feature"
        texts = [child.get("text") for child in element.get("children", []) if child.get("tag") == "text" and child.get("text")]
        description = "\n\n".join(text for text in texts if not text.startswith("Source:"))
        source_text = next((text[len("Source:"):].strip() for text in texts if text.startswith("Source:")), None)
        result: dict[str, Any] = {"name": name, "description": description or name}
        effect = Effect.from_description(result["description"])
        if effect is not None and effect.description is None:
            result["effects"] = [effect.model_dump(mode="json", exclude_none=True)]
        if level is not None:
            result["level"] = level
        if source_text:
            result["source"] = {"text": source_text}
        return result

    def text(self, element: dict[str, Any], tag: str) -> str | None:
        for child in element.get("children", []):
            if child.get("tag") == tag:
                return child.get("text")
        return None

    def feature_owners(self, name: str, marker: str, known: dict[str, dict[str, Any]]) -> list[str]:
        owners: list[str] = []
        prefix = f"{marker}: "
        if name.startswith(prefix):
            owners.append(name[len(prefix):].strip())
        match = re.search(r"\(([^()]+)\)\s*$", name)
        if match:
            owner = match.group(1).strip()
            if owner not in owners and owner != marker:
                owners.append(owner)
        for owner in known:
            if name.startswith(f"{owner}: ") and owner not in owners:
                owners.append(owner)
        return owners