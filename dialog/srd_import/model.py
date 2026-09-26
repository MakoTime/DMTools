from dataclasses import dataclass, field

from dialog.base.editor import EditorModel


@dataclass
class SRDImportModel(EditorModel):
    collections: tuple[str, ...] = ()
    query_options: dict[str, tuple[str, ...]] = field(default_factory=dict)
    collection: str = ""
    query: dict[str, str] = field(default_factory=dict)

    def validate(self):
        if not self.collection:
            raise ValueError("Choose an API collection.")

    def apply(self):
        self.validate()
        return self
