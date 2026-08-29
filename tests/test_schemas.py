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
                

if __name__ == "__main__":
    unittest.main()
