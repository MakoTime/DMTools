from pathlib import Path
import json
import unittest

from parsers.item_parser import parse_item
from parsers.item_adaptor import ItemAdaptor
from parsers.xml_parser import parse_xml
from models.item import Item
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "xml_files" / "items"
RESULTS_ROOT = DATA_ROOT / "results"
ADAPTED_RESULTS_ROOT = DATA_ROOT / "adapted_results"


class TestItemParser(unittest.TestCase):
    def test_parse_items(self):
        for xml_path in DATA_ROOT.glob("*.xml"):
            with self.subTest(xml=xml_path.name):
                parsed_xml = parse_xml(xml_path)
                item = parse_item(parsed_xml)
                adapted_item = ItemAdaptor().adapt(item)

                self.assertIsInstance(item, dict)
                self.assertEqual(adapted_item["category"], "wand")
                self.assertEqual(item["name"], "Wand of Orcus")
                self.assertEqual(item["type"], "WD")
                self.assertEqual(item["magic"], "1")
                self.assertEqual(item["detail"], "artifact (requires attunement)")
                self.assertEqual(item["weight"], "4")
                self.assertEqual(len(item["text"]), 31)
                self.assertIsNone(item["text"][4])
                self.assertEqual(
                    item["text"][-3],
                    "Bathing the wand in positive energy causes it to crack and explode, but unless the above conditions are met, the wand instantly reforms on Orcus's layer of the Abyss.",
                )
                self.assertEqual(
                    item["text"][-1],
                    "Source: Dungeon Master's Guide p. 227",
                )
                self.assertEqual(len(item["modifiers"]), 3)
                self.assertEqual(item["modifiers"][0]["category"], "bonus")
                self.assertEqual(
                    item["modifiers"][0]["text"],
                    "melee attacks +3",
                )

                result_path = RESULTS_ROOT / f"{xml_path.stem}.json"
                RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
                result_path.write_text(
                    json.dumps(item, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )

                adapted_path = DATA_ROOT / "adapted_results" / f"{xml_path.stem}.json"
                adapted_path.parent.mkdir(parents=True, exist_ok=True)
                adapted_path.write_text(
                    json.dumps(adapted_item, indent=4, ensure_ascii=False),
                    encoding="utf-8",
                )

                validated_item = Item.model_validate(adapted_item)
                self.assertEqual(validated_item.name, "Wand of Orcus")

    def test_item_models_round_trip(self):
        for path in sorted(
            (PROJECT_ROOT / "tests" / "data" / "schemas" / "entities" / "items").glob("*.json")
        ):
            with self.subTest(item=path.name):
                item = Item.model_validate(
                    json.loads(path.read_text(encoding="utf-8"))
                )

                validate(
                    PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                    item.model_dump(mode="json", exclude_none=True),
                    PROJECT_ROOT / "schemas",
                )

    def test_parse_preserves_category_fields_and_attributes(self):
        parsed_xml = parse_xml(
            """
            <item source="fixture">
                <name>Longsword</name>
                <type>W</type>
                <magic>1</magic>
                <detail>rare</detail>
                <weight>3</weight>
                <value>15</value>
                <ac>18</ac>
                <dmg1>1d8</dmg1>
                <dmg2>1d10</dmg2>
                <dmgType>slashing</dmgType>
                <range>5/20</range>
                <property>versatile</property>
                <property>heavy</property>
                <stealth>disadvantage</stealth>
                <strength>15</strength>
                <text>Description</text>
                <text />
                <roll>1d8</roll>
                <modifier category="bonus" source="test">attack +1</modifier>
            </item>
            """
        )

        item = parse_item(parsed_xml)

        self.assertEqual(item["attributes"], {"source": "fixture"})
        self.assertEqual(item["value"], "15")
        self.assertEqual(item["ac"], "18")
        self.assertEqual(item["dmg1"], "1d8")
        self.assertEqual(item["dmg2"], "1d10")
        self.assertEqual(item["dmgType"], "slashing")
        self.assertEqual(item["range"], "5/20")
        self.assertEqual(item["property"], ["versatile", "heavy"])
        self.assertEqual(item["stealth"], "disadvantage")
        self.assertEqual(item["strength"], "15")
        self.assertEqual(item["text"], ["Description", None])
        self.assertEqual(item["roll"], ["1d8"])
        self.assertEqual(item["modifiers"][0]["attributes"], {"category": "bonus", "source": "test"})

    def test_adapt_basic_item(self):
        parsed_xml = parse_xml(
            """
            <item>
                <name>Backpack</name>
                <type>G</type>
                <weight>5</weight>
                <value>2</value>
                <text>A backpack can hold one cubic foot of gear.</text>
                <text>Source: Player's Handbook p. 153</text>
            </item>
            """
        )

        adapted_item = ItemAdaptor().adapt(parse_item(parsed_xml))

        self.assertEqual(adapted_item["category"], "adventuring_gear")
        self.assertEqual(adapted_item["weight"], 5.0)
        self.assertEqual(adapted_item["cost"], {"amount": 2, "currency": "gp"})
        self.assertEqual(
            adapted_item["description"],
            "A backpack can hold one cubic foot of gear.",
        )
        self.assertEqual(
            adapted_item["source"],
            {"text": "Player's Handbook p. 153"},
        )
        Item.model_validate(adapted_item)
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                adapted_item,
                PROJECT_ROOT / "schemas",
            )
        )

    def test_adapt_d3_charge_recharge(self):
        adapted_item = ItemAdaptor().adapt(
            {
                "name": "D3 Charge Item",
                "type": "W",
                "magic": "1",
                "detail": "rare",
                "text": [
                    "This item has 3 charges and regains 1d3 expended charges daily.",
                    "Source: Test",
                ],
            }
        )

        self.assertEqual(
            adapted_item["magic_item"]["charges"]["recharge"],
            {"count": 1, "dice": 3},
        )
        item = Item.model_validate(adapted_item)
        self.assertTrue(
            validate(
                PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                item.model_dump(mode="json", exclude_none=True),
                PROJECT_ROOT / "schemas",
            )
        )

    def test_adapt_weapon_and_armor(self):
        dagger = ItemAdaptor().adapt(parse_item(parse_xml(
            """
            <item>
                <name>Dagger</name>
                <type>M</type>
                <weight>1</weight>
                <value>2</value>
                <text>Finesse: A dagger is a finesse weapon.</text>
                <text>Source: Player's Handbook p. 149</text>
                <dmg1>1d4</dmg1>
                <dmgType>P</dmgType>
                <property>F,L,T</property>
                <range>20/60</range>
            </item>
            """
        )))
        chain_mail = ItemAdaptor().adapt(parse_item(parse_xml(
            """
            <item>
                <name>Chain Mail</name>
                <type>HA</type>
                <weight>55</weight>
                <value>75</value>
                <text>Made of interlocking metal rings.</text>
                <text>Source: Player's Handbook p. 145</text>
                <ac>16</ac>
                <strength>13</strength>
                <stealth>1</stealth>
            </item>
            """
        )))

        self.assertEqual(dagger["category"], "weapon")
        self.assertEqual(dagger["weapon"]["type"], "dagger")
        self.assertEqual(
            dagger["weapon"]["properties"],
            ["finesse", "light", "thrown"],
        )
        self.assertEqual(dagger["weapon"]["range"], {"normal": 20, "long": 60})
        self.assertEqual(
            dagger["weapon"]["effects"][0]["damage"],
            {"type": "piercing", "roll": {"count": 1, "dice": 4}},
        )
        self.assertEqual(
            chain_mail["armor"],
            {
                "category": "heavy",
                "type": "chain_mail",
                "armor_class": 16,
                "stealth_disadvantage": True,
                "strength_requirement": 13,
            },
        )
        self.assertNotIn("magic_item", dagger)
        self.assertNotIn("magic_item", chain_mail)
        for item in (dagger, chain_mail):
            Item.model_validate(item)
            self.assertTrue(
                validate(
                    PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                    item,
                    PROJECT_ROOT / "schemas",
                )
            )

    def test_adapt_artifact_weapon_uses_proficiency_base_type(self):
        sword = ItemAdaptor().adapt(parse_item(parse_xml(
            """
            <item>
                <name>Sword of Kas</name>
                <type>M</type>
                <magic>1</magic>
                <detail>artifact (requires attunement)</detail>
                <weight>3</weight>
                <text>Introductory lore.</text>
                <text>More introductory lore.</text>
                <text>Random Properties: The sword has random properties.</text>
                <text>Spirit of Kas: The sword grants a bonus.</text>
                <text>Spells: The sword casts spells.</text>
                <text>Sentience: The sword is sentient.</text>
                <text>Personality: The sword seeks Vecna.</text>
                <text>Destroying the Sword: The sword can be destroyed.</text>
                <text>Versatile: This weapon can be used with one or two hands.</text>
                <text>Proficiency: martial, longsword</text>
                <text>Source: Dungeon Master's Guide p. 226</text>
                <dmg1>1d8</dmg1>
                <dmg2>1d10</dmg2>
                <dmgType>S</dmgType>
                <property>V</property>
            </item>
            """
        )))

        self.assertEqual(sword["weapon"]["type"], "longsword")
        self.assertEqual(
            sword["description"],
            "Introductory lore.\n\nMore introductory lore.",
        )
        self.assertEqual(
            [feature["name"] for feature in sword["features"]],
            [
                "Random Properties",
                "Spirit of Kas",
                "Spells",
                "Sentience",
                "Personality",
                "Destroying the Sword",
                "Proficiency",
            ],
        )

    def test_adapt_source_weapon_and_armor_representatives(self):
        source_items = {}
        for element in parse_xml(PROJECT_ROOT / "5eFile.xml")["children"]:
            if element["tag"] != "item":
                continue
            name = next(
                child["text"]
                for child in element["children"]
                if child["tag"] == "name"
            )
            if name in {"Shield", "Longbow", "Longsword"}:
                source_items[name] = parse_item(element)

        adapted_items = {
            name: ItemAdaptor().adapt(source)
            for name, source in source_items.items()
        }

        self.assertEqual(adapted_items["Shield"]["armor"]["category"], "shield")
        self.assertEqual(adapted_items["Shield"]["armor"]["armor_class"], 2)
        self.assertEqual(
            adapted_items["Longbow"]["weapon"]["properties"],
            ["ammunition", "heavy", "two_handed"],
        )
        self.assertEqual(
            adapted_items["Longbow"]["weapon"]["range"],
            {"normal": 150, "long": 600},
        )
        self.assertEqual(
            adapted_items["Longsword"]["weapon"]["properties"],
            ["versatile"],
        )
        self.assertEqual(
            adapted_items["Longsword"]["weapon"]["effects"][1]["damage"],
            {"type": "slashing", "roll": {"count": 1, "dice": 10}},
        )
        for item in adapted_items.values():
            Item.model_validate(item)
            self.assertTrue(
                validate(
                    PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                    item,
                    PROJECT_ROOT / "schemas",
                )
            )

    def test_adapt_source_magic_item_representatives(self):
        source_items = {}
        for element in parse_xml(PROJECT_ROOT / "5eFile.xml")["children"]:
            if element["tag"] != "item":
                continue
            name = next(
                child["text"]
                for child in element["children"]
                if child["tag"] == "name"
            )
            if name in {
                "Arrows +1",
                "Armor of Vulnerability (Bludgeoning)",
                "Staff of Power",
            }:
                source_items[name] = parse_item(element)

        adapted_items = {
            name: ItemAdaptor().adapt(source)
            for name, source in source_items.items()
        }

        self.assertEqual(
            adapted_items["Arrows +1"]["magic_item"],
            {
                "rarity": "uncommon",
                "attunement": False,
                "bonuses": [
                    {"type": "attack", "value": 1},
                    {"type": "damage", "value": 1},
                ],
            },
        )
        self.assertEqual(
            adapted_items["Armor of Vulnerability (Bludgeoning)"]["magic_item"]["rarity"],
            "rare",
        )
        self.assertTrue(
            adapted_items["Armor of Vulnerability (Bludgeoning)"]["magic_item"]["attunement"]
        )
        staff_magic = adapted_items["Staff of Power"]["magic_item"]
        self.assertEqual(staff_magic["charges"]["maximum"], 20)
        self.assertEqual(staff_magic["charges"]["recharge"]["modifier"], 4)
        self.assertIn(
            {"spell": "cone of cold", "charges": 5},
            staff_magic["spells"],
        )
        self.assertIn(
            "Power Strike",
            {feature["name"] for feature in adapted_items["Staff of Power"]["features"]},
        )
        for item in adapted_items.values():
            Item.model_validate(item)
            self.assertTrue(
                validate(
                    PROJECT_ROOT / "schemas" / "entities" / "Item.schema.json",
                    item,
                    PROJECT_ROOT / "schemas",
                )
            )