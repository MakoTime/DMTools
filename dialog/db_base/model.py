from dataclasses import dataclass, field
import sqlite3
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DatabaseTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.database_path = None
        self.query = ""
        self.error = None

        self._columns = []
        self._rows = []

    @classmethod
    def from_database(cls, database_path: str, query: str, parent=None):
        instance = cls(parent)
        instance.database_path = database_path
        instance.query = query
        instance.load()
        return instance

    def load(self):
        self.beginResetModel()
        self.error = None
        self._columns = []
        self._rows = []
        try:
            if not self.database_path:
                raise ValueError("Choose a SQLite database file")
            if not self.query.strip():
                raise ValueError("Enter a SQL query")
            with sqlite3.connect(self.database_path) as connection:
                cursor = connection.execute(self.query)
                self._columns = [
                    description[0] for description in cursor.description or []
                ]
                self._rows = cursor.fetchall()
        except (OSError, sqlite3.Error, ValueError) as error:
            self.error = str(error)
        finally:
            self.endResetModel()
        return self.error is None

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0

        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0

        return len(self._columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        value = self._rows[index.row()][index.column()]

        if value is None:
            return ""

        return str(value)

    def headerData(
        self,
        section,
        orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return self._columns[section]

        return section + 1

    def refresh(self):
        self.load()

@dataclass
class DatabaseQueryModel:
    name: str
    sql: str


@dataclass
class DatabaseModel:
    name: str = "Database"
    comments: str = ""
    guid: str = field(default_factory=lambda: str(uuid4()))
    database: DatabaseTableModel = field(default=None, repr=False)
    database_path: str = field(default="", repr=False)
    queries: list[DatabaseQueryModel] = field(default_factory=list)
    query: str = field(default="", repr=False)

    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseTableModel()
            if self.database_path and self.query:
                self.database.database_path = self.database_path
                self.database.query = self.query
                self.database.load()

    @property
    def active_query(self):
        return self.query

    def add_query(self, name="Query", sql=""):
        query = DatabaseQueryModel(name=name.strip() or "Query", sql=sql.strip())
        self.queries.append(query)
        self.query = query.sql
        return query

    def remove_query(self, index):
        if 0 <= index < len(self.queries):
            self.queries.pop(index)
            self.query = self.queries[0].sql if self.queries else ""

    @classmethod
    def from_object(cls, database_object) -> "DatabaseModel":
        queries = [
            DatabaseQueryModel(query["name"], query["sql"])
            for query in database_object.queries
        ]
        return cls(
            name=database_object.name,
            comments=database_object.metadata.get("comments", ""),
            guid=database_object.guid,
            database_path=str(database_object.database_path or ""),
            queries=queries,
            query=queries[0].sql if queries else "",
        )

    def to_object(self):
        from objects.database_object import DatabaseObject

        database = DatabaseObject(
            name=self.name,
            database_path=Path(self.database_path) if self.database_path else None,
            metadata={"comments": self.comments},
            guid=self.guid,
        )
        queries = self.queries or (
            [DatabaseQueryModel("Default query", self.query)]
            if self.query.strip()
            else []
        )
        for query in queries:
            if query.sql.strip():
                database.add_query(query.name, query.sql.strip())
        return database

    @classmethod
    def from_json(cls, data) -> "DatabaseModel":
        queries = [
            DatabaseQueryModel(item.get("name", "Query"), item.get("sql", ""))
            for item in data.get("queries", [])
        ]
        if not queries and data.get("query", "").strip():
            queries.append(DatabaseQueryModel("Default query", data["query"]))
        return cls(
            name=data.get("name", "Database"),
            comments=data.get("comments", ""),
            guid=data.get("guid", str(uuid4())),
            database_path=data.get("database_path"),
            queries=queries,
            query=data.get("query", ""),
        )
        
    def to_json(self) -> dict:
        return {
            "type": "database",
            "name": self.name,
            "comments": self.comments,
            "guid": self.guid,
            "database_path": self.database_path,
            "queries": [
                {"name": query.name, "sql": query.sql}
                for query in self.queries
            ],
        }
