from dataclasses import dataclass

from application.rules_catalog import rule_details
from dialog.base.editor import EditorModel


@dataclass
class RuleDetailModel(EditorModel):
    value: str
    category: str
    schema_names: tuple[str, ...]

    @property
    def title(self):
        return self.value.replace("_", " ").title()

    @property
    def details(self):
        return rule_details(self.value, self.category, self.schema_names)