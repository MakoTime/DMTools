from __future__ import annotations

import re
from typing import Any


class BackgroundAdaptor:
    SKILLS = {
        "acrobatics", "animal_handling", "arcana", "athletics", "deception",
        "history", "insight", "intimidation", "investigation", "medicine",
        "nature", "perception", "performance", "persuasion", "religion",
        "sleight_of_hand", "stealth", "survival",
    }
    TOOLS = {
        "alchemist_supplies", "brewer_supplies", "calligrapher_supplies",
        "carpenter_tools", "cartographer_tools", "cobbler_tools", "cook_utensils",
        "glassblower_tools", "jeweler_tools", "leatherworker_tools", "mason_tools",
        "painter_supplies", "potter_tools", "smith_tools", "tinker_tools",
        "weaver_tools", "woodcarver_tools", "disguise_kit", "forgery_kit",
        "herbalism_kit", "navigator_tools", "poisoner_kit", "thieves_tools",
    }

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        traits = source.get("traits", [])
        text = [value for trait in traits for value in trait.get("text", []) if value]
        result = {
            "name": source.get("name"),
            "description": self.description(traits),
            "skill_proficiencies": self.skills(source.get("proficiency")),
            "tool_proficiencies": self.tools(text),
            "features": self.features(traits),
            "source": self.source(text),
        }
        return {key: value for key, value in result.items() if value is not None}

    def description(self, traits: list[dict[str, Any]]) -> str | None:
        trait = next((trait for trait in traits if trait.get("name") == "Description"), None)
        if trait is None:
            return None
        values = [value for value in trait.get("text", []) if value]
        return "\n\n".join(values) or None

    def skills(self, value: Any) -> list[str] | None:
        if not value:
            return None
        result = [self.normalize(part) for part in str(value).split(",")]
        return result if result and all(skill in self.SKILLS for skill in result) else None

    def tools(self, text: list[str]) -> list[str] | None:
        values: list[str] = []
        for value in text:
            match = re.search(r"Tool Proficiencies:\s*([^.;]+)", value, re.IGNORECASE)
            if match is None:
                continue
            for part in re.split(r",\s*|\s+and\s+", match.group(1)):
                tool = self.normalize(part)
                if tool in self.TOOLS:
                    values.append(tool)
        return list(dict.fromkeys(values)) or None

    def features(self, traits: list[dict[str, Any]]) -> list[dict[str, str]] | None:
        features = []
        for trait in traits:
            name = trait.get("name")
            if not name or not name.startswith("Feature:"):
                continue
            values = [value for value in trait.get("text", []) if value]
            if values:
                features.append({
                    "name": name.removeprefix("Feature:").strip(),
                    "description": "\n\n".join(values),
                })
        return features or None

    def source(self, text: list[str]) -> dict[str, str] | None:
        for value in text:
            if value.startswith("Source:"):
                return {"text": value.removeprefix("Source:").strip()}
        return None

    def normalize(self, value: str) -> str:
        return re.sub(r"\s+", "_", value.strip().lower())