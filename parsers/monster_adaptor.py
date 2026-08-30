from __future__ import annotations

import re

from typing import Any


SIZE_MAP = {
    "T": "tiny",
    "S": "small",
    "M": "medium",
    "L": "large",
    "H": "huge",
    "G": "gargantuan",
}

ABILITY_MAP = {
    "str": "strength",
    "dex": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "wis": "wisdom",
    "cha": "charisma",
}

DISTANCE_TYPE_MAP = {
    "ft.": "feet",
    "ft": "feet",
    "mile": "miles",
    "miles": "miles",
}


class MonsterAdaptor:
    """Adapt parsed monster source data into the Monster schema."""

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        result = {
            "name": self.adapt_name(source.get("name")),
            "size": self.adapt_size(source.get("size")),
            "creature_type": self.adapt_creature_type(source.get("type")),
            "alignment": self.adapt_alignment(source.get("alignment")),
            "ability_scores": self.adapt_ability_scores(
                source.get("ability_scores")
            ),
            "armor_class": self.adapt_armor_class(source.get("ac")),
            "hit_points": self.adapt_hit_points(source.get("hp")),
            "hit_dice": self.adapt_hit_dice(source.get("hp")),
            "movement": self.adapt_movement(source.get("speed")),
            "saving_throws": self.adapt_saving_throws(source.get("saves")),
            "skills": self.adapt_skills(source.get("skills")),
            "damage_resistances": self.adapt_damage_types(
                source.get("resistances")
            ),
            "damage_vulnerabilities": self.adapt_damage_types(
                source.get("vulnerabilities")
            ),
            "damage_immunities": self.adapt_damage_types(
                source.get("immunities")
            ),
            "condition_immunities": self.adapt_conditions(
                source.get("condition_immunities")
            ),
            "senses": self.adapt_senses(source.get("senses")),
            "passive_perception": self.adapt_int(source.get("passive")),
            "languages": self.adapt_languages(source.get("languages")),
            "features": self.adapt_features(source.get("traits")),
            "actions": self.adapt_actions(source.get("actions")),
            "legendary_actions": self.adapt_actions(
                source.get("legendary_actions")
            ),
            "challenge_rating": self.adapt_challenge_rating(source.get("cr")),
            "environments": self.adapt_environments(
                source.get("environment")
            ),
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def adapt_name(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value).strip()

    def adapt_size(self, value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return SIZE_MAP.get(value, value.lower())

    def adapt_creature_type(self, value: Any) -> str | None:
        if value is None:
            return None

        return str(value).strip().lower()

    def adapt_alignment(self, value: Any) -> Any:
        if value is None:
            return None

        value = str(value).strip().lower()

        if value in {"unaligned", "any"}:
            return value

        parts = value.split()

        if len(parts) == 2:
            return {
                "order": parts[0],
                "morality": parts[1],
            }

        if len(parts) == 1:
            if parts[0] in {"lawful", "neutral", "chaotic"}:
                return {
                    "order": parts[0],
                }

            if parts[0] in {"good", "evil"}:
                return {
                    "morality": parts[0],
                }

        return value

    def adapt_ability_scores(
        self,
        values: Any,
    ) -> dict[str, int] | None:
        if not values:
            return None

        result = {}

        for source_name, schema_name in ABILITY_MAP.items():
            value = values.get(source_name)

            if value is not None:
                result[schema_name] = int(value)

        return result or None

    def adapt_armor_class(
        self,
        value: Any,
    ) -> dict[str, Any] | None:
        if value is None:
            return None

        match = re.match(
            r"^(?P<value>\d+)(?:\s*\((?P<description>.+)\))?$",
            str(value).strip(),
        )

        if not match:
            return None

        result = {
            "value": int(match.group("value")),
        }

        description = match.group("description")

        if description:
            result["description"] = description.strip()

        return result

    def adapt_hit_points(
        self,
        value: Any,
    ) -> dict[str, int] | None:
        if value is None:
            return None

        match = re.match(r"^(?P<hp>\d+)", str(value).strip())

        if not match:
            return None

        hp = int(match.group("hp"))

        return {
            "maximum": hp,
            "current": hp,
        }

    def adapt_hit_dice(
        self,
        value: Any,
    ) -> dict[str, int] | None:
        if value is None:
            return None

        match = re.search(
            r"\((?P<count>\d+)d(?P<dice>\d+)(?:[+-]\d+)?\)",
            str(value),
        )

        if not match:
            return None

        return {
            "count": int(match.group("count")),
            "dice": int(match.group("dice")),
        }

    def adapt_movement(
        self,
        value: Any,
    ) -> list[dict[str, Any]] | None:
        if value is None:
            return None

        result = []

        for part in str(value).split(","):
            part = part.strip()

            match = re.match(
                r"^(?:(?P<type>[a-z]+)\s+)?"
                r"(?P<distance>\d+)\s*(?P<unit>ft\.?|miles?)"
                r"(?:\s*\((?P<notes>[^)]+)\))?$",
                part,
                re.IGNORECASE,
            )

            if not match:
                continue

            movement_type = match.group("type") or "walk"
            notes = match.group("notes") or ""

            movement = {
                "movement_type": movement_type.lower(),
                "speed": {
                    "distance": int(match.group("distance")),
                    "unit": self.adapt_distance_type(match.group("unit")),
                },
            }

            if "hover" in notes.lower():
                movement["hover"] = True

            result.append(movement)

        return result or None

    def adapt_distance_type(self, value: str) -> str:
        return DISTANCE_TYPE_MAP[value.lower().rstrip(".")]

    def adapt_saving_throws(
        self,
        value: Any,
    ) -> dict[str, int] | None:
        if value is None:
            return None

        result = {}

        for ability, modifier in re.findall(
            r"(Str|Dex|Con|Int|Wis|Cha)\s*([+-]\d+)",
            str(value),
            re.IGNORECASE,
        ):
            result[ABILITY_MAP[ability.lower()]] = int(modifier)

        return result or None

    def adapt_skills(
        self,
        value: Any,
    ) -> dict[str, int] | None:
        if value is None:
            return None

        result = {}

        for skill, modifier in re.findall(
            r"([^,+]+?)\s*([+-]\d+)(?:,|$)",
            str(value),
        ):
            result[
                skill.strip()
                .lower()
                .replace(" ", "_")
            ] = int(modifier)

        return result or None

    def adapt_damage_types(
        self,
        value: Any,
    ) -> list[str] | None:
        if value is None:
            return None

        return [
            item.strip().lower()
            for item in str(value).split(",")
            if item.strip()
        ] or None

    def adapt_conditions(
        self,
        value: Any,
    ) -> list[str] | None:
        if value is None:
            return None

        return [
            item.strip().lower()
            for item in str(value).split(",")
            if item.strip()
        ] or None

    def adapt_senses(
        self,
        value: Any,
    ) -> list[dict[str, Any]] | None:
        if value is None:
            return None

        result = []

        for sense, distance, unit in re.findall(
            r"([a-z_ ]+?)\s+(\d+)\s*(ft\.?|miles?)",
            str(value),
            re.IGNORECASE,
        ):
            result.append({
                "type": sense.strip().lower().replace(" ", "_"),
                "distance": int(distance),
                "distance_type": self.adapt_distance_type(unit),
            })

        return result or None

    def adapt_int(self, value: Any) -> int | None:
        if value is None:
            return None

        return int(value)

    def adapt_languages(
        self,
        value: Any,
    ) -> list[str] | None:
        if value is None:
            return None

        return [
            language.strip()
            for language in str(value).split(",")
            if language.strip()
        ] or None

    def adapt_features(
        self,
        values: Any,
    ) -> list[dict[str, Any]] | None:
        if not values:
            return None

        result = []

        for value in values:
            feature = self.adapt_feature(value)

            if feature is not None:
                result.append(feature)

        return result or None

    def adapt_feature(
        self,
        value: dict[str, Any],
    ) -> dict[str, Any] | None:
        name = value.get("name")
        text = self.join_text(value.get("text"))

        if not name or not text:
            return None

        if name == "Source":
            return None

        return {
            "name": name,
            "description": text,
        }

    def adapt_actions(
        self,
        values: Any,
    ) -> list[dict[str, Any]] | None:
        if not values:
            return None

        result = []

        for value in values:
            action = self.adapt_action(value)

            if action is not None:
                result.append(action)

        return result or None

    def adapt_action(
        self,
        value: dict[str, Any],
    ) -> dict[str, Any] | None:
        name = value.get("name")
        description = self.join_text(value.get("text"))
        children = self.adapt_actions(value.get("children"))

        if not name:
            return None

        result = {
            "name": name,
        }

        if description:
            result["description"] = description

        if children:
            result["children"] = children

        if len(result) == 1:
            return None

        return result

    def adapt_challenge_rating(
        self,
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        return float(value)

    def adapt_environments(
        self,
        values: Any,
    ) -> list[str] | None:
        if not values:
            return None

        return [
            str(value).strip().lower()
            for value in values
            if str(value).strip()
        ] or None

    def join_text(
        self,
        values: Any,
    ) -> str | None:
        if not values:
            return None

        sections = []
        current = []

        for value in values:
            if value is None:
                if current:
                    sections.append("\n".join(current))
                    current = []
                continue

            current.append(str(value))

        if current:
            sections.append("\n".join(current))

        if not sections:
            return None

        return "\n\n".join(sections)