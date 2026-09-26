from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .common import AbilityScore, Dice
from .components import Feature, SpellGrant, WeaponProficiency


class SkillChoice(BaseModel):
    choose: int = Field(ge=1)
    from_: list[str] = Field(alias="from", min_length=1)

    model_config = {"populate_by_name": True}


class ToolChoice(SkillChoice):
    pass


class Spellcasting(BaseModel):
    ability: str
    progression: str
    ritual: bool = False
    prepared: bool = False
    spells: SpellGrant | None = None


class ClassResourceLevel(BaseModel):
    level: int = Field(ge=1, le=20)
    maximum: int | str | None = None
    value: int | str | None = None
    dice: Dice | None = None

    @model_validator(mode="after")
    def validate_value(self):
        values = (self.maximum, self.value, self.dice)
        if sum(value is not None for value in values) != 1:
            raise ValueError("Resource level requires exactly one maximum, value, or dice")
        if isinstance(self.maximum, int) and self.maximum < 1:
            raise ValueError("Resource maximum must be positive")
        return self


class ClassResource(BaseModel):
    name: str = Field(min_length=1)
    maximum_formula: str | None = Field(default=None, min_length=1)
    ability: AbilityScore | None = None
    minimum_level: int | None = Field(default=None, ge=1, le=20)
    levels: list[ClassResourceLevel] | None = Field(default=None, min_length=1)
    recharge: str | None = None

    @model_validator(mode="after")
    def validate_maximum(self):
        if self.maximum_formula is None and self.levels is None:
            raise ValueError("Resource requires maximum_formula or levels")
        if self.levels is not None:
            if len(self.levels) < 2:
                raise ValueError("Resource progression requires at least two levels")
            if min(level.level for level in self.levels) > 3:
                raise ValueError("Resource progression must begin by level 3")
            if any(
                earlier.level >= later.level
                for earlier, later in zip(self.levels, self.levels[1:])
            ):
                raise ValueError("Resource progression levels must be increasing")
            amounts = [
                level.maximum
                if level.maximum is not None
                else level.value
                if level.value is not None
                else level.dice
                for level in self.levels
            ]
            for earlier, later in zip(amounts, amounts[1:]):
                if (
                    isinstance(earlier, int)
                    and isinstance(later, int)
                    and later <= earlier
                ):
                    raise ValueError("Resource progression values must increase")
                if earlier == "unlimited":
                    raise ValueError("Unlimited must be the final resource value")
        if self.maximum_formula == "ability_modifier" and self.ability is None:
            raise ValueError("Ability modifier resources require an ability")
        return self


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
    tool_choices: ToolChoice | None = None
    spellcasting: Spellcasting | None = None
    resources: list[ClassResource] | None = None
    features: list[Feature] | None = None
    repeating_features: list[Feature] | None = None
    required_stats: list[str] | None = None
    starting_class: str | None = None
    multiclassing: str | None = None
    ability_score_increase: list[int] | None = None

    model_config = {"extra": "forbid"}