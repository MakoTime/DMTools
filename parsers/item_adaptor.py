from __future__ import annotations

import re
from typing import Any


class ItemAdaptor:
    """Adapt parsed item source data into the Item schema."""

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = [value for value in source.get("text", []) if value]
        description = self.description(text)
        features = self.features(text)
        result = {
            "name": source.get("name"),
            "category": self.category(source),
            "weight": self.weight(source.get("weight")),
            "description": description,
            "features": features,
            "weapon": self.weapon(text),
            "magic_item": self.magic_item(source, text),
            "source": self.source(text),
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def category(self, source: dict[str, Any]) -> str | None:
        item_type = source.get("type")

        if item_type == "WD":
            return "wand"

        return None

    def weight(self, value: Any) -> float | None:
        if value is None:
            return None

        return float(value)

    def description(self, text: list[str]) -> str | None:
        paragraphs = text[:2]
        return "\n\n".join(paragraphs) or None

    def features(self, text: list[str]) -> list[dict[str, str]] | None:
        names = {
            "Attunement",
            "Random Properties",
            "Protection",
            "Spells",
            "Call Undead",
            "Sentience",
            "Personality",
            "Destroying the Wand",
        }
        features = []
        current_name = None
        current_text: list[str] = []

        for value in text[2:]:
            heading, separator, remainder = value.partition(":")

            if separator and heading in names:
                if current_name is not None:
                    features.append(self.feature(current_name, current_text))
                current_name = heading
                current_text = [remainder.strip()] if remainder.strip() else []
            elif current_name is not None:
                current_text.append(value.lstrip("• "))

        if current_name is not None:
            features.append(self.feature(current_name, current_text))

        return features or None

    def feature(self, name: str, text: list[str]) -> dict[str, str]:
        return {
            "name": name,
            "description": " ".join(part for part in text if part),
        }

    def weapon(self, text: list[str]) -> dict[str, Any] | None:
        weapon_text = next(
            (value for value in text if "magic mace" in value.lower()),
            None,
        )

        if weapon_text is None:
            return None

        damage_match = re.search(
            r"extra (?P<count>\d+)d(?P<dice>\d+) (?P<type>[a-z]+) damage",
            weapon_text,
            re.IGNORECASE,
        )
        if damage_match is None:
            return {"type": "mace"}

        return {
            "type": "mace",
            "effects": [{
                "attack_hit": {
                    "type": "melee_weapon",
                    "effects": [{
                        "damage": {
                            "type": damage_match.group("type").lower(),
                            "roll": {
                                "dice": int(damage_match.group("dice")),
                                "count": int(damage_match.group("count")),
                            },
                        },
                    }],
                },
            }],
        }

    def magic_item(
        self,
        source: dict[str, Any],
        text: list[str],
    ) -> dict[str, Any] | None:
        detail = (source.get("detail") or "").lower()
        modifiers = source.get("modifiers") or []
        bonuses = [
            {
                "type": self.bonus_type(modifier.get("text", "")),
                "value": self.bonus_value(modifier.get("text", "")),
            }
            for modifier in modifiers
            if modifier.get("category") == "bonus"
        ]
        spells = self.spells(next((value for value in text if value.startswith("Spells:")), ""))
        charges = self.charges(next((value for value in text if value.startswith("Spells:")), ""))
        result = {
            "rarity": detail.split(" ", 1)[0] if detail else None,
            "attunement": "requires attunement" in detail,
            "bonuses": bonuses or None,
            "charges": charges,
            "spells": spells,
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def bonus_type(self, text: str) -> str:
        if "attack" in text:
            return "attack"
        if "damage" in text:
            return "damage"
        return "armor_class"

    def bonus_value(self, text: str) -> int:
        return int(re.search(r"\+(\d+)", text).group(1))

    def charges(self, text: str) -> dict[str, Any] | None:
        maximum = re.search(r"has (\d+) charges", text)
        recharge = re.search(r"regains (\d+)d(\d+) expended charges daily", text)

        if maximum is None:
            return None

        result: dict[str, Any] = {"maximum": int(maximum.group(1))}
        if recharge:
            result.update({
                "recharge": {
                    "dice": int(recharge.group(2)),
                    "count": int(recharge.group(1)),
                    "modifier": 3,
                },
                "recharge_duration": {"amount": 1, "duration": "day"},
            })
        return result

    def spells(self, text: str) -> list[dict[str, Any]] | None:
        values = re.findall(r"([a-z ]+) \((\d+) charge", text)
        return [
            {"spell": spell.strip(), "charges": int(charges)}
            for spell, charges in values
        ] or None

    def source(self, text: list[str]) -> dict[str, str] | None:
        value = next(
            (item for item in text if item.startswith("Source:")),
            None,
        )
        return {"text": value.removeprefix("Source: ").strip()} if value else None