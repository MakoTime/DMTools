from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .common import (
	Condition,
	CreatureType,
	DamageType,
	Size,
)
from .components import (
	AbilityScores,
	Action,
	Feature,
	HitDice,
	HitPoints,
	Image,
	Movement,
	RollTable,
	SavingThrows,
	Sense,
	Source,
	SpellCasting,
)


class Alignment(BaseModel):
	order: Literal["lawful", "neutral", "chaotic"] | None = None
	morality: Literal["good", "neutral", "evil"] | None = None

	@model_validator(mode="after")
	def validate_alignment(self):
		if self.order is None and self.morality is None:
			raise ValueError(
				"Alignment requires 'order' or 'morality'"
			)
		return self


class ArmorClass(BaseModel):
	value: int = Field(ge=0)
	description: str | None = None


class Creature(BaseModel):
	name: str = Field(min_length=1)
	size: Size | None = None
	creature_type: CreatureType | None = None
	alignment: Alignment | Literal["unaligned", "any"] | str | None = None
	ability_scores: AbilityScores | None = None
	hit_points: HitPoints | None = None
	hit_dice: HitDice | None = None
	armor_class: ArmorClass | None = None
	movement: list[Movement] | None = None
	saving_throws: SavingThrows | None = None
	skills: dict[str, int] | None = None
	senses: list[Sense] | None = None
	passive_perception: int | None = Field(default=None, ge=0)
	languages: list[str] | None = None
	proficiency_bonus: int | None = Field(default=None, ge=0)
	condition_immunities: list[Condition | str] | None = None
	damage_immunities: list[DamageType | str] | None = None
	damage_resistances: list[DamageType | str] | None = None
	damage_vulnerabilities: list[DamageType | str] | None = None
	features: list[Feature] | None = None
	actions: list[Action] | None = None
	reactions: list[Action] | None = None
	legendary_actions: list[Action] | None = None
	spell_casting: SpellCasting | None = None
	roll_table: RollTable | None = None
	challenge_rating: float | str | None = None
	environments: list[str] | None = None
	description: str | None = None
	image: Image | None = None
	source: Source | None = None

	model_config = {"extra": "forbid"}


class Monster(Creature):
	challenge_rating: float | str = Field(...)
