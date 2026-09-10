from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .components import Source


AbilityKind = Literal[
    "maneuver",
    "eldritch_invocation",
    "infusion",
    "monk_technique",
    "other",
]


class Ability(BaseModel):
    name: str = Field(min_length=1)
    kind: AbilityKind
    description: str = Field(min_length=1)
    level: int | None = Field(default=None, ge=0, le=20)
    classes: list[str] | None = None
    prerequisites: list[str] | None = None
    source: Source | None = None

    model_config = {"extra": "forbid"}