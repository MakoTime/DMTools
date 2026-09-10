from pathlib import Path
import unittest

from models.ability import Ability
from parsers.ability_adaptor import AbilityAdaptor
from parsers.dispatcher import dispatch_root
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestAbilityParser(unittest.TestCase):
    def test_adapts_eldritch_invocation(self):
        adapted = AbilityAdaptor().adapt(
            {
                "name": "Invocation: Agonizing Blast",
                "level": "0",
                "classes": "Eldritch Invocations",
                "text": [
                    "Prerequisite: Eldritch Blast cantrip",
                    "When you cast eldritch blast, add your Charisma modifier.",
                    "Source: Player's Handbook p. 110",
                ],
            }
        )

        self.assertEqual(adapted["kind"], "eldritch_invocation")
        self.assertEqual(adapted["prerequisites"], ["Eldritch Blast cantrip"])
        self.assertTrue(self._validate(adapted))

    def test_dispatches_battle_master_record_as_ability(self):
        root = parse_xml(
            """
            <compendium>
                <spell>
                    <name>Precision Attack</name>
                    <level>1</level>
                    <classes>Fighter (Battle Master), Martial Adept</classes>
                    <text>You expend one superiority die.</text>
                    <text>Source: Player's Handbook p. 74</text>
                </spell>
            </compendium>
            """
        )

        result = dispatch_root(root)[0]

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tag"], "ability")
        self.assertEqual(result["data"]["kind"], "maneuver")
        self.assertTrue(self._validate(result["data"]))

    def _validate(self, value: dict) -> bool:
        ability = Ability.model_validate(value)
        return validate(
            PROJECT_ROOT / "schemas" / "entities" / "Ability.schema.json",
            ability.model_dump(mode="json", exclude_none=True),
            PROJECT_ROOT / "schemas",
        )


if __name__ == "__main__":
    unittest.main()