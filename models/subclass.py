from __future__ import annotations

from pydantic import BaseModel, Field

from .components import Feature, Source, SpellGrant


class Subclass(BaseModel):
    name: str = Field(min_length=1)
    class_name: str = Field(alias="class", min_length=1)
    description: str | None = None
    features: list[Feature] | None = None
    spells: list[SpellGrant] | None = None
    tags: list[str] | None = None
    source: Source | None = None

    model_config = {"populate_by_name": True, "extra": "forbid"}