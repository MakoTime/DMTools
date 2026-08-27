import sqlite3

from PySide6.QtWidgets import QApplication

from dialog.db_base.model import DatabaseModel
from dialog.db_base.view import DatabaseView


def qt_app():
    return QApplication.instance() or QApplication([])


def test_new_database_is_created_in_project_data(tmp_path):
    qt_app()
    model = DatabaseModel()
    dialog = DatabaseView(
        model,
        project_directory=tmp_path,
        is_new=True,
    )
    dialog.name_edit.setText("Campaign")
    dialog.path_edit.setText(str(tmp_path.parent / "outside" / "custom.sqlite"))

    dialog._accept()

    destination = tmp_path / "data" / "custom.sqlite"
    assert destination.is_file()
    assert model.database_path == str(destination)


def test_external_database_is_copied_into_project_data(tmp_path):
    qt_app()
    external = tmp_path.parent / "external.sqlite"
    with sqlite3.connect(external) as connection:
        connection.execute("CREATE TABLE imported (id INTEGER PRIMARY KEY)")

    model = DatabaseModel()
    dialog = DatabaseView(model, project_directory=tmp_path, is_new=True)
    dialog.name_edit.setText("Imported")
    dialog.external_database_path = external
    dialog.path_edit.setText(str(external))

    dialog._accept()

    destination = tmp_path / "data" / "external.sqlite"
    assert destination.is_file()
    assert destination != external
    with sqlite3.connect(destination) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchone() == ("imported",)


def test_sql_source_file_is_imported_as_sqlite_database(tmp_path):
    qt_app()
    source = tmp_path.parent / "seed.sql"
    source.write_text(
        "CREATE TABLE spells (id INTEGER PRIMARY KEY, name TEXT);"
        "INSERT INTO spells(name) VALUES ('Magic Missile');",
        encoding="utf-8",
    )

    model = DatabaseModel()
    dialog = DatabaseView(model, project_directory=tmp_path, is_new=True)
    dialog.name_edit.setText("Spells")
    dialog.external_database_path = source
    dialog.path_edit.setText(str(source))

    dialog._accept()

    destination = tmp_path / "data" / "seed.sqlite"
    assert destination.is_file()
    with sqlite3.connect(destination) as connection:
        assert connection.execute("SELECT name FROM spells").fetchone() == (
            "Magic Missile",
        )


def test_mysql_dump_is_imported_as_sqlite_database(tmp_path):
    qt_app()
    source = tmp_path.parent / "mysql_dump.sql"
    source.write_text(
        "SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n"
        "CREATE DATABASE IF NOT EXISTS `dnddb`;\n"
        "USE `dnddb`;\n"
        "CREATE TABLE `dnd5_classes` (\n"
        "  `class_id` int(11) NOT NULL AUTO_INCREMENT,\n"
        "  `class_name` varchar(9) NOT NULL,\n"
        "  PRIMARY KEY (`class_id`)\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=13;\n"
        "INSERT INTO `dnd5_classes` (`class_id`, `class_name`) VALUES\n"
        "(1, 'barbarian');\n",
        encoding="utf-8",
    )

    model = DatabaseModel()
    dialog = DatabaseView(model, project_directory=tmp_path, is_new=True)
    dialog.name_edit.setText("D&D Database")
    dialog.external_database_path = source
    dialog.path_edit.setText(str(source))

    dialog._accept()

    destination = tmp_path / "data" / "mysql_dump.sqlite"
    assert destination.is_file()
    with sqlite3.connect(destination) as connection:
        assert connection.execute(
            "SELECT class_name FROM dnd5_classes"
        ).fetchone() == ("barbarian",)


def test_invalid_sql_source_explains_why_dialog_stays_open(tmp_path):
    qt_app()
    source = tmp_path.parent / "invalid.sql"
    source.write_text("CREATE TABLE missing closing parenthesis (", encoding="utf-8")

    dialog = DatabaseView(DatabaseModel(), project_directory=tmp_path, is_new=True)
    dialog.name_edit.setText("Invalid")
    dialog.external_database_path = source
    dialog.path_edit.setText(str(source))

    dialog._accept()

    assert dialog.result() != dialog.DialogCode.Accepted
    assert "Unable to import database" in dialog.error_label.text()
