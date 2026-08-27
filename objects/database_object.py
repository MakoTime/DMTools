import shutil
import sqlite3
from pathlib import Path

import pandas as pd

from application.database_service import DatabaseService
from .object_base import ObjectBase, ObjectData


class DatabaseObject(ObjectBase):
    """A project object wrapping a SQLite database and its saved queries."""

    type_name = "database"

    def __init__(self, name, database_path=None, queries=None, **kwargs):
        super().__init__(name, **kwargs)
        self.database_path = Path(database_path) if database_path else None
        self.object_data = ObjectData(self.database_path)
        self.queries = list(queries) if queries is not None else []
        self.query_objects = []
        self.revision = 0
        self._change_callbacks = []

    @property
    def service(self):
        if self.database_path is None:
            raise ValueError(f"database object '{self.name}' has no database file")
        return DatabaseService(self.database_path)

    def add_change_callback(self, callback):
        self._change_callbacks.append(callback)

    def _changed(self):
        self.revision += 1
        for callback in tuple(self._change_callbacks):
            callback(self)

    def add_query(self, name: str, sql: str):
        """Save a named query for later reuse against this database."""
        self.queries.append({"name": name, "sql": sql})
        self._changed()

    def add_query_object(self, query_object):
        """Attach a saved query object as a child of this database."""
        query_object.database_guid = self.guid
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
        stored_path = Path(project_directory) / ObjectData.DATA_DIRECTORY / f"{self.guid}.sqlite"
        if self.database_path.resolve() != stored_path.resolve():
            stored_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.database_path, stored_path)
            self.database_path = stored_path
        self.object_data.value = self.database_path
        item.update({"data_file": f"{ObjectData.DATA_DIRECTORY}/{stored_path.name}"})
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
