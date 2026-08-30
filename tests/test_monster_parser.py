from pathlib import Path
import json
import unittest

from models.components import Action
from models.monster import Monster
from parsers.monster_adaptor import MonsterAdaptor
from parsers.monster_parser import parse_monster
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files" / "monsters"
RESULTS_ROOT = DATA_ROOT / "results"
ADAPTED_RESULTS_ROOT = DATA_ROOT / "adapted_results"


class TestMonsterParser(unittest.TestCase):
    def test_parse_monsters(self):
        RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
        ADAPTED_RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

        for xml_path in DATA_ROOT.glob("*.xml"):
            with self.subTest(xml=xml_path.name):
                parsed_xml = parse_xml(xml_path)
                monster = parse_monster(parsed_xml)

                self.assertIsInstance(monster, dict)

                result_path = RESULTS_ROOT / f"{xml_path.stem}.json"
                result_path.write_text(
                    json.dumps(monster, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )

                adapted_monster = MonsterAdaptor().adapt(monster)
                self.assertIsInstance(adapted_monster, dict)

                result_path = ADAPTED_RESULTS_ROOT / f"{xml_path.stem}.json"
                result_path.write_text(
                    json.dumps(adapted_monster, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )


class TestModel(unittest.TestCase):
    def load_beholder(self):
        return json.loads(
            (ADAPTED_RESULTS_ROOT / "beholder.json").read_text(
                encoding="utf-8"
            )
        )

    def test_actions_model(self):
        actions_input = self.load_beholder()["actions"]

        actions = [Action.model_validate(data) for data in actions_input]

        self.assertEqual([action.name for action in actions], ["Bite", "Eye Rays"])
        self.assertEqual(actions[0].description, actions_input[0]["description"])
        self.assertEqual(actions[1].description, actions_input[1]["description"])
        self.assertEqual(actions[0].target.range.amount, 5)
        self.assertEqual(actions[0].target.count.maximum, 1)
        self.assertEqual(actions[0].effects[0].attack_hit.bonus, 5)
        self.assertEqual(
            actions[0].effects[0].attack_hit.effects[0].damage.type,
            "piercing",
        )

    def test_monster_model_round_trip_is_schema_valid(self):
        monster_input = self.load_beholder()

        monster = Monster.model_validate(monster_input)

        self.assertEqual(monster.name, "Beholder")
        self.assertEqual(monster.ability_scores.wisdom, 15)
        self.assertEqual(monster.armor_class.value, 18)
        self.assertEqual(monster.movement[1].speed.distance, 20)
        self.assertEqual(monster.legendary_actions[1].name, "Eye Ray")
        self.assertEqual(monster.challenge_rating, 13)

        validate(
            PROJECT_ROOT / "schemas" / "entities" / "Creature.schema.json",
            monster.model_dump(mode="json", exclude_none=True),
            PROJECT_ROOT / "schemas",
        )

    def test_all_adapted_monsters_construct(self):
        for path in sorted(ADAPTED_RESULTS_ROOT.glob("*.json")):
            with self.subTest(monster=path.name):
                monster = Monster.model_validate(
                    json.loads(path.read_text(encoding="utf-8"))
                )

                self.assertTrue(monster.name)
                self.assertIsNotNone(monster.challenge_rating)

    def test_action_with_roll_table(self):
        action_input = self.load_beholder()["actions"][1].copy()

        action = Action.model_validate(action_input)

        self.assertIsNotNone(action.roll_table)
        self.assertEqual(action.roll_table.dice, 10)
        self.assertEqual(len(action.roll_table.entries), 10)
        self.assertEqual(action.roll_table.entries[0].result, "Charm Ray")
        self.assertEqual(action.roll_table.entries[-1].result, "Death Ray")
        self.assertIsNone(action.effects)
        self.assertEqual(action.target.range.amount, 120)
        self.assertEqual(action.target.count.minimum, 1)
        self.assertEqual(action.target.count.maximum, 3)
        self.assertEqual(
            action.roll_table.entries[0].effects[0].attack_save.ability,
            "wisdom",
        )
        self.assertEqual(
            action.roll_table.entries[0]
            .effects[0]
            .attack_save
            .failure[0]
            .condition,
            "charmed",
        )
        
        self.assertEqual(
            action.roll_table.entries[9]
            .effects[0]
            .attack_save
            .failure[0]
            .damage.roll.dice,
            10,
        )
        
        # type: DamageType
        #     roll: Roll
        #     modifier: int = 0
        #     ability: AbilityScore | None = None


if __name__ == "__main__":
    unittest.main()
