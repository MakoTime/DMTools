from __future__ import annotations

import re
from typing import Any


class FeatAdaptor:
    ABILITY_NAMES = {
        "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
    }
    ABILITY_CODES = {
        "STR": "strength", "DEX": "dexterity", "CON": "constitution",
        "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma",
    }

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = [value for value in source.get("text", []) if value]
        result = {
            "name": self.name(source.get("name")),
            "description": self.description(text),
            "prerequisite": source.get("prerequisite"),
            "ability_score_increases": self.ability_increases(source.get("modifiers", [])),
            "spell_grants": self.spell_grants(source, text),
            "source": self.source(text),
        }
        return {key: value for key, value in result.items() if value is not None}

    def name(self, value: Any) -> str | None:
        if not value:
            return None
        return str(value).strip()

    def description(self, text: list[str]) -> str | None:
        values = [value for value in text if not value.startswith("Source:")]
        return "\n\n".join(values) or None

    def ability_increases(self, modifiers: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        increases = []
        for modifier in modifiers:
            if modifier.get("category") != "ability score":
                continue
            match = re.fullmatch(r"\s*([A-Za-z ]+)\s*([+-]\d+)\s*", str(modifier.get("text")))
            if match is None:
                continue
            ability = self.ABILITY_CODES.get(match.group(1).strip().upper(), match.group(1).strip().lower())
            amount = int(match.group(2))
            if ability in self.ABILITY_NAMES and amount > 0:
                increases.append({"ability": ability, "amount": amount})
        return increases or None

    def spell_grants(self, source: dict[str, Any], text: list[str]) -> list[dict[str, Any]] | None:
        description = " ".join(text)
        if "misty step spell" not in description.lower():
            return None
        ability = next(
            (entry["ability"] for entry in self.ability_increases(source.get("modifiers", [])) or []),
            None,
        )
        choice = {
            "filter": {
                "schools": ["divination", "enchantment"],
                "levels": [1],
            },
            "choice_count": 1,
            "uses": 1,
            "recharge": "long_rest",
        }
        if ability:
            choice["casting_ability"] = ability
        grant = {
            "spells": ["misty step"],
            "uses": 1,
            "recharge": "long_rest",
        }
        if ability:
            grant["casting_ability"] = ability
        return [grant, {"choices": [choice]}]

    def source(self, text: list[str]) -> dict[str, str] | None:
        for value in text:
            if value.startswith("Source:"):
                return {"text": value.removeprefix("Source:").strip()}
        return None