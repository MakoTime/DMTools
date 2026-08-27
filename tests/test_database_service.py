import sqlite3

import pandas as pd

from application.database_service import DatabaseService


def make_database(tmp_path):
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE monsters (id INTEGER PRIMARY KEY, name TEXT, hp INTEGER)"
        )
        connection.executemany(
            "INSERT INTO monsters(name, hp) VALUES (?, ?)",
            [("Frost Giant", 138), ("Ancient Dragon", 546)],
        )
    return path


def test_query_returns_pandas_frame(tmp_path):
    service = DatabaseService(make_database(tmp_path))

    result = service.query("SELECT name FROM monsters WHERE hp > ?", (150,))

    assert isinstance(result, pd.DataFrame)
    assert result["name"].tolist() == ["Ancient Dragon"]


def test_crud_operations_are_persisted(tmp_path):
    service = DatabaseService(make_database(tmp_path))

    service.insert_row("monsters", {"name": "Yeti", "hp": 51})
    service.update_row("monsters", "name", "Yeti", {"hp": 60})
    service.delete_row("monsters", "name", "Frost Giant")

    result = service.query("SELECT name, hp FROM monsters ORDER BY name")
    assert result.to_dict("records") == [
        {"name": "Ancient Dragon", "hp": 546},
        {"name": "Yeti", "hp": 60},
    ]


def test_table_names_are_not_interpreted_as_sql(tmp_path):
    service = DatabaseService(make_database(tmp_path))

    try:
        service.table_schema("monsters; DROP TABLE monsters")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid identifier was accepted")
