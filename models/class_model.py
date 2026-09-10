from __future__ import annotations

from pydantic import BaseModel, Field

from .components import WeaponProficiency


class SkillChoice(BaseModel):
    choose: int = Field(ge=1)
    from_: list[str] = Field(alias="from", min_length=1)

    model_config = {"populate_by_name": True}


class Spellcasting(BaseModel):
    ability: str
    progression: str


class Class(BaseModel):
    name: str = Field(min_length=1)
    hit_dice: int
    description: str | None = None
    primary_abilities: list[str] | None = None
    saving_throws: list[str] | None = None
    armor_proficiencies: list[str] | None = None
    weapon_proficiencies: list[WeaponProficiency] | None = None
    tool_proficiencies: list[str] | None = None
    skill_choices: SkillChoice | None = None
    spellcasting: Spellcasting | None = None

    model_config = {"extra": "forbid"}