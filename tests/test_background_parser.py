from pathlib import Path
import unittest

from models.background import Background
from parsers.background_adaptor import BackgroundAdaptor
from parsers.background_parser import parse_background
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestBackgroundParser(unittest.TestCase):
    def source_background(self, name: str):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        element = next(
            element for element in root["children"]
            if element["tag"] == "background"
            and next(child["text"] for child in element["children"] if child["tag"] == "name") == name
        )
        return parse_background(element)

    def test_parse_preserves_traits(self):
        source = parse_background(parse_xml(
            """
            <background>
                <name>Acolyte</name>
                <proficiency>Insight, Religion</proficiency>
                <trait><name>Feature: Shelter</name><text>Care and healing.</text></trait>
            </background>
            """
        ))
        self.assertEqual(source["proficiency"], "Insight, Religion")
        self.assertEqual(source["traits"][0]["name"], "Feature: Shelter")

    def test_adapt_acolyte_and_charlatan(self):
        acolyte = BackgroundAdaptor().adapt(self.source_background("Acolyte"))
        charlatan = BackgroundAdaptor().adapt(self.source_background("Charlatan"))

        self.assertEqual(acolyte["skill_proficiencies"], ["insight", "religion"])
        self.assertEqual(charlatan["skill_proficiencies"], ["deception", "sleight_of_hand"])
        self.assertEqual(charlatan["tool_proficiencies"], ["disguise_kit", "forgery_kit"])
        self.assertEqual(acolyte["features"][0]["name"], "Shelter of the Faithful")
        for background in (acolyte, charlatan):
            Background.model_validate(background)
            self.assertTrue(validate(
                PROJECT_ROOT / "schemas" / "entities" / "Background.schema.json",
                background,
                PROJECT_ROOT / "schemas",
            ))