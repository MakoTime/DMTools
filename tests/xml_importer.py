from pathlib import Path


class XMLImporter:
    def __init__(self, data_root: Path):
        self.data_root = data_root

    def iter_tests(self):
        yield from sorted(self.data_root.glob("*.xml"))