from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .components import Feature, Movement, Source, SpellGrant, WeaponProficiency


class AbilityScoreIncrease(BaseModel):
    ability: str
    amount: int = Field(ge=1)


class Race(BaseModel):
    name: str = Field(min_length=1)
    subtype: str | None = Field(default=None, min_length=1)
    size: str | None = None
    movement: list[Movement] | None = None
    ability_score_increases: list[AbilityScoreIncrease] | None = None
    features: list[Feature] | None = None
    skill_proficiencies: list[str] | None = None
    languages: list[str] | None = None
    senses: list[dict[str, Any]] | None = None
    spell_grants: list[SpellGrant] | None = None
    weapon_proficiencies: list[WeaponProficiency] | None = None
    source: Source | None = None

    model_config = {"extra": "forbid"}