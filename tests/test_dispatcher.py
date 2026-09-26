from pathlib import Path
import unittest

from models.class_model import Class
from models.monster import Monster
from parsers.dispatcher import dispatch_root
from parsers.xml_parser import parse_xml


class TestDispatcher(unittest.TestCase):
    def test_raw_xml_monster_spellcasting_reaches_pydantic_model(self):
        fixture = Path(__file__).parent / "data" / "xml_files" / "monsters" / "failed_spellcasters.xml"
        root = parse_xml(fixture)

        results = dispatch_root(root)

        self.assertEqual([result["name"] for result in results], ["Acolyte", "Archmage"])
        self.assertTrue(all(result["status"] == "success" for result in results))
        acolyte = Monster.model_validate(results[0]["data"])
        archmage = Monster.model_validate(results[1]["data"])
        self.assertEqual(
            acolyte.spell_casting.spells_known.level_1.spells,
            ["bless", "cure wounds", "sanctuary"],
        )
        self.assertEqual(
            acolyte.spell_casting.spells_known.cantrips,
            ["light", "sacred flame", "thaumaturgy"],
        )
        self.assertEqual(
            archmage.spell_casting.spells_known.level_9.spells,
            ["time stop"],
        )

    def test_raw_xml_class_reaches_pydantic_model_and_preserves_cantrip_metadata(self):
        root = parse_xml("""
            <compendium>
                <class>
                    <name>Wizard</name><hd>6</hd>
                    <proficiency>Intelligence, Arcana, History</proficiency>
                    <spellAbility>Intelligence</spellAbility><numSkills>2</numSkills>
                    <armor>none</armor><weapons>daggers</weapons><tools>none</tools>
                    <autolevel level="1">
                        <feature>
                            <name>Spellcasting</name><text/>
                            <text>At 1st level, you know three cantrips. You learn an additional cantrip at 4th level and another at 10th level.</text>
                        </feature>
                    </autolevel>
                </class>
            </compendium>
        """)

        result = dispatch_root(root)[0]

        self.assertEqual(result["status"], "success")
        Class.model_validate(result["data"])
        self.assertEqual(
            result["source_metadata"]["presentation_progression"]["cantrips_known"]["1"],
            3,
        )
        self.assertEqual(
            result["source_metadata"]["presentation_progression"]["cantrips_known"]["10"],
            5,
        )

    def test_dispatches_supported_entities_and_reports_unsupported(self):
        root = parse_xml(
            """
            <compendium>
                <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
                <race><name>Custom Lineage</name><size>M</size><speed>30</speed></race>
                <unknown><name>Future Entity</name></unknown>
            </compendium>
            """
        )

        results = dispatch_root(root)

        self.assertEqual([result["status"] for result in results], ["success", "success", "unsupported"])
        self.assertEqual(results[0]["data"]["name"], "Backpack")
        self.assertEqual(results[1]["data"]["name"], "Custom Lineage")
        self.assertEqual(results[2]["name"], "Future Entity")

    def test_dispatch_root_preserves_records_for_shared_validation(self):
        root = parse_xml(
            """
            <compendium>
                <spell><name>Broken Spell</name><level>not-a-level</level></spell>
                <race><name>Custom Lineage</name><size>M</size><speed>30</speed></race>
            </compendium>
            """
        )

        results = dispatch_root(root)

        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["data"]["name"], "Broken Spell")
        self.assertEqual(results[1]["status"], "success")

    def test_dispatches_subclasses_from_class_features(self):
        root = parse_xml("""
            <compendium>
                <class>
                    <name>Bard</name><hd>8</hd>
                    <autolevel level="3">
                        <feature optional="YES">
                            <name>Bard College: College of Lore</name>
                            <text>College description.</text>
                            <text>Source: Test</text>
                        </feature>
                        <feature optional="YES">
                            <name>Cutting Words (College of Lore)</name>
                            <text>Feature description.</text>
                        </feature>
                    </autolevel>
                </class>
            </compendium>
        """)

        results = dispatch_root(root)
        subclasses = [result for result in results if result["tag"] == "subclass"]

        self.assertEqual(len(subclasses), 1)
        self.assertEqual(subclasses[0]["status"], "success")
        self.assertEqual(subclasses[0]["data"]["class"], "bard")
        self.assertEqual(len(subclasses[0]["data"]["features"]), 2)
        class_record = next(result for result in results if result["tag"] == "class")
        self.assertNotIn("features", class_record["data"])
        self.assertNotIn("Spellcasting", str(class_record["data"]))