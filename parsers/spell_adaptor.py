from __future__ import annotations

from common.state_enum import StateEnum
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
    "EV": "Evocation",
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "EN": "Enchantment",
    "N": "Necromancy",
    "T": "Transmutation"
}

RITUAL_MAP = {
    "YES": True,
    "NO": False
}

class SpellAdaptor:
    """Adapt parsed spell source data into the Spell schema."""

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = source.get("text", [])
        description = self.description(text)
        effects = self.effects(text)
        result = {
            "name": source.get("name"),
            "level": source.get("level"),
            "school": self.school(source.get("school")),
            "ritual": self.ritual(source.get("ritual")),
            "casting_time": self.casting_time(source.get("casting_time")),
            "range": source.get("range"),
            "components": self.components(source.get("components")),
            "duration": self.duration(source.get("duration")),
            "material": self.material(source.get("components")),
            "concentration": self.concentration(source.get("duration")),
            "description": description,
            "effects": effects,
            "source": self.source(text),
        }

        return {
            key: value
            for key, value in result.items()
            if value is not None
        }
        
    def school(self, school_str: str) -> str | None:
        if not school_str:
            return None
        return SCHOOL_MAP.get(school_str, None)
    
    def ritual(self, ritual_str: str) -> bool | None:
        if not ritual_str:
            return None
        return RITUAL_MAP.get(ritual_str, None)
    
    def casting_time(self, casting_time_str: str) -> str | None:
        
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
            return last_line
        return None