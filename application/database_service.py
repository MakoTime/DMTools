from pathlib import Path
import re
import sqlite3

import pandas as pd


class DatabaseService:
    """Execute SQLite operations for one authoritative database file."""

    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def connect(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.database_path)

    def list_tables(self):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            ).fetchall()
        return [row[0] for row in rows]

    def table_schema(self, table_name):
        with self.connect() as connection:
            return connection.execute(
                f"PRAGMA table_info({self._identifier(table_name)})"
            ).fetchall()

    def query(self, sql, parameters=()):
        with self.connect() as connection:
            return pd.read_sql_query(sql, connection, params=parameters)

    def execute(self, sql, parameters=()):
        with self.connect() as connection:
            cursor = connection.execute(sql, parameters)
            connection.commit()
            return cursor.rowcount

    def insert_row(self, table_name, values):
        columns = list(values)
        placeholders = ", ".join("?" for _ in columns)
        identifiers = ", ".join(self._identifier(column) for column in columns)
        self.execute(
            f"INSERT INTO {self._identifier(table_name)} ({identifiers}) "
            f"VALUES ({placeholders})",
            tuple(values[column] for column in columns),
        )

    def update_row(self, table_name, primary_key_column, primary_key, values):
        assignments = ", ".join(
            f"{self._identifier(column)} = ?" for column in values
        )
        parameters = tuple(values.values()) + (primary_key,)
        return self.execute(
            f"UPDATE {self._identifier(table_name)} SET {assignments} "
            f"WHERE {self._identifier(primary_key_column)} = ?",
            parameters,
        )

    def delete_row(self, table_name, primary_key_column, primary_key):
        return self.execute(
            f"DELETE FROM {self._identifier(table_name)} "
            f"WHERE {self._identifier(primary_key_column)} = ?",
            (primary_key,),
        )

    @staticmethod
    def _identifier(value):
        value = str(value)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(f"Invalid SQLite identifier: {value!r}")
        return f'"{value}"'
