from dataclasses import asdict

from projectfoundry import BlockData, BlockObject
from pydantic import Field

from dialog.database.model import FilterCondition, MultiTableLookup

from .object_base import ProjectObject


class QueryBlockData(BlockData):
    """ProjectFoundry metadata for a saved database query."""

    database_guid: str | None = None
    sql: str = ""
    table_name: str = ""
    filters: list[dict] = Field(default_factory=list)
    lookup: dict = Field(default_factory=dict)


class QueryBlock(BlockObject):
    """Registration block for a saved query during the migration."""

    type_name = "query"

    def __init__(self, name, database_guid=None, sql="", table_name="", filters=None, lookup=None, guid=None):
        super().__init__(
            name=name,
            guid=guid,
            block_data=QueryBlockData(
                database_guid=database_guid,
                sql=sql,
                table_name=table_name,
                filters=list(filters or []),
                lookup=dict(lookup or {}),
            ),
        )

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        del prepared, progress_callback

    def serialise(self, path):
        del path


class QueryObject(ProjectObject):
    """A saved query configuration owned by one database object."""

    type_name = "query"

    def __init__(
        self,
        name,
        database_guid=None,
        sql="",
        table_name="",
        filters=None,
        lookup=None,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.database_guid = database_guid
        self.sql = sql
        self.table_name = table_name
        self.filters = list(filters or [])
        self.lookup = lookup or MultiTableLookup()
        self.block_object = QueryBlock(
            self.name,
            database_guid=self.database_guid,
            sql=self.sql,
            table_name=self.table_name,
            filters=[asdict(condition) for condition in self.filters],
            lookup=asdict(self.lookup),
            guid=self.guid,
        )

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item.update(
            {
                "database_guid": self.database_guid,
                "sql": self.sql,
                "table_name": self.table_name,
                "filters": [asdict(condition) for condition in self.filters],
                "lookup": asdict(self.lookup),
            }
        )
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        filters = [FilterCondition(**item) for item in data.get("filters", [])]
        lookup = MultiTableLookup(**data.get("lookup", {}))
        return cls(
            name=data["name"],
            database_guid=data.get("database_guid"),
            sql=data.get("sql", ""),
            table_name=data.get("table_name", ""),
            filters=filters,
            lookup=lookup,
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )