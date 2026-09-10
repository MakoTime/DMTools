from __future__ import annotations

from pydantic import BaseModel, Field

from .components import Feature, Source, SpellGrant, WeaponProficiency


class AbilityScoreIncrease(BaseModel):
    ability: str
    amount: int = Field(ge=1)


class Feat(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    prerequisite: str | None = None
    ability_score_increases: list[AbilityScoreIncrease] | None = None
    spell_grants: list[SpellGrant] | None = None
    weapon_proficiencies: list[WeaponProficiency] | None = None
    features: list[Feature] | None = None
    source: Source | None = None

    model_config = {"extra": "forbid"}