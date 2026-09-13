import shutil
from pathlib import Path

import pandas as pd
from projectfoundry import BlockData, BlockObject
from pydantic import Field

from application.database_service import DatabaseService

from .object_base import PayloadStore, ProjectObject


class DatabaseBlockData(BlockData):
    """ProjectFoundry metadata for a DMTools SQLite database."""

    database_path: str | None = None
    queries: list[dict] = Field(default_factory=list)


class DatabaseBlock(BlockObject):
    """Registration block for a database during the migration."""

    type_name = "database"

    def __init__(self, name, database_path=None, queries=None, guid=None):
        super().__init__(
            name=name,
            guid=guid,
            block_data=DatabaseBlockData(
                database_path=str(database_path) if database_path else None,
                queries=list(queries or []),
            ),
        )

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        del prepared, progress_callback

    def serialise(self, path):
        del path


class DatabaseObject(ProjectObject):
    """A project object wrapping a SQLite database and its saved queries."""

    type_name = "database"

    def __init__(self, name, database_path=None, queries=None, **kwargs):
        super().__init__(name, **kwargs)
        self.database_path = Path(database_path) if database_path else None
        self.object_data = PayloadStore(self.database_path)
        self.queries = list(queries) if queries is not None else []
        self.query_objects = []
        self.revision = 0
        self._change_callbacks = []
        self.block_object = DatabaseBlock(
            self.name,
            database_path=self.database_path,
            queries=self.queries,
            guid=self.guid,
        )

    @property
    def service(self):
        if self.database_path is None:
            raise ValueError(f"database object '{self.name}' has no database file")
        return DatabaseService(self.database_path)

    def add_change_callback(self, callback):
        self._change_callbacks.append(callback)

    def _changed(self):
        self.revision += 1
        self.block_object.name = self.name
        self.block_object.block_data = DatabaseBlockData(
            database_path=str(self.database_path) if self.database_path else None,
            queries=list(self.queries),
        )
        self.block_object.mark_changed()
        for callback in tuple(self._change_callbacks):
            callback(self)

    def add_query(self, name: str, sql: str):
        """Save a named query for later reuse against this database."""
        self.queries.append({"name": name, "sql": sql})
        self._changed()

    def add_query_object(self, query_object):
        """Attach a saved query object as a child of this database."""
        query_object.database_guid = self.guid
        query_object.block_object.block_data.database_guid = self.guid
        self.block_object.add_child_block_object(query_object.block_object)
        if query_object not in self.query_objects:
            self.query_objects.append(query_object)
        if query_object.node.parent is not self.node:
            self.node.add_child(query_object.node)
        self._changed()

    def remove_query(self, name: str):
        """Remove a previously saved query by name."""
        self.queries = [query for query in self.queries if query["name"] != name]
        self._changed()

    def run_query(self, sql: str, parameters=()) -> pd.DataFrame:
        """Execute ``sql`` against the database and return the results."""
        return self.service.query(sql, parameters)

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item["queries"] = list(self.queries)
        if self.database_path is None:
            item["data_file"] = None
            return item
        stored_path = Path(project_directory) / PayloadStore.DATA_DIRECTORY / f"{self.guid}.sqlite"
        if self.database_path.resolve() != stored_path.resolve():
            stored_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.database_path, stored_path)
            self.database_path = stored_path
        self.object_data.value = self.database_path
        item.update({"data_file": f"{PayloadStore.DATA_DIRECTORY}/{stored_path.name}"})
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        database_file = data.get("data_file", data.get("database_file"))
        database_path = (
            Path(project_directory) / database_file if database_file else None
        )
        return cls(
            name=data["name"],
            database_path=database_path,
            queries=data.get("queries", []),
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
