from pathlib import Path
import unittest

from schema_importer import SchemaImporter
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_ROOT = PROJECT_ROOT / "schemas"
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "schemas"


class TestSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_importer = SchemaImporter(
            SCHEMA_ROOT,
            DATA_ROOT,
        )

    def test_schemas(self):
        for schema_path, data_path in self.schema_importer.iter_tests():
            with self.subTest(
                schema=schema_path.name,
                data=data_path.name,
            ):
                self.assertTrue(
                    validate(schema_path, data_path, SCHEMA_ROOT)
                )

    def test_language_and_custom_value_rules(self):
        creature_schema = SCHEMA_ROOT / "entities" / "Creature.schema.json"
        self.assertTrue(
            validate(
                creature_schema,
                {"name": "Test", "languages": ["common", "Astral"]},
                SCHEMA_ROOT,
            )
        )
        with self.assertRaises(ValueError):
            validate(
                creature_schema,
                {"name": "Test", "languages": [""]},
                SCHEMA_ROOT,
            )

        progression_schema = (
            SCHEMA_ROOT / "values" / "spellcasting_progression.schema.json"
        )
        self.assertTrue(
            validate(progression_schema, "homebrew_progression", SCHEMA_ROOT)
        )


if __name__ == "__main__":
    unittest.main()
