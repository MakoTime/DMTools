from pathlib import Path
import json
import unittest

from parsers.spell_adaptor import SpellAdaptor
from parsers.spell_parser import parse_spell
from parsers.xml_parser import parse_xml
from models.spell import Spell
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

                self.assertEqual(spell["name"], "Prismatic Spray")
                self.assertEqual(spell["level"], "7")
                self.assertEqual(spell["school"], "EV")
                self.assertEqual(spell["ritual"], "NO")
                self.assertEqual(spell["time"], "1 action")
                self.assertEqual(spell["range"], "Self (60 foot cone)")
                self.assertEqual(spell["components"], "V, S")
                self.assertEqual(spell["duration"], "Instantaneous")
                self.assertEqual(spell["classes"], "Sorcerer, Wizard, Bard")
                self.assertEqual(len(spell["text"]), 36)
                self.assertEqual(spell["roll"], ["1d8", "10d6"])

    def test_parse_source_spell_with_roll_and_optional_fields(self):
        source_spell = next(
            child
            for child in parse_xml(PROJECT_ROOT / "5eFile.xml")["children"]
            if child["tag"] == "spell"
            and next(
                value["text"]
                for value in child["children"]
                if value["tag"] == "name"
            ) == "Cure Wounds"
        )

        spell = parse_spell(source_spell)

        self.assertEqual(spell["name"], "Cure Wounds")
        self.assertEqual(spell["level"], "1")
        self.assertEqual(spell["school"], "EV")
        self.assertEqual(spell["ritual"], "NO")
        self.assertEqual(spell["classes"], "Bard, Cleric, Druid, Paladin, Ranger, Warlock (Celestial), Artificer")
        self.assertEqual(len(spell["text"]), 5)
        self.assertEqual(spell["roll"], ["1d8+SPELL"])

    def test_adapt_basic_source_spell(self):
        source_spell = next(
            child
            for child in parse_xml(PROJECT_ROOT / "5eFile.xml")["children"]
            if child["tag"] == "spell"
            and next(
                value["text"]
                for value in child["children"]
                if value["tag"] == "name"
            ) == "Cure Wounds"
        )

        adapted_spell = SpellAdaptor().adapt(parse_spell(source_spell))

        self.assertEqual(adapted_spell["level"], 1)
        self.assertEqual(adapted_spell["school"], "evocation")
        self.assertEqual(
            adapted_spell["casting_time"],
            {"amount": 1, "unit": "action"},
        )
        self.assertEqual(adapted_spell["target"], {"targeting": "touch"})
        self.assertEqual(adapted_spell["components"], ["verbal", "somatic"])
        self.assertEqual(
            adapted_spell["duration"],
            {"duration": "instantaneous"},
        )
        self.assertFalse(adapted_spell["concentration"])
        self.assertEqual(
            adapted_spell["source"],
            {"text": "Player's Handbook p. 230"},
        )
        self.assertNotIn("range", adapted_spell)
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Spell.schema.json",
                adapted_spell,
                PROJECT_ROOT / "schemas",
            )
        )

    def test_adapt_mile_range(self):
        adapted_spell = SpellAdaptor().adapt(
            {"name": "Far Sight", "range": "500 miles"}
        )

        self.assertEqual(
            adapted_spell["target"],
            {
                "targeting": "range",
                "range": {"amount": 500, "unit": "miles"},
            },
        )
        spell = Spell.model_validate(
            {
                "name": "Far Sight",
                "level": 1,
                "description": "A spell with a mile-based range.",
                "casting_time": {"unit": "action"},
                "components": ["verbal"],
                "duration": {"duration": "instantaneous"},
                **adapted_spell,
            }
        )
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Spell.schema.json",
                spell.model_dump(mode="json", exclude_none=True),
                PROJECT_ROOT / "schemas",
            )
        )

    def test_adapt_non_distance_target_modes(self):
        for source_range in ("Special", "Sight", "Unlimited"):
            with self.subTest(source_range=source_range):
                adapted_spell = SpellAdaptor().adapt(
                    {"name": "Target Mode", "range": source_range}
                )
                self.assertEqual(
                    adapted_spell["target"],
                    {"targeting": source_range.lower()},
                )

    def test_adapt_multiple_and_descriptive_reaction_casting_times(self):
        adaptor = SpellAdaptor()

        self.assertEqual(
            adaptor.casting_time("1 action or 8 hours"),
            [
                {"amount": 1, "unit": "action"},
                {"amount": 8, "unit": "hour"},
            ],
        )
        self.assertEqual(
            adaptor.casting_time(
                "1 reaction, which you take when you speak to another creature"
            ),
            {"amount": 1, "unit": "reaction"},
        )
        self.assertEqual(
            adaptor.casting_time(
                "1 reaction, which you take when you take acid, cold, fire, lightning, or thunder damage"
            ),
            {"amount": 1, "unit": "reaction"},
        )

    def test_adapt_prismatic_spray_roll_table(self):
        adapted_spell = SpellAdaptor().adapt(
            parse_spell(parse_xml(DATA_ROOT / "prismatic_spray.xml"))
        )

        roll_table = adapted_spell["roll_table"]
        self.assertEqual(roll_table["dice"], 8)
        self.assertEqual(len(roll_table["entries"]), 8)
        self.assertEqual(roll_table["entries"][0]["result"], "Red")
        self.assertEqual(
            roll_table["entries"][0]["effects"][0]["attack_save"]["ability"],
            "dexterity",
        )
        self.assertEqual(
            roll_table["entries"][0]["effects"][0]["attack_save"]["failure"][0]["damage"]["type"],
            "fire",
        )
        self.assertEqual(
            roll_table["entries"][5]["effects"][0]["attack_save"]["failure"][0],
            {"condition": "restrained"},
        )
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Spell.schema.json",
                adapted_spell,
                PROJECT_ROOT / "schemas",
            )
        )

    def test_adapt_common_damage_spells_to_structured_effects(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        adaptor = SpellAdaptor()

        def adapted(name):
            source = next(
                child for child in root["children"]
                if child["tag"] == "spell"
                and next(value["text"] for value in child["children"] if value["tag"] == "name") == name
            )
            return adaptor.adapt(parse_spell(source))

        lightning_bolt = adapted("Lightning Bolt")
        lightning_effect = lightning_bolt["effects"][0]["attack_save"]
        self.assertEqual(lightning_effect["ability"], "dexterity")
        self.assertEqual(lightning_effect["failure"][0]["damage"]["type"], "lightning")
        self.assertEqual(lightning_effect["failure"][0]["damage"]["roll"]["count"], 8)
        self.assertEqual(lightning_effect["failure"][0]["damage"]["roll"]["dice"], 6)
        self.assertEqual(lightning_effect["success"][0]["description"], "(Halved)")

        ice_storm = adapted("Ice Storm")
        ice_effect = ice_storm["effects"][0]["attack_save"]
        self.assertEqual(
            [item["damage"]["type"] for item in ice_effect["failure"]],
            ["bludgeoning", "cold"],
        )

        for spell_data in (lightning_bolt, ice_storm):
            Spell.model_validate(spell_data)
            self.assertTrue(validate(
                PROJECT_ROOT / "schemas" / "entities" / "Spell.schema.json",
                spell_data,
                PROJECT_ROOT / "schemas",
            ))

    def test_spell_models_round_trip_source_representatives(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        for name in {"Cure Wounds", "Prismatic Spray"}:
            with self.subTest(spell=name):
                source_spell = next(
                    child
                    for child in root["children"]
                    if child["tag"] == "spell"
                    and next(
                        value["text"]
                        for value in child["children"]
                        if value["tag"] == "name"
                    ) == name
                )
                adapted_spell = SpellAdaptor().adapt(
                    parse_spell(source_spell)
                )
                spell = Spell.model_validate(adapted_spell)
                validate(
                    PROJECT_ROOT / "schemas" / "entities" / "Spell.schema.json",
                    spell.model_dump(mode="json", exclude_none=True),
                    PROJECT_ROOT / "schemas",
                )
                
                
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