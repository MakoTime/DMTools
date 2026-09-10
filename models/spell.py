from __future__ import annotations

from pydantic import BaseModel, Field

from .components import Effect, Grant, RollTable, Source, Target
from .item import DurationAmount


class CastingTime(BaseModel):
    amount: int | None = Field(default=None, ge=1)
    unit: str


class MaterialComponent(BaseModel):
    description: str
    cost: float | None = Field(default=None, ge=0)
    consumed: bool = False


class Spell(BaseModel):
    name: str = Field(min_length=1)
    description: str
    higher_level: str | None = None
    level: int = Field(ge=0, le=9)
    school: str | None = None
    classes: list[str] | None = None
    casting_time: CastingTime | list[CastingTime]
    target: Target | None = None
    components: list[str] = Field(min_length=1)
    material: MaterialComponent | None = None
    ritual: bool = False
    concentration: bool = False
    duration: DurationAmount
    effects: list[Effect] | None = None
    roll_table: RollTable | None = None
    tags: list[str] | None = None
    source: Source | None = None
    grants: list[Grant] | None = None
