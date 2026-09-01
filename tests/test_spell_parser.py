from pathlib import Path
import json
import unittest

# from parsers.spell_adaptor import SpellAdaptor
from parsers.spell_parser import parse_spell
from parsers.xml_parser import parse_xml
# from models.spell import Spell
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files" / "spells"
RESULTS_ROOT = DATA_ROOT / "results"
ADAPTED_RESULTS_ROOT = DATA_ROOT / "adapted_results"


class TestSpellParser(unittest.TestCase):
    def test_parse_spell_xml(self):
        for xml_path in DATA_ROOT.glob("*.xml"):
            with self.subTest(xml=xml_path.name):
                parsed_xml = parse_xml(xml_path)
                spell = parse_spell(parsed_xml)
                # adapted_spell = SpellAdaptor().adapt(spell)

                self.assertIsInstance(spell, dict)
                result_path = RESULTS_ROOT / f"{xml_path.stem}.json"
                RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
                result_path.write_text(
                    json.dumps(parsed_xml, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )
                # self.assertIsInstance(adapted_spell, dict)
                
                
    # def test_parse_items(self):
    #     for xml_path in DATA_ROOT.glob("*.xml"):
    #         with self.subTest(xml=xml_path.name):
    #             parsed_xml = parse_xml(xml_path)
    #             spell = parse_spell(parsed_xml)
    #             adapted_spell = SpellAdaptor().adapt(spell)

    #             self.assertIsInstance(item, dict)
    #             self.assertEqual(adapted_item["category"], "wand")
    #             self.assertEqual(item["name"], "Wand of Orcus")
    #             self.assertEqual(item["type"], "WD")
    #             self.assertEqual(item["magic"], "1")
    #             self.assertEqual(item["detail"], "artifact (requires attunement)")
    #             self.assertEqual(item["weight"], "4")
    #             self.assertEqual(len(item["text"]), 31)
    #             self.assertIsNone(item["text"][4])
    #             self.assertEqual(
    #                 item["text"][-3],
    #                 "Bathing the wand in positive energy causes it to crack and explode, but unless the above conditions are met, the wand instantly reforms on Orcus's layer of the Abyss.",
    #             )
    #             self.assertEqual(
    #                 item["text"][-1],
    #                 "Source: Dungeon Master's Guide p. 227",
    #             )
    #             self.assertEqual(len(item["modifiers"]), 3)
    #             self.assertEqual(item["modifiers"][0]["category"], "bonus")
    #             self.assertEqual(
    #                 item["modifiers"][0]["text"],
    #                 "melee attacks +3",
    #             )

    #             result_path = RESULTS_ROOT / f"{xml_path.stem}.json"
    #             RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    #             result_path.write_text(
    #                 json.dumps(item, indent=4, ensure_ascii=False),
    #                 encoding="utf-8",
    #             )

    #             adapted_path = DATA_ROOT / "adapted_results" / f"{xml_path.stem}.json"
    #             adapted_path.parent.mkdir(parents=True, exist_ok=True)
    #             adapted_path.write_text(
    #                 json.dumps(adapted_item, indent=4, ensure_ascii=False),
    #                 encoding="utf-8",
    #             )

    #             validated_item = Item.model_validate(adapted_item)
    #             self.assertEqual(validated_item.name, "Wand of Orcus")

    # def test_item_models_round_trip(self):
    #     for path in sorted(
    #         (PROJECT_ROOT / "tests" / "data" / "schemas" / "entities" / "items").glob("*.json")
    #     ):
    #         with self.subTest(item=path.name):
    #             item = Item.model_validate(
    #                 json.loads(path.read_text(encoding="utf-8"))
    #             )

    #             validate(
    #                 PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
    #                 item.model_dump(mode="json", exclude_none=True),
    #                 PROJECT_ROOT / "schemas",
    #             )