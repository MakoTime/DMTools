from pathlib import Path
import unittest
import json

from xml_importer import XMLImporter
from parsers.xml_parser import parse_xml, get_text, find_child, find_children


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files"
RESULTS_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files" / "results"


class TestXMLParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml_importer = XMLImporter(DATA_ROOT)

    def test_xml(self):
        for xml_path in self.xml_importer.iter_tests():
            with self.subTest(xml=xml_path.name):
                parsed = parse_xml(xml_path)

                self.assertIsInstance(parsed, dict)
                self.assertIn("tag", parsed)
                self.assertIn("attributes", parsed)
                self.assertIn("text", parsed)
                self.assertIn("children", parsed)

    def test_find_child(self):
        element = {
            "tag": "monster",
            "attributes": {},
            "text": None,
            "children": [
                {
                    "tag": "size",
                    "attributes": {},
                    "text": "L",
                    "children": [],
                },
            ],
        }

        child = find_child(element, "size")

        self.assertIsNotNone(child)
        self.assertEqual(child["text"], "L")

    def test_find_children(self):
        element = {
            "tag": "monster",
            "attributes": {},
            "text": None,
            "children": [
                {"tag": "trait", "attributes": {}, "text": None, "children": []},
                {"tag": "trait", "attributes": {}, "text": None, "children": []},
                {"tag": "action", "attributes": {}, "text": None, "children": []},
            ],
        }

        traits = find_children(element, "trait")

        self.assertEqual(len(traits), 2)

    def test_get_text(self):
        element = {
            "tag": "monster",
            "attributes": {},
            "text": None,
            "children": [
                {
                    "tag": "size",
                    "attributes": {},
                    "text": "L",
                    "children": [],
                },
            ],
        }

        self.assertEqual(get_text(element, "size"), "L")
        self.assertIsNone(get_text(element, "missing"))


if __name__ == "__main__":
    unittest.main()