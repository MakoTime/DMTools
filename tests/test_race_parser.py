from pathlib import Path
import unittest

from models.race import Race
from parsers.race_adaptor import RaceAdaptor
from parsers.race_parser import parse_race
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestRaceParser(unittest.TestCase):
    def source_races(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        names = {"Dragonborn (Black)", "Custom Lineage"}
        return {
            next(child["text"] for child in element["children"] if child["tag"] == "name"): parse_race(element)
            for element in root["children"]
            if element["tag"] == "race"
            and next((child.get("text") for child in element["children"] if child["tag"] == "name"), None) in names
        }

    def test_parse_preserves_nested_trait_content(self):
        source = parse_race(parse_xml(
            """
            <race>
                <name>Warforged</name>
                <trait>
                    <name>Constructed Resilience</name>
                    <text>You have resistance to poison damage.</text>
                    <special>powerful build</special>
                    <modifier category="bonus">ac +1</modifier>
                </trait>
            </race>
            """
        ))
        self.assertEqual(source["traits"][0]["special"], ["powerful build"])
        self.assertEqual(source["traits"][0]["modifiers"][0]["category"], "bonus")

    def test_adapt_source_races(self):
        races = self.source_races()
        dragonborn = RaceAdaptor().adapt(races["Dragonborn (Black)"])
        custom = RaceAdaptor().adapt(races["Custom Lineage"])

        self.assertEqual(dragonborn["name"], "Dragonborn")
        self.assertEqual(dragonborn["subtype"], "Black")
        self.assertEqual(dragonborn["ability_score_increases"], [
            {"ability": "strength", "amount": 2},
            {"ability": "charisma", "amount": 1},
        ])
        self.assertEqual(custom["name"], "Custom Lineage")
        self.assertEqual(custom["size"], "medium")
        self.assertEqual(custom["movement"][0]["speed"], {"distance": 30, "unit": "feet"})

        for race in (dragonborn, custom):
            Race.model_validate(race)
            self.assertTrue(validate(
                PROJECT_ROOT / "schemas" / "entities" / "Race.schema.json",
                race,
                PROJECT_ROOT / "schemas",
            ))

    def test_adapt_high_elf_supported_choices(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        element = next(
            element for element in root["children"]
            if element["tag"] == "race"
            and next(child["text"] for child in element["children"] if child["tag"] == "name") == "Elf, High"
        )
        race = RaceAdaptor().adapt(parse_race(element))

        self.assertEqual(race["name"], "Elf")
        self.assertEqual(race["subtype"], "High")
        self.assertEqual(race["skill_proficiencies"], ["perception"])
        self.assertEqual(race["senses"], [{"type": "darkvision", "distance": 60, "distance_type": "feet"}])
        self.assertEqual(race["spell_grants"][0]["choices"][0]["casting_ability"], "intelligence")
        Race.model_validate(race)
        self.assertTrue(validate(
            PROJECT_ROOT / "schemas" / "entities" / "Race.schema.json",
            race,
            PROJECT_ROOT / "schemas",
        ))