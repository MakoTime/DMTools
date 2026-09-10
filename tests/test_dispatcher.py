import unittest

from parsers.dispatcher import dispatch_root
from parsers.xml_parser import parse_xml


class TestDispatcher(unittest.TestCase):
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

    def test_dispatch_root_reports_record_failures_without_aborting(self):
        root = parse_xml(
            """
            <compendium>
                <spell><name>Broken Spell</name><level>not-a-level</level></spell>
                <race><name>Custom Lineage</name><size>M</size><speed>30</speed></race>
            </compendium>
            """
        )

        results = dispatch_root(root)

        self.assertEqual(results[0]["status"], "failed")
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