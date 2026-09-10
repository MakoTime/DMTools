from __future__ import annotations

import re
from typing import Any


class RaceAdaptor:
    SIZE_BY_CODE = {
        "T": "tiny",
        "S": "small",
        "M": "medium",
        "L": "large",
        "H": "huge",
        "G": "gargantuan",
    }

    ABILITY_BY_CODE = {
        "STR": "strength",
        "DEX": "dexterity",
        "CON": "constitution",
        "INT": "intelligence",
        "WIS": "wisdom",
        "CHA": "charisma",
    }

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        name, subtype = self.name_and_subtype(source.get("name"))
        result = {
            "name": name,
            "subtype": subtype,
            "size": self.SIZE_BY_CODE.get(source.get("size")),
            "movement": self.movement(source.get("speed")),
            "ability_score_increases": self.ability_increases(source.get("ability")),
            "features": self.features(source.get("traits", [])),
            "skill_proficiencies": self.skill_proficiencies(source.get("proficiency")),
            "languages": self.languages(source.get("traits", [])),
            "senses": self.senses(source.get("traits", [])),
            "spell_grants": self.spell_grants(source),
            "source": self.source(source.get("traits", [])),
        }
        return {key: value for key, value in result.items() if value is not None}

    def name_and_subtype(self, value: Any) -> tuple[str | None, str | None]:
        if not value:
            return None, None
        match = re.fullmatch(r"\s*([^()]+?)\s*\(([^()]+)\)\s*", str(value))
        if match is not None:
            return match.group(1).strip(), match.group(2).strip()
        if "," in str(value):
            name, subtype = (part.strip() for part in str(value).split(",", 1))
            return name, subtype or None
        return str(value), None

    def movement(self, value: Any) -> list[dict[str, Any]] | None:
        if not value:
            return None
        match = re.fullmatch(r"\s*(\d+)\s*", str(value))
        if match is None:
            return None
        return [{
            "movement_type": "walk",
            "speed": {"distance": int(match.group(1)), "unit": "feet"},
        }]

    def ability_increases(self, value: Any) -> list[dict[str, Any]] | None:
        if not value:
            return None
        increases = []
        for part in str(value).split(","):
            match = re.fullmatch(r"\s*([A-Za-z]+)\s*([+-]?\d+)\s*", part)
            if match is None:
                return None
            ability = self.ABILITY_BY_CODE.get(match.group(1).upper())
            amount = int(match.group(2))
            if ability is None or amount < 1:
                return None
            increases.append({"ability": ability, "amount": amount})
        return increases or None

    def features(self, traits: list[dict[str, Any]]) -> list[dict[str, str]] | None:
        features = []
        for trait in traits:
            name = trait.get("name")
            text = [value for value in trait.get("text", []) if value]
            special = [value for value in trait.get("special", []) if value]
            modifiers = [modifier.get("text") for modifier in trait.get("modifiers", [])]
            description = "\n\n".join(text + special + [value for value in modifiers if value])
            if name and description:
                features.append({"name": name, "description": description})
        return features or None

    def skill_proficiencies(self, value: Any) -> list[str] | None:
        if not value:
            return None
        skills = {
            "acrobatics", "animal_handling", "arcana", "athletics",
            "deception", "history", "insight", "intimidation",
            "investigation", "medicine", "nature", "perception",
            "performance", "persuasion", "religion", "sleight_of_hand",
            "stealth", "survival",
        }
        result = [
            re.sub(r"\s+", "_", part.strip().lower())
            for part in str(value).split(",")
        ]
        return result if result and all(skill in skills for skill in result) else None

    def languages(self, traits: list[dict[str, Any]]) -> list[str] | None:
        for trait in traits:
            if trait.get("name") != "Languages":
                continue
            text = " ".join(value for value in trait.get("text", []) if value)
            match = re.search(r"speak, read, and write ([^.]+)", text, re.IGNORECASE)
            if match is None:
                continue
            values = re.split(r",\s*|\s+and\s+", match.group(1))
            languages = [value.strip().lower() for value in values]
            return [value for value in languages if value and "choice" not in value]
        return None

    def senses(self, traits: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        for trait in traits:
            if trait.get("name") not in {"Darkvision", "Superior Darkvision"}:
                continue
            text = " ".join(value for value in trait.get("text", []) if value)
            match = re.search(r"within (\d+) feet", text, re.IGNORECASE)
            if match is not None:
                return [{
                    "type": "darkvision",
                    "distance": int(match.group(1)),
                    "distance_type": "feet",
                }]
        return None

    def spell_grants(self, source: dict[str, Any]) -> list[dict[str, Any]] | None:
        ability_value = str(source.get("spellAbility", "")).strip().lower()
        ability = (
            ability_value
            if ability_value in self.ABILITY_BY_CODE.values()
            else self.ABILITY_BY_CODE.get(ability_value.upper())
        )
        for trait in source.get("traits", []):
            if trait.get("name") != "Cantrip":
                continue
            text = " ".join(value for value in trait.get("text", []) if value)
            if "cantrip" in text.lower() and "wizard spell list" in text.lower():
                grant = {
                    "choices": [{
                        "filter": {"classes": ["wizard"]},
                        "choice_count": 1,
                    }],
                }
                if ability:
                    grant["choices"][0]["casting_ability"] = ability
                return [grant]
        return None

    def source(self, traits: list[dict[str, Any]]) -> dict[str, str] | None:
        for trait in traits:
            for value in trait.get("text", []):
                if value and value.startswith("Source:"):
                    return {"text": value.removeprefix("Source:").strip()}
        return None