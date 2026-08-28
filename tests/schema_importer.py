from pathlib import Path


class SchemaImporter:
    SCHEMA_MAP = {
        "creatures": "entities/Creature.schema.json",
        "items": "entities/Item.schema.json",
        "spells": "entities/Spell.schema.json",
    }

    def __init__(self, schema_root: Path, data_root: Path):
        self.schema_root = schema_root
        self.data_root = data_root

    def iter_tests(self):
        for directory, schema in self.SCHEMA_MAP.items():
            data_directory = self.data_root / "entities" / directory
            schema_path = self.schema_root / schema

            if not data_directory.exists():
                continue

            for data_path in sorted(data_directory.glob("*.json")):
                yield schema_path, data_path