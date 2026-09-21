from __future__ import annotations

import re
from typing import Any


class ItemAdaptor:
    """Adapt parsed item source data into the Item schema."""

    FEATURE_HEADINGS = {
        "Attunement",
        "Random Properties",
        "Protection",
        "Power Strike",
        "Spells",
        "Call Undead",
        "Retributive Strike",
        "Sentience",
        "Personality",
        "Spirit of Kas",
        "Destroying the Sword",
        "Destroying the Wand",
        "Proficiency",
    }

    NON_FEATURE_HEADINGS = {
        "Finesse",
        "Heavy",
        "Light",
        "Reach",
        "Special",
        "Thrown",
        "Two-Handed",
        "Versatile",
    }

    CATEGORY_BY_TYPE = {
        "$": "adventuring_gear",
        "A": "adventuring_gear",
        "G": "adventuring_gear",
        "HA": "armor",
        "LA": "armor",
        "MA": "armor",
        "M": "weapon",
        "P": "potion",
        "R": "weapon",
        "RD": "rod",
        "RG": "ring",
        "S": "armor",
        "SC": "scroll",
        "ST": "staff",
        "W": "wonderous_item",
        "WD": "wand",
    }

    PROPERTY_BY_CODE = {
        "A": "ammunition",
        "F": "finesse",
        "H": "heavy",
        "L": "light",
        "LD": "loading",
        "R": "reach",
        "SP": "special",
        "T": "thrown",
        "2H": "two_handed",
        "V": "versatile",
    }

    DAMAGE_TYPE_BY_CODE = {
        "B": "bludgeoning",
        "P": "piercing",
        "S": "slashing",
    }

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = [value for value in source.get("text", []) if value]
        description = self.description(text)
        features = self.features(text)
        result = {
            "name": source.get("name"),
            "category": self.category(source),
            "weight": self.weight(source.get("weight")),
            "cost": self.cost(source.get("value")),
            "description": description,
            "features": features,
            "weapon": self.weapon(source, text),
            "armor": self.armor(source),
            "magic_item": self.magic_item(source, text),
            "source": self.source(text),
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def category(self, source: dict[str, Any]) -> str | None:
        return self.CATEGORY_BY_TYPE.get(source.get("type"))

    def weight(self, value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def cost(self, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None

        try:
            amount = float(value)
        except (TypeError, ValueError):
            return None

        if amount < 1 or not amount.is_integer():
            return None

        return {"amount": int(amount), "currency": "gp"}

    def description(self, text: list[str]) -> str | None:
        paragraphs = []
        for value in text:
            if value.startswith("Source:"):
                break
            heading, separator, _ = value.partition(":")
            if separator and heading in self.FEATURE_HEADINGS:
                break
            paragraphs.append(value)
        return "\n\n".join(paragraphs) or None

    def features(self, text: list[str]) -> list[dict[str, str]] | None:
        features = []
        current_name = None
        current_text: list[str] = []

        for value in text[2:]:
            heading, separator, remainder = value.partition(":")

            if separator and heading in self.FEATURE_HEADINGS:
                if current_name is not None:
                    features.append(self.feature(current_name, current_text))
                if heading == "Proficiency":
                    features.append(self.feature(heading, [remainder.strip()]))
                    break
                current_name = heading
                current_text = [remainder.strip()] if remainder.strip() else []
            elif separator and heading in self.NON_FEATURE_HEADINGS:
                if current_name is not None:
                    features.append(self.feature(current_name, current_text))
                    current_name = None
                    current_text = []
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

    def weapon(
        self,
        source: dict[str, Any],
        text: list[str],
    ) -> dict[str, Any] | None:
        if source.get("type") not in {"M", "R", "WD"}:
            return None

        properties = [
            self.PROPERTY_BY_CODE[code]
            for code in self.source_codes(source.get("property"))
            if code in self.PROPERTY_BY_CODE
        ]
        weapon: dict[str, Any] = {
            "type": self.weapon_type(source.get("name"), text),
            "properties": properties or None,
            "range": self.weapon_range(source.get("range")),
        }

        weapon_text = next(
            (value for value in text if "magic mace" in value.lower()),
            None,
        )

        if source.get("dmg1"):
            damage = self.damage(source)
            if damage is not None:
                weapon["effects"] = [{"damage": damage}]

        versatile_damage = self.damage(source, "dmg2")
        if versatile_damage is not None:
            weapon.setdefault("effects", []).append({"damage": versatile_damage})

        if weapon_text is not None:
            damage_match = re.search(
                r"extra (?P<count>\d+)d(?P<dice>\d+) (?P<type>[a-z]+) damage",
                weapon_text,
                re.IGNORECASE,
            )
            if damage_match is not None:
                weapon["effects"] = [{
                    "damage": {
                        "type": damage_match.group("type").lower(),
                        "roll": {
                            "dice": int(damage_match.group("dice")),
                            "count": int(damage_match.group("count")),
                        },
                    },
                }]

        return {
            key: value
            for key, value in weapon.items()
            if value is not None
        }

    def weapon_type(self, name: Any, text: list[str] | None = None) -> str | None:
        for value in text or ():
            match = re.fullmatch(r"\s*Proficiency:\s*(?:simple|martial),\s*(.+?)\s*", value, re.IGNORECASE)
            if match:
                return re.sub(r"[^a-z0-9]+", "_", match.group(1).lower()).strip("_")
        if not name:
            return None

        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")

    def source_codes(self, value: Any) -> list[str]:
        if not value:
            return []

        values = value if isinstance(value, list) else [value]
        return [
            code.strip().upper()
            for item in values
            for code in str(item).split(",")
            if code.strip()
        ]

    def weapon_range(self, value: Any) -> dict[str, int] | None:
        if not value:
            return None

        values = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", str(value))
        if values is None:
            return None

        return {"normal": int(values.group(1)), "long": int(values.group(2))}

    def damage(
        self,
        source: dict[str, Any],
        field: str = "dmg1",
    ) -> dict[str, Any] | None:
        match = re.fullmatch(r"\s*(\d+)d(\d+)\s*", str(source.get(field)))
        damage_type = self.DAMAGE_TYPE_BY_CODE.get(
            str(source.get("dmgType", "")).strip().upper()
        )
        if match is None or damage_type is None:
            return None

        return {
            "type": damage_type,
            "roll": {
                "count": int(match.group(1)),
                "dice": int(match.group(2)),
            },
        }

    def armor(self, source: dict[str, Any]) -> dict[str, Any] | None:
        category_by_type = {
            "HA": "heavy",
            "LA": "light",
            "MA": "medium",
            "S": "shield",
        }
        category = category_by_type.get(source.get("type"))
        if category is None or not source.get("ac"):
            return None

        try:
            armor_class = int(source["ac"])
        except (TypeError, ValueError):
            return None

        armor: dict[str, Any] = {
            "category": category,
            "type": self.armor_type(source.get("name")),
            "armor_class": armor_class,
            "stealth_disadvantage": str(source.get("stealth", "")).strip() == "1",
        }
        strength = source.get("strength")
        if strength:
            try:
                armor["strength_requirement"] = int(strength)
            except (TypeError, ValueError):
                pass

        return armor

    def armor_type(self, name: Any) -> str | None:
        if not name:
            return None

        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")

    def magic_item(
        self,
        source: dict[str, Any],
        text: list[str],
    ) -> dict[str, Any] | None:
        detail = (source.get("detail") or "").lower()
        full_text = " ".join(text)
        modifiers = source.get("modifiers") or []
        if not source.get("magic") and not detail and not modifiers:
            return None
        bonuses = [
            {
                "type": self.bonus_type(modifier.get("text", "")),
                "value": self.bonus_value(modifier.get("text", "")),
            }
            for modifier in modifiers
            if modifier.get("category") == "bonus"
            and re.search(r"\+\d+", modifier.get("text", ""))
        ]
        spells = self.spells(next((value for value in text if value.startswith("Spells:")), ""))
        charges = self.charges(full_text)
        result = {
            "rarity": self.rarity(detail),
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

    def rarity(self, detail: str) -> str | None:
        if not detail:
            return None

        return re.split(r"[,(]", detail, maxsplit=1)[0].strip() or None

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
        recharge = re.search(
            r"regains (\d+)(?:d(\d+))?(?:\+(\d+))? expended charges daily",
            text,
        )

        if maximum is None:
            return None

        result: dict[str, Any] = {"maximum": int(maximum.group(1))}
        if recharge:
            recharge_roll = {
                "count": int(recharge.group(1)),
                "dice": int(recharge.group(2) or 0),
            }
            if recharge.group(3) is not None:
                recharge_roll["modifier"] = int(recharge.group(3))
            result.update({
                "recharge": recharge_roll,
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