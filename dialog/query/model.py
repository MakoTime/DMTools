from copy import deepcopy
from dataclasses import dataclass, field

from dialog.base.editor import EditorModel
from dialog.database.model import FilterCondition, MultiTableLookup


@dataclass
class QueryEditorModel(EditorModel):
    """Temporary saved-query state owned by one editor session."""

    name: str = "Query"
    sql: str = ""
    table_name: str = ""
    filters: list[FilterCondition] = field(default_factory=list)
    lookup: MultiTableLookup = field(default_factory=MultiTableLookup)
    query_object: object | None = field(default=None, repr=False)

    @classmethod
    def from_query(cls, query_object):
        return cls(
            name=query_object.name,
            sql=query_object.sql,
            table_name=query_object.table_name,
            filters=deepcopy(query_object.filters),
            lookup=deepcopy(query_object.lookup),
            query_object=query_object,
        )

    def validate(self):
        if not self.name.strip():
            raise ValueError("Enter a query name.")
        if not self.sql.strip():
            raise ValueError("Enter a SQL query.")

    def apply(self):
        self.name = self.name.strip()
        self.sql = self.sql.strip()
        self.validate()
        return self