from __future__ import annotations

from common.state_enum import StateEnum
from models.search_strings import DAMAGE_ROLL
import re
from typing import Any

CONDITIONS = {
    "blinded",
    "charmed",
    "deafened",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious"
}

SCHOOL_MAP = {
    "EV": "evocation",
    "A": "abjuration",
    "C": "conjuration",
    "D": "divination",
    "EN": "enchantment",
    "N": "necromancy",
    "T": "transmutation"
}

RITUAL_MAP = {
    "YES": True,
    "NO": False
}

class SpellAdaptor:
    """Adapt parsed spell source data into the Spell schema."""

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = [value for value in source.get("text", []) if value]
        description = self.description(text)
        result = {
            "name": source.get("name"),
            "level": self.level(source.get("level")),
            "school": self.school(source.get("school")),
            "ritual": self.ritual(source.get("ritual")),
            "casting_time": self.casting_time(source.get("time")),
            "target": self.target(source.get("range")),
            "components": self.components(source.get("components")),
            "duration": self.duration(source.get("duration")),
            "material": self.material(source.get("components")),
            "concentration": self.concentration(source.get("duration")),
            "classes": self.classes(source.get("classes")),
            "description": description,
            "effects": self.effects(description),
            "roll_table": self.roll_table(text),
            "source": self.source(text),
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }

    def level(self, level: Any) -> int | None:
        try:
            return int(level)
        except (TypeError, ValueError):
            return None
        
    def school(self, school_str: str) -> str | None:
        if not school_str:
            return None
        return SCHOOL_MAP.get(school_str.upper(), school_str.lower())
    
    def ritual(self, ritual_str: str) -> bool | None:
        if not ritual_str:
            return None
        return RITUAL_MAP.get(ritual_str.upper())
    
    def casting_time(self, casting_time_str: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        if not casting_time_str:
            return None

        values = re.split(
            r"\s+or\s+(?=(?:(?:\d+)\s+)?(?:bonus action|action|reaction|round|minute|hour)s?\b)",
            casting_time_str.strip(),
            flags=re.IGNORECASE,
        )
        results = []
        for value in values:
            match = re.match(
                r"\s*(?:(\d+)\s+)?(bonus action|action|reaction|round|minute|hour)s?",
                value.lower(),
            )
            if match is None:
                return None

            unit = match.group(2).replace(" ", "_")
            result: dict[str, Any] = {"unit": unit}
            if match.group(1) is not None or unit in {"round", "minute", "hour"}:
                result["amount"] = int(match.group(1) or 1)
            results.append(result)

        return results if len(results) > 1 else results[0]

    def target(self, range_str: str | None) -> dict[str, Any] | None:
        if not range_str:
            return None

        value = range_str.strip().lower()
        if value == "touch":
            return {"targeting": "touch"}
        if value in {"special", "sight", "unlimited"}:
            return {"targeting": value}
        if value.startswith("self"):
            result: dict[str, Any] = {"targeting": "self"}
            zone = re.search(r"(\d+)\s+foot\s+(cone|cube|cylinder|line|sphere)", value)
            if zone:
                result["zone"] = {
                    "type": zone.group(2),
                    "size": int(zone.group(1)),
                }
            return result

        distance = re.fullmatch(r"(\d+)\s*(feet|foot|ft|miles?|mi)", value)
        if distance:
            return {
                "targeting": "range",
                "range": {
                    "amount": int(distance.group(1)),
                    "unit": "miles" if distance.group(2).startswith(("mile", "mi")) else "feet",
                },
            }
        return {"targeting": "range", "description": range_str}

    def components(self, components_str: str | None) -> list[str] | None:
        if not components_str:
            return None

        result = []
        for component in components_str.split(","):
            code = component.strip().split(" ", 1)[0].upper()
            if code == "V":
                result.append("verbal")
            elif code == "S":
                result.append("somatic")
            elif code == "M":
                result.append("material")
        return result or None

    def material(self, components_str: str | None) -> dict[str, Any] | None:
        if not components_str or "M" not in components_str.upper():
            return None

        description = re.search(r"M\s*\((.*)\)", components_str)
        return {"description": description.group(1).strip() if description else ""}

    def duration(self, duration_str: str | None) -> dict[str, Any] | None:
        if not duration_str:
            return None

        value = duration_str.lower().replace(",", " ")
        if "instantaneous" in value:
            return {"duration": "instantaneous"}

        match = re.search(r"(\d+)\s+(round|minute|hour|day|week|month|year)", value)
        if match:
            return {"amount": int(match.group(1)), "duration": match.group(2)}

        return {"duration": "until_dispelled"}

    def concentration(self, duration_str: str | None) -> bool | None:
        if not duration_str:
            return None
        return duration_str.lower().startswith("concentration")

    def classes(self, classes_str: str | None) -> list[str] | None:
        if not classes_str:
            return None
        classes = []
        for value in classes_str.split(","):
            class_name = value.strip().lower()
            if class_name and class_name not in classes:
                classes.append(class_name)
        return classes or None

    def description(self, text: list[str]) -> str | None:
        paragraphs = [value for value in text if not value.lower().startswith("source:")]
        return "\n\n".join(paragraphs) or None

    def effects(self, description: str | None) -> list[dict[str, Any]] | None:
        if not description:
            return None

        damages = []
        for match in DAMAGE_ROLL.finditer(description):
            damages.append({
                "damage": {
                    "type": match.group("type").lower(),
                    "roll": {
                        "count": int(match.group("count") or 1),
                        "dice": int(match.group("dice")),
                        **self.modifier(match.group("modifier")),
                    },
                },
            })
        if not damages:
            return None

        save = re.search(
            r"(?P<ability>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)"
            r"\s+saving throw",
            description,
            re.IGNORECASE,
        )
        if save is None:
            return damages

        attack_save: dict[str, Any] = {
            "ability": save.group("ability").lower(),
            "failure": damages,
        }
        if re.search(r"half as much|successful save|successful one", description, re.IGNORECASE):
            attack_save["success"] = [
                {**damage, "description": "(Halved)"}
                for damage in damages
            ]
        return [{"attack_save": attack_save}]

    def modifier(self, value: str | None) -> dict[str, int]:
        return {"modifier": int(value)} if value else {}

    def roll_table(self, text: list[str]) -> dict[str, Any] | None:
        entries = []
        ability = None
        for value in text:
            ability_match = re.search(r"(\w+) saving throw", value, re.IGNORECASE)
            if ability_match and ability is None:
                ability = ability_match.group(1).lower()

            entry_match = re.match(r"\s*(\d+)\s+([^:]+):\s*(.*)", value)
            if entry_match is None:
                continue

            roll = int(entry_match.group(1))
            result = entry_match.group(2).strip()
            description = entry_match.group(3).strip()
            effects: list[dict[str, Any]] = []
            damage_match = re.search(
                r"(\d+)d(\d+)\s+([a-z]+) damage",
                description,
                re.IGNORECASE,
            )
            if damage_match and ability:
                damage = {
                    "type": damage_match.group(3).lower(),
                    "roll": {
                        "count": int(damage_match.group(1)),
                        "dice": int(damage_match.group(2)),
                    },
                }
                effects.append({
                    "attack_save": {
                        "ability": ability,
                        "failure": [{"damage": damage}],
                        "success": [{
                            "damage": damage,
                            "description": "(Halved)",
                        }],
                    },
                })
            elif result.lower() == "indigo":
                effects.append({
                    "attack_save": {
                        "ability": ability or "constitution",
                        "failure": [
                            {"condition": "restrained"},
                            {"description": description},
                        ],
                    },
                })
            elif result.lower() == "violet":
                effects.append({
                    "attack_save": {
                        "ability": ability or "wisdom",
                        "failure": [
                            {"condition": "blinded"},
                            {"description": description},
                        ],
                    },
                })
            elif description:
                effects.append({"description": description})

            entry = {"roll": roll, "result": result}
            if effects:
                entry["effects"] = effects
            entries.append(entry)

        if not entries:
            return None

        return {"dice": max(entry["roll"] for entry in entries), "entries": entries}
    def separate_conditions(self, text: list[str]) -> tuple[dict[str, str], str]:
        conditions = {}
        condition = ""
        condition_description = []
        remaining_text = []
        class description_states(StateEnum):
            REGULAR = 0
            CONDITION = 1
            CONDITION_DESCRIPTION = 2
        
        state = description_states.REGULAR
        for line in text:
            match state:
                case description_states.REGULAR:
                    if line is None:
                        continue
                    first_word, is_condition = self.first_word_in_conditions(line)
                    if is_condition:
                        state = description_states.CONDITION
                        condition = first_word
                    else:
                        remaining_text.append(line)
                case description_states.CONDITION:
                    if line is None:
                        continue
                    if re.match(r"^\s*[A-Z•]", line):
                        state = description_states.CONDITION_DESCRIPTION
                        line = re.sub(r"^\s*•\s*", "", line)
                        condition_description.append(line)
                    else:
                        # Oops, lets put that condition back into description
                        condition_description.append(line)
                        remaining_text.extend(condition_description)
                        condition_description = []
                        conditions.pop(condition, None)
                        condition = ""
                        state = description_states.REGULAR
                case description_states.CONDITION_DESCRIPTION:
                    if line is None:
                        continue
                    first_word, is_condition = self.first_word_in_conditions(line)
                    if is_condition:
                        conditions[condition] = condition_description.copy()
                        condition_description = []
                        state = description_states.CONDITION
                        condition = first_word
                    elif re.match(r"^\s*[A-Z•]", line):
                        state = description_states.CONDITION_DESCRIPTION
                        line = re.sub(r"^\s*•\s*", "", line)
                        condition_description.append(line)
                    else:
                        remaining_text.append(line)
                        conditions[condition] = condition_description.copy()
                        condition = ""
                        condition_description = []
                        state = description_states.REGULAR
                case _:
                    remaining_text.append(line)
                    
        description_str = "\n".join(remaining_text)
        conditions = {k: '\n'.join(v) for k, v in conditions.items()}

        return conditions, description_str
    
    def first_word_in_conditions(self, line: str):
        if line is None:
            return None, False
        first_word = line.split()[0].lower() if line.split() else ""
        first_word = re.sub(r"[^A-Za-z]", "", first_word)
        if first_word in CONDITIONS:
            return first_word, True
        return first_word, False
    

    def source(self, text: list[str]):
        last_line = text[-1] if text else None
        if last_line and last_line.lower().startswith("source:"):
            return {"text": last_line.split(":", 1)[1].strip()}
        return None