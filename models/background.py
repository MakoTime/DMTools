from __future__ import annotations

from pydantic import BaseModel, Field

from .components import Feature, Source


class Background(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    skill_proficiencies: list[str] | None = None
    tool_proficiencies: list[str] | None = None
    languages: list[str] | None = None
    features: list[Feature] | None = None
    source: Source | None = None

    model_config = {"extra": "forbid"}