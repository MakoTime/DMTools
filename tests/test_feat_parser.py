from pathlib import Path
import unittest

from models.feat import Feat
from parsers.feat_adaptor import FeatAdaptor
from parsers.feat_parser import parse_feat
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFeatParser(unittest.TestCase):
    def test_parse_preserves_modifier_and_text(self):
        source = parse_feat(parse_xml(
            """
            <feat>
                <name>Actor</name>
                <prerequisite />
                <text>Benefit one.</text>
                <text />
                <modifier category="ability score">charisma +1</modifier>
            </feat>
            """
        ))
        self.assertEqual(source["text"], ["Benefit one.", None])
        self.assertEqual(source["modifiers"][0]["category"], "ability score")

    def test_adapt_fey_touched(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        element = next(
            element for element in root["children"]
            if element["tag"] == "feat"
            and next(child["text"] for child in element["children"] if child["tag"] == "name") == "Fey Touched (Intelligence)"
        )
        feat = FeatAdaptor().adapt(parse_feat(element))

        self.assertEqual(feat["name"], "Fey Touched (Intelligence)")
        self.assertEqual(feat["ability_score_increases"], [{"ability": "intelligence", "amount": 1}])
        self.assertEqual(feat["spell_grants"][0]["spells"], ["misty step"])
        self.assertEqual(feat["spell_grants"][1]["choices"][0]["filter"], {
            "schools": ["divination", "enchantment"],
            "levels": [1],
        })
        Feat.model_validate(feat)
        self.assertTrue(validate(
            PROJECT_ROOT / "schemas" / "entities" / "Feat.schema.json",
            feat,
            PROJECT_ROOT / "schemas",
        ))

    def test_adapt_resilient_preserves_saving_throw_proficiency(self):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        element = next(
            element for element in root["children"]
            if element["tag"] == "feat"
            and next(child["text"] for child in element["children"] if child["tag"] == "name") == "Resilient (Constitution)"
        )
        source = parse_feat(element)
        feat = FeatAdaptor().adapt(source)

        self.assertEqual(feat["name"], "Resilient (Constitution)")
        self.assertEqual(feat["ability_score_increases"], [{"ability": "constitution", "amount": 1}])
        self.assertIn("proficiency", feat["description"].lower())
        Feat.model_validate(feat)
        self.assertTrue(validate(
            PROJECT_ROOT / "schemas" / "entities" / "Feat.schema.json",
            feat,
            PROJECT_ROOT / "schemas",
        ))