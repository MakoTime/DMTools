from __future__ import annotations

import re
from typing import Any


class AbilityAdaptor:
    """Adapt spell-shaped source records into selectable abilities."""

    @classmethod
    def kind_for(cls, source: dict[str, Any]) -> str | None:
        classes = (source.get("classes") or "").lower()
        name = (source.get("name") or "").lower()
        text = " ".join(value or "" for value in source.get("text", [])).lower()

        if "eldritch invocation" in classes:
            return "eldritch_invocation"
        if "artificer infusion" in classes or name.startswith("infusion:"):
            return "infusion"
        if (
            "battle master" in classes
            or "martial adept" in classes
            or "superiority die" in text
        ):
            return "maneuver"
        if "arcane archer" in classes:
            return "other"
        if "monk" in classes:
            return "monk_technique"
        return None

    @classmethod
    def is_custom_ability(cls, source: dict[str, Any]) -> bool:
        return cls.kind_for(source) is not None

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        text = [value for value in source.get("text", []) if value]
        kind = self.kind_for(source) or "other"
        result = {
            "name": str(source.get("name") or "").strip(),
            "kind": kind,
            "description": self.description(text),
            "level": self.level(source.get("level")),
            "classes": self.classes(source.get("classes")),
            "prerequisites": self.prerequisites(text),
            "source": self.source(text),
        }
        return {key: value for key, value in result.items() if value is not None}

    def description(self, text: list[str]) -> str | None:
        values = [value for value in text if not value.lower().startswith("source:")]
        return "\n\n".join(values).strip() or None

    def level(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def classes(self, value: Any) -> list[str] | None:
        if not value:
            return None
        result = []
        for item in str(value).split(","):
            item = item.strip().lower()
            if item and item not in result:
                result.append(item)
        return result or None

    def prerequisites(self, text: list[str]) -> list[str] | None:
        result = []
        for value in text:
            match = re.match(r"\s*prerequisite:\s*(.+)", value, re.IGNORECASE)
            if match:
                result.append(match.group(1).strip())
        return result or None

    def source(self, text: list[str]) -> dict[str, str] | None:
        for value in text:
            if value.lower().startswith("source:"):
                return {"text": value.split(":", 1)[1].strip()}
        return None