from pathlib import Path
import unittest

from parsers.xml_parser import parse_xml, get_text, find_child, find_children


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files"


class TestXMLParser(unittest.TestCase):
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

    def test_find_child_missing(self):
        element = {
            "tag": "monster",
            "attributes": {},
            "text": None,
            "children": [],
        }

        self.assertIsNone(find_child(element, "size"))

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

    def test_find_children_missing(self):
        element = {
            "tag": "monster",
            "attributes": {},
            "text": None,
            "children": [],
        }

        self.assertEqual(find_children(element, "trait"), [])

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

    def test_parse_xml_string(self):
        parsed = parse_xml(
            """
            <monster>
                <name>Lich</name>
                <size>M</size>
            </monster>
            """
        )

        self.assertEqual(parsed["tag"], "monster")
        self.assertEqual(get_text(parsed, "name"), "Lich")
        self.assertEqual(get_text(parsed, "size"), "M")

    def test_parse_preserves_attributes_and_empty_elements(self):
        parsed = parse_xml(
            """
            <root type="creature" source="test">
                <empty />
                <value>Content</value>
            </root>
            """
        )

        self.assertEqual(parsed["attributes"], {"type": "creature", "source": "test"})
        self.assertIsNone(parsed["children"][0]["text"])
        self.assertEqual(parsed["children"][1]["text"], "Content")

    def test_parse_preserves_child_order_and_repeated_elements(self):
        parsed = parse_xml(
            """
            <root>
                <value>10</value>
                <value>20</value>
                <other>30</other>
            </root>
            """
        )

        self.assertEqual(
            [child["tag"] for child in parsed["children"]],
            ["value", "value", "other"],
        )
        self.assertEqual(
            [child["text"] for child in find_children(parsed, "value")],
            ["10", "20"],
        )

    def test_parse_preserves_nested_children_and_mixed_text(self):
        parsed = parse_xml(
            """
            <root>Text before <parent>Parent <child>Content</child> after</parent> Text after</root>
            """
        )

        parent = find_child(parsed, "parent")
        self.assertIsNotNone(parent)
        self.assertEqual(parsed["text"], "Text before")
        self.assertEqual(parsed["children"][-1]["tail"], "Text after")
        self.assertEqual(parent["text"], "Parent")
        self.assertEqual(parent["children"][0]["text"], "Content")
        self.assertEqual(parent["children"][0]["tail"], "after")

    def test_parse_xml_file(self):
        for xml_path in DATA_ROOT.glob("*.xml"):

            parsed = parse_xml(xml_path)

            self.assertIsInstance(parsed, dict)
            self.assertIn("tag", parsed)
            self.assertIn("attributes", parsed)
            self.assertIn("text", parsed)
            self.assertIn("children", parsed)


if __name__ == "__main__":
    unittest.main()

