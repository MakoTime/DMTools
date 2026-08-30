from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .components import (
    Effect,
    Feature,
    Grant,
    Image,
    Roll,
    RollTable,
    Source,
)


class DurationAmount(BaseModel):
    amount: int | None = Field(default=None, ge=1)
    duration: str

    @model_validator(mode="after")
    def validate_duration(self):
        requires_amount = self.duration in {
            "round",
            "minute",
            "hour",
            "day",
            "week",
            "month",
            "year",
        }

        if requires_amount and self.amount is None:
            raise ValueError(
                "DurationAmount requires 'amount' for this duration"
            )

        if self.duration == "instantaneous" and self.amount is not None:
            raise ValueError(
                "Instantaneous duration cannot have an amount"
            )

        return self


class Bonus(BaseModel):
    type: Literal[
        "attack",
        "damage",
        "armor_class",
        "ability_score",
        "maximum_hit_points",
        "saving_throw",
    ] | str
    value: int
    ability: str | None = None

    @model_validator(mode="after")
    def validate_ability_bonus(self):
        if self.type == "ability_score" and self.ability is None:
            raise ValueError(
                "Ability-score bonuses require 'ability'"
            )
        return self


class Cost(BaseModel):
    amount: int = Field(ge=1)
    currency: str


class MagicItemCharges(BaseModel):
    maximum: int = Field(ge=1)
    recharge: Roll | Literal["all"] | None = None
    recharge_duration: DurationAmount | None = None
    depletion: str | None = None

    @model_validator(mode="after")
    def validate_recharge(self):
        if self.recharge is not None and self.recharge_duration is None:
            raise ValueError(
                "Recharge requires 'recharge_duration'"
            )
        return self


class SpellCharge(BaseModel):
    spell: str
    charges: int = Field(default=1, ge=1)


class Weapon(BaseModel):
    type: str | None = None
    effects: list[Effect] | None = Field(default=None, min_length=1)
    properties: list[str] | None = None
    range: Range | None = None


class Range(BaseModel):
    normal: int = Field(ge=0)
    long: int | None = Field(default=None, ge=0)


class Armor(BaseModel):
    category: str
    type: str | None = None
    armor_class: int = Field(ge=0)
    add_dexterity: AddDexterity | None = None
    stealth_disadvantage: bool = False
    strength_requirement: int | None = Field(default=None, ge=1)


class AddDexterity(BaseModel):
    enabled: bool = True
    maximum: int | None = Field(default=None, ge=0)


class MagicItem(BaseModel):
    attunement: bool = False
    bonuses: list[Bonus] | None = None
    effects: list[Effect] | None = None
    rarity: str | None = None
    charges: MagicItemCharges | None = None
    spells: list[SpellCharge] | None = None
    roll_table: RollTable | None = None
    grants: list[Grant] | None = None


class Item(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    category: str | None = None
    weapon: Weapon | None = None
    armor: Armor | None = None
    magic_item: MagicItem | None = None
    weight: float | None = Field(default=None, ge=0)
    cost: Cost | None = None
    features: list[Feature] | None = None
    source: Source | None = None
    image: Image | None = None

    model_config = {"extra": "forbid"}