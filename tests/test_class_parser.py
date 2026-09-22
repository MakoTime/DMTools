from pathlib import Path
import unittest

from models.class_model import Class
from parsers.class_adaptor import ClassAdaptor
from parsers.class_parser import parse_class
from parsers.xml_parser import parse_xml
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestClassParser(unittest.TestCase):
    def source_class(self, name: str):
        root = parse_xml(PROJECT_ROOT / "5eFile.xml")
        element = next(
            element for element in root["children"]
            if element["tag"] == "class"
            and next(child["text"] for child in element["children"] if child["tag"] == "name") == name
        )
        return parse_class(element)

    def test_parse_preserves_base_fields(self):
        source = self.source_class("Barbarian")
        self.assertEqual(source["hd"], "12")
        self.assertEqual(source["numSkills"], "2")
        self.assertEqual(source["armor"], "light armor, medium armor, shields")
        self.assertTrue(source["autolevels"])
        self.assertEqual(source["autolevels"][0]["attributes"]["level"], "1")

    def test_adapt_barbarian_and_cleric(self):
        barbarian = ClassAdaptor().adapt(self.source_class("Barbarian"))
        cleric = ClassAdaptor().adapt(self.source_class("Cleric"))

        self.assertEqual(barbarian["name"], "barbarian")
        self.assertEqual(barbarian["hit_dice"], 12)
        self.assertEqual(barbarian["skill_choices"], {
            "choose": 2,
            "from": ["animal_handling", "athletics", "intimidation", "nature", "perception", "survival"],
        })
        self.assertEqual(cleric["spellcasting"], {"ability": "wisdom", "progression": "full"})
        self.assertTrue(barbarian["features"])
        self.assertTrue(all("level" in feature for feature in barbarian["features"]))
        for class_data in (barbarian, cleric):
            Class.model_validate(class_data)
            self.assertTrue(validate(
                PROJECT_ROOT / "schemas" / "entities" / "Class.schema.json",
                class_data,
                PROJECT_ROOT / "schemas",
            ))

            self.assertIn("Starting Barbarian", barbarian.get("description", ""))
            self.assertNotIn("Path of the Berserker", barbarian.get("description", ""))

    def test_class_schema_uses_editor_friendly_progression_shapes(self):
        class_data = {
            "name": "Test Class",
            "hit_dice": 8,
            "required_stats": ["strength", "constitution"],
            "starting_class": "You can start as a member of this class.",
            "multiclassing": "You need Strength 13 to multiclass into this class.",
            "ability_score_increase": [4, 8, 12, 16, 19],
        }

        Class.model_validate(class_data)
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Class.schema.json",
                class_data,
                PROJECT_ROOT / "schemas",
            )
        )

    def test_parse_preserves_progression_metadata(self):
        source = self.source_class("Wizard")
        score_levels = [
            level for level in source["autolevels"]
            if level["attributes"].get("scoreImprovement") == "YES"
        ]
        self.assertTrue(score_levels)
        self.assertTrue(any(
            child["tag"] == "slots"
            for level in source["autolevels"]
            for child in level["children"]
        ))

    def test_extracts_bard_subclasses_from_optional_features(self):
        subclasses = ClassAdaptor().subclasses(self.source_class("Bard"))
        by_name = {value["name"]: value for value in subclasses}

        self.assertIn("College of Lore", by_name)
        self.assertTrue(any(
            feature["name"] == "Cutting Words (College of Lore)"
            for feature in by_name["College of Lore"]["features"]
        ))
        bard = ClassAdaptor().adapt(self.source_class("Bard"))
        self.assertIn("Starting Bard", bard.get("description", ""))
        self.assertNotIn("Cutting Words (College of Lore)", bard.get("description", ""))
        self.assertNotIn("Cutting Words (College of Lore)", {
            feature["name"] for feature in bard["features"]
        })

    def test_registers_subclass_feature_levels_for_class_presentation(self):
        progression = ClassAdaptor().subclass_progression(self.source_class("Bard"))

        self.assertIn(
            {
                "subclass": "College of Lore",
                "level": 3,
                "feature": "Cutting Words (College of Lore)",
            },
            progression,
        )

        self.assertEqual(
            ClassAdaptor().subclass_feature_levels(self.source_class("Bard")),
            [3, 6, 14],
        )

    def test_cantrip_progression_ignores_empty_text_nodes(self):
        source = {
            "autolevels": [{
                "attributes": {"level": 1},
                "children": [{
                    "tag": "feature",
                    "children": [
                        {"tag": "name", "text": "Spellcasting"},
                        {"tag": "text", "text": None},
                        {
                            "tag": "text",
                            "text": "At 1st level, you know three cantrips. "
                            "You learn an additional cantrip at 4th level.",
                        },
                    ],
                }],
            }],
        }

        result = ClassAdaptor().cantrips_known(source)

        self.assertEqual(result["1"], 3)
        self.assertEqual(result["4"], 4)

    def test_extracts_bard_cantrip_progression_from_source_text(self):
        result = ClassAdaptor().cantrips_known(self.source_class("Bard"))

        self.assertEqual(result["1"], 2)
        self.assertEqual(result["3"], 2)
        self.assertEqual(result["4"], 3)
        self.assertEqual(result["9"], 3)
        self.assertEqual(result["10"], 4)

    def test_does_not_cross_assign_similarly_named_subclasses(self):
        subclasses = ClassAdaptor().subclasses(self.source_class("Rogue"))
        by_name = {value["name"]: value for value in subclasses}

        self.assertNotIn("Spell Thief (Arcane Trickster)", {
            feature["name"]
            for feature in by_name["Thief"]["features"]
        })

    def test_paladin_subclass_features_are_not_class_features(self):
        source = self.source_class("Paladin")
        adaptor = ClassAdaptor()

        class_feature_names = {feature["name"] for feature in adaptor.adapt(source)["features"]}
        subclasses = {subclass["name"]: subclass for subclass in adaptor.subclasses(source)}

        self.assertNotIn("Channel Divinity: Peerless Athlete (Oath of Glory)", class_feature_names)
        self.assertNotIn("Channel Divinity: Watcher's Will (Oath of the Watchers)", class_feature_names)
        self.assertIn(
            "Channel Divinity: Peerless Athlete (Oath of Glory)",
            {feature["name"] for feature in subclasses["Oath of Glory"]["features"]},
        )
        self.assertIn(
            "Channel Divinity: Watcher's Will (Oath of the Watchers)",
            {feature["name"] for feature in subclasses["Oath of the Watchers"]["features"]},
        )

    def test_replacement_features_remain_class_features(self):
        source = self.source_class("Cleric")
        adaptor = ClassAdaptor()

        class_features = adaptor.adapt(source)["features"]
        subclasses = adaptor.subclasses(source)

        self.assertIn(
            "Blessed Strikes (replaces the Divine Strike or Potent Spellcasting feature)",
            {feature["name"] for feature in class_features},
        )
        self.assertNotIn(
            "Blessed Strikes (replaces the Divine Strike or Potent Spellcasting feature)",
            {
                feature["name"]
                for subclass in subclasses
                for feature in subclass["features"]
            },
        )

    def test_class_features_preserve_structured_effects_when_supported(self):
        source = {
            "name": "Test Class",
            "autolevels": [{
                "attributes": {"level": "3"},
                "children": [{
                    "tag": "feature",
                    "attributes": {"optional": "YES"},
                    "children": [
                        {"tag": "name", "text": "Arcane Strike"},
                        {"tag": "text", "text": "The target takes 2d6 fire damage."},
                    ],
                }],
            }],
        }

        feature = ClassAdaptor().feature(source["autolevels"][0]["children"][0], 3)
        self.assertEqual(feature["effects"][0]["damage"]["type"], "fire")