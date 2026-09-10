from pathlib import Path
import unittest

from models.components import (
    AbilityScoreChoice,
    ClassProgression,
    EffectResult,
    SpellChoice,
    SpellFilter,
    SpellGrant,
    SpellSlot,
    WeaponProficiency,
)
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_ROOT = PROJECT_ROOT / "schemas"
COMPONENT_ROOT = SCHEMA_ROOT / "components"


class TestComponentModels(unittest.TestCase):
    def assert_component_valid(self, model, schema_name):
        data = model.model_dump(mode="json", by_alias=True, exclude_none=True)
        self.assertTrue(validate(COMPONENT_ROOT / schema_name, data, SCHEMA_ROOT))

    def test_ability_score_choice(self):
        self.assert_component_valid(
            AbilityScoreChoice(
                abilities=["strength", "dexterity"],
                choice_count=1,
                amount=2,
            ),
            "ability_score_choice.schema.json",
        )

    def test_class_progression(self):
        self.assert_component_valid(
            ClassProgression(name="fighter", subclass="champion", level=5),
            "class_progression.schema.json",
        )

    def test_effect_result(self):
        self.assert_component_valid(
            EffectResult(description="The target is pushed 10 feet."),
            "effect_result.schema.json",
        )

    def test_spell_choice_and_grant(self):
        choice = SpellChoice(
            filter=SpellFilter(classes=["wizard"], levels=[1]),
            casting_ability="intelligence",
            uses=1,
            recharge="long_rest",
        )
        self.assert_component_valid(choice, "spell_choice.schema.json")
        self.assert_component_valid(
            SpellGrant(choices=[choice], casting_ability="intelligence"),
            "spell_grant.schema.json",
        )
        self.assert_component_valid(
            SpellGrant(spells=["misty step"]),
            "spell_grant.schema.json",
        )

    def test_spell_slot(self):
        self.assert_component_valid(
            SpellSlot(level=3, maximum=2, current=1, recharge="long_rest"),
            "spell_slot.schema.json",
        )

    def test_weapon_proficiency(self):
        data = WeaponProficiency.model_validate("martial").model_dump(mode="json")
        self.assertTrue(
            validate(
                COMPONENT_ROOT / "weapon_proficiency.schema.json",
                data,
                SCHEMA_ROOT,
            )
        )


if __name__ == "__main__":
    unittest.main()
