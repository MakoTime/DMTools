from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator

from .common import (
    AbilityScore,
    ActionType,
    AttackType,
    Condition,
    DamageType,
    Dice,
    DistanceType,
    MovementType,
    SenseType,
    Skill,
    TargetType,
    TargetZoneType,
)

from .search_strings import (
    BECOMES_CONDITION,
    DAMAGE,
    MELEE_OR_RANGED_ATTACK,
    NUMBERED_ENTRY,
    RANGE,
    RANGE_WITH_UNIT,
    REACH,
    SAVING_THROW_ANY_DC,
    TARGET_COUNT,
    parse_number,
)

class AbilityScores(BaseModel):
    strength: int = Field(ge=1)
    dexterity: int = Field(ge=1)
    constitution: int = Field(ge=1)
    intelligence: int = Field(ge=1)
    wisdom: int = Field(ge=1)
    charisma: int = Field(ge=1)


class HitPoints(BaseModel):
    maximum: int = Field(ge=0)
    current: int = Field(ge=0)
    temporary: int = Field(default=0, ge=0)
    maximum_change: int = 0


class HitDice(BaseModel):
    count: int = Field(default=1, ge=1)
    dice: Dice


class Speed(BaseModel):
    distance: int = Field(ge=0)
    unit: DistanceType


class Movement(BaseModel):
    movement_type: MovementType
    speed: Speed
    hover: bool = False


class SavingThrows(BaseModel):
    strength: int | None = None
    dexterity: int | None = None
    constitution: int | None = None
    intelligence: int | None = None
    wisdom: int | None = None
    charisma: int | None = None


class Sense(BaseModel):
    type: SenseType
    distance: int = Field(ge=0)
    distance_type: DistanceType


class Feature(BaseModel):
    name: str = Field(min_length=1)
    description: str
    level: int | None = Field(default=None, ge=1, le=20)
    source: Source | None = None


class Source(BaseModel):
    text: str | None = None
    note: str | None = None
    href: str | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.text is None and self.href is None:
            raise ValueError("Source requires either 'text' or 'href'")
        return self


class Distance(BaseModel):
    amount: int = Field(ge=0)
    unit: DistanceType


class TargetCount(BaseModel):
    minimum: int | None = Field(default=None, ge=1)
    maximum: int | None = Field(default=None, ge=1)
    all: bool | None = None

    @model_validator(mode="after")
    def validate_count(self):
        if self.all:
            if self.minimum is not None or self.maximum is not None:
                raise ValueError(
                    "'all' cannot be combined with 'minimum' or 'maximum'"
                )
        elif self.minimum is None and self.maximum is None:
            raise ValueError(
                "TargetCount requires 'all', 'minimum', or 'maximum'"
            )

        return self


class TargetZone(BaseModel):
    type: TargetZoneType
    size: int = Field(ge=0)


class Target(BaseModel):
    targeting: str
    range: Distance | None = None
    type: TargetType | None = None
    count: TargetCount | None = None
    zone: TargetZone | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if self.targeting == "range" and self.range is None:
            raise ValueError(
                "'range' is required when targeting is 'range'"
            )

        return self

    @classmethod
    def from_description(cls, description: str | None) -> Target | None:
        if not description:
            return None

        attack_match = MELEE_OR_RANGED_ATTACK.search(description)
        target_description = (
            attack_match.group(0) if attack_match else description
        )
        range_match = RANGE.search(target_description)
        if range_match is None:
            range_match = RANGE_WITH_UNIT.search(target_description)
        reach_match = REACH.search(target_description)
        distance_match = range_match or reach_match

        if distance_match is None:
            return None

        amount = int(distance_match.group("distance"))
        count = None

        count_match = TARGET_COUNT.search(target_description)

        if count_match:
            minimum = parse_number(count_match.group("minimum"))
            count = TargetCount(
                minimum=(minimum if count_match.group("maximum") else None),
                maximum=(
                    parse_number(count_match.group("maximum"))
                    if count_match.group("maximum")
                    else minimum
                )
            )

        return cls(
            targeting="range",
            range=Distance(amount=amount, unit="feet"),
            count=count,
        )


class Roll(BaseModel):
    dice: Dice | None = None
    count: int | None = Field(default=1, ge=1)
    modifier: int | None = None
    ability: AbilityScore | None = None

    @model_validator(mode="after")
    def validate_roll(self):
        if (
            self.dice is None
            and self.modifier is None
            and self.ability is None
        ):
            raise ValueError(
                "Roll requires dice, modifier, or ability"
            )

        return self


class Damage(BaseModel):
    type: DamageType
    roll: Roll
    modifier: int = 0
    ability: AbilityScore | None = None

    @classmethod
    def from_description(cls, description: str) -> Damage | None:
        match = DAMAGE.search(description)

        if match is None:
            return None

        modifier = match.group("modifier")

        return cls(
            type=DamageType(match.group("type").lower()),
            roll=Roll(
                dice=int(match.group("dice")),
                count=int(match.group("count") or 1),
                modifier=int(modifier) if modifier else None,
            ),
        )


class AttackHit(BaseModel):
    type: AttackType
    bonus: int = 0
    effects: list[Effect] | None = None

    @classmethod
    def from_description(cls, description: str) -> AttackHit | None:
        match = MELEE_OR_RANGED_ATTACK.search(description)

        if match is None:
            return None

        hit_effects = Effect.from_description(match.group("hit"))

        return cls(
            type=AttackType(
                f"{match.group('attack_type').lower()}_"
                f"{match.group('weapon_type').lower()}"
            ),
            bonus=int(match.group("bonus")),
            effects=[hit_effects] if hit_effects else None,
        )


class AttackSave(BaseModel):
    ability: AbilityScore
    dc: int | None = Field(default=None, ge=1)
    success: list[Effect] | None = None
    failure: list[Effect] | None = None

    @classmethod
    def from_description(cls, description: str) -> AttackSave | None:
        match = SAVING_THROW_ANY_DC.search(description)

        if match is None:
            return None

        consequence = description[match.end():].strip()
        consequence = re.sub(r"^or\s+", "", consequence, flags=re.IGNORECASE)
        effects = Effect.from_description(consequence)

        return cls(
            ability=AbilityScore(match.group("ability").lower()),
            dc=int(match.group("dc")),
            failure=[effects] if effects else None,
        )


class Grant(BaseModel):
    type: str
    ability_check: AbilityScore | None = None
    skill: Skill | None = None
    saving_throw: AbilityScore | Condition | None = None
    condition: Condition | None = None
    damage_type: DamageType | None = None
    sense: SenseType | None = None
    distance: int | None = Field(default=None, ge=0)
    movement_type: MovementType | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_grant(self):
        if self.type in {
            "resistance",
            "vulnerability",
            "immunity",
        }:
            if self.damage_type is None:
                raise ValueError(
                    f"'{self.type}' grant requires 'damage_type'"
                )

        elif self.type == "sense":
            if self.sense is None or self.distance is None:
                raise ValueError(
                    "'sense' grant requires 'sense' and 'distance'"
                )

        elif self.type == "movement":
            if self.movement_type is None or self.distance is None:
                raise ValueError(
                    "'movement' grant requires "
                    "'movement_type' and 'distance'"
                )

        return self


class Effect(BaseModel):
    damage: Damage | None = None
    healing: Roll | None = None
    max_hit_points: Roll | None = None
    temporary_hit_points: Roll | None = None
    ability_score: Roll | None = None
    exhaustion: Roll | None = None
    attack_hit: AttackHit | None = None
    attack_save: AttackSave | None = None
    condition: Condition | None = None
    grants: list[Grant] | None = None
    description: str | None = None

    @classmethod
    def from_description(cls, description: str) -> Effect | None:
        attack_hit = AttackHit.from_description(description)

        if attack_hit is not None:
            return cls(attack_hit=attack_hit)

        attack_save = AttackSave.from_description(description)

        if attack_save is not None:
            return cls(attack_save=attack_save)

        damage = Damage.from_description(description)

        if damage is not None:
            return cls(damage=damage)

        condition = BECOMES_CONDITION.search(description)

        if condition is not None:
            return cls(
                condition=Condition(condition.group("condition").lower())
            )

        return cls(description=description.strip())

    @model_validator(mode="after")
    def validate_effect(self):
        if not any(
            value is not None
            for value in (
                self.damage,
                self.healing,
                self.max_hit_points,
                self.temporary_hit_points,
                self.ability_score,
                self.exhaustion,
                self.attack_hit,
                self.attack_save,
                self.condition,
                self.grants,
                self.description,
            )
        ):
            raise ValueError(
                "Effect must contain at least one property"
            )

        return self


class Action(BaseModel):
    name: str = Field(min_length=1)
    description: str
    type: ActionType | None = None
    target: Target | None = None
    effects: list[Effect] | None = None
    roll_table: RollTable | None = None

    @model_validator(mode="before")
    @classmethod
    def delegate_description(cls, values):
        if not isinstance(values, dict):
            return values

        derived_roll_table = False

        if values.get("roll_table") is None:
            roll_table = RollTable.from_description(values.get("description"))

            if roll_table is not None:
                values = values.copy()
                values["roll_table"] = roll_table
                derived_roll_table = True

        if values.get("target") is None:
            target = Target.from_description(values.get("description"))

            if target is not None:
                values = values.copy()
                values["target"] = target

        if values.get("effects") is None and not derived_roll_table:
            effect = Effect.from_description(values.get("description", ""))

            if effect is not None:
                values = values.copy()
                values["effects"] = [effect]

        return values


class SpellCasting(BaseModel):
    ability: AbilityScore | None = None
    save_dc: int | None = Field(default=None, ge=1)
    attack_bonus: int | None = None
    spells_known: SpellsKnown | None = None


class SpellsKnown(BaseModel):
    cantrips: list[str] | None = None
    level_1: SpellsKnown | None = None
    level_2: SpellsKnown | None = None
    level_3: SpellsKnown | None = None
    level_4: SpellsKnown | None = None
    level_5: SpellsKnown | None = None
    level_6: SpellsKnown | None = None
    level_7: SpellsKnown | None = None
    level_8: SpellsKnown | None = None
    level_9: SpellsKnown | None = None
    at_will: list[str] | None = None


class RollTableEntry(BaseModel):
    roll: int = Field(ge=1)
    result: str = Field(min_length=1)
    effects: list[Effect] | None = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="before")
    @classmethod
    def delegate_description(cls, values):
        if not isinstance(values, dict) or values.get("effects") is not None:
            return values

        description = values.get("description")

        if description:
            effect = Effect.from_description(description)

            if effect is not None:
                values = values.copy()
                values["effects"] = [effect]

        return values


class RollTable(BaseModel):
    count: int | None = Field(default=None, ge=1)
    dice: Dice
    entries: list[RollTableEntry] = Field(min_length=1)

    @classmethod
    def from_description(cls, description: str | None) -> RollTable | None:
        if not description:
            return None

        matches = list(NUMBERED_ENTRY.finditer(description))

        if not matches:
            return None

        return cls.model_validate(
            {
                "dice": max(
                    int(match.group("number"))
                    for match in matches
                ),
                "entries": [
                    {
                        "roll": int(match.group("number")),
                        "result": match.group("name").strip(),
                        "description": match.group("description").strip(),
                    }
                    for match in matches
                ],
            }
        )


class Image(BaseModel):
    uri: str
    alt: str
    caption: str | None = None
    source: Source | None = None