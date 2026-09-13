import sqlite3

import pandas as pd
from PySide6.QtWidgets import QApplication, QDialog, QGroupBox, QMenu
from PySide6.QtCore import Qt

from application.project_controller import ProjectController
from dialog.base.popup_editor import PopupEditorView
from dialog.base.mdi_contracts import (
    DatabaseWorkspaceMdiContract,
    EditableDraftMdiContract,
    EntityInspectionMdiContract,
    EntityQueryResultsMdiContract,
    ObjectInspectionMdiContract,
    TableEditorMdiContract,
)
from dialog.entity_detail.mdi_view import EntityDetailMdiView
from dialog.entity_query_results.view import EntityQueryResultsView
from dialog.homebrew.mdi_view import HomebrewEditorMdiView
from dialog.database.model import (
    DatabaseWorkspaceModel,
    DataFrameModel,
    FilterCondition,
)
from dialog.database.view import DatabaseWorkspaceView
from dialog.base.widget_editor import WidgetEditorView
from dialog.database.factory import create_database_workspace
from dialog.db_base.factory import create_database_dialog
from dialog.db_base.model import DatabaseModel
from dialog.db_base.view import DatabaseView
from dialog.query.factory import create_query_dialog
from dialog.query.model import QueryEditorModel
from objects.database_object import DatabaseObject
from objects.query_object import QueryObject
from tools.widgets import SplitButton


def qt_app():
    return QApplication.instance() or QApplication([])


def test_dataframe_model_sorts_by_clicked_header():
    qt_app()
    model = DataFrameModel(pd.DataFrame({"name": ["B", "A"], "level": [2, 1]}))

    model.sort(0)

    assert model.frame["name"].tolist() == ["A", "B"]

    model.sort(1, Qt.SortOrder.DescendingOrder)
    assert model.frame["level"].tolist() == [2, 1]


def test_database_workspace_uses_widget_editor_factory(tmp_path):
    qt_app()
    workspace = create_database_workspace(DatabaseObject("Rules", tmp_path / "rules.sqlite"))

    assert isinstance(workspace, WidgetEditorView)
    assert workspace.model.database_object.name == "Rules"


def test_database_workspace_resolves_by_uid_and_releases_payload(tmp_path):
    qt_app()
    database = DatabaseObject("Rules", tmp_path / "rules.sqlite")
    loaded_uids = []

    def load_database(uid):
        loaded_uids.append(uid)
        return database

    model = DatabaseWorkspaceModel(
        database_uid=database.guid,
        database_loader=load_database,
    )
    workspace = create_database_workspace(model)

    assert loaded_uids == [database.guid]
    assert workspace.model.database_object is database

    workspace.close_editor("test")

    assert workspace.model.database_object is None
    assert workspace.database_object is None


def test_database_definition_uses_model_view_factory():
    qt_app()

    dialog = create_database_dialog(DatabaseModel(name="Rules"))

    assert isinstance(dialog, DatabaseView)
    assert dialog.model.name == "Rules"


def test_mdi_views_follow_separate_structural_contracts():
    contracts = {
        EntityInspectionMdiContract: ("refresh_entity", "close_editor"),
        EditableDraftMdiContract: ("apply_changes", "close_editor"),
        DatabaseWorkspaceMdiContract: ("refresh_schema", "run_query"),
        EntityQueryResultsMdiContract: (
            "selected_entity_uid",
            "open_selected_entity",
            "navigate_back",
        ),
        TableEditorMdiContract: (
            "refresh_table",
            "commit_changes",
            "close_editor",
        ),
        ObjectInspectionMdiContract: ("refresh_object", "close_editor"),
    }
    for contract, methods in contracts.items():
        assert contract.__name__.endswith("MdiContract")
        assert all(hasattr(contract, method) for method in methods)
    assert all(
        isinstance(view, type)
        for view in (
            EntityDetailMdiView,
            HomebrewEditorMdiView,
            DatabaseWorkspaceView,
            EntityQueryResultsView,
        )
    )


def test_query_editor_model_keeps_persistent_query_unchanged_until_apply():
    query = QueryObject(
        "Spells",
        sql="SELECT * FROM spells",
        filters=[],
    )

    draft = QueryEditorModel.from_query(query)
    draft.name = "Cantrips"
    draft.sql = "SELECT * FROM spells WHERE level = 0"
    draft.filters.append(FilterCondition("level", "Equals", "0"))

    assert query.name == "Spells"
    assert query.sql == "SELECT * FROM spells"
    assert query.filters == []
    assert draft.apply() is draft


def test_query_editor_model_rejects_empty_name_and_sql():
    draft = QueryEditorModel(name=" ", sql="SELECT 1")

    try:
        draft.apply()
    except ValueError as error:
        assert str(error) == "Enter a query name."
    else:
        raise AssertionError("Expected an empty query name to be rejected")

    draft.name = "Query"
    draft.sql = " "
    try:
        draft.apply()
    except ValueError as error:
        assert str(error) == "Enter a SQL query."
    else:
        raise AssertionError("Expected empty SQL to be rejected")


def test_query_editor_factory_uses_popup_editor_base():
    qt_app()

    dialog = create_query_dialog(QueryEditorModel(name="Spells", sql="SELECT 1"))

    assert isinstance(dialog, PopupEditorView)
    assert dialog.model.name == "Spells"


def test_query_editor_cancel_does_not_mutate_saved_query(tmp_path, monkeypatch):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")
    database = DatabaseObject("Rules", path)
    query = QueryObject("Spells", sql="SELECT * FROM spells")
    database.add_query_object(query)
    workspace = DatabaseWorkspaceView(database)
    workspace.query_list.setCurrentIndex(0)
    workspace.sql_edit.setPlainText("SELECT * FROM spells WHERE level = 0")

    class RejectedDialog:
        def __init__(self, model):
            self.model = model

        def exec(self):
            self.model.name = "Cantrips"
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "dialog.database.view.create_query_dialog",
        lambda model, parent=None: RejectedDialog(model),
    )

    assert workspace.save_query() is None
    assert query.name == "Spells"
    assert query.sql == "SELECT * FROM spells"


def test_query_editor_accept_routes_update_through_project(tmp_path, monkeypatch):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")
    controller = ProjectController()
    database = DatabaseObject("Rules", path)
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.register_database(database)
    query = QueryObject("Spells", sql="SELECT * FROM spells")
    controller.register_query(database, query)
    workspace = DatabaseWorkspaceView(database)
    workspace.query_list.setCurrentIndex(0)
    workspace.sql_edit.setPlainText("SELECT * FROM spells WHERE level = 0")

    class AcceptedDialog:
        def __init__(self, model):
            self.model = model

        def exec(self):
            self.model.name = "Cantrips"
            self.model.apply()
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(
        "dialog.database.view.create_query_dialog",
        lambda model, parent=None: AcceptedDialog(model),
    )

    assert workspace.save_query() is query
    assert query.name == "Cantrips"
    assert query.sql == "SELECT * FROM spells WHERE level = 0"
    assert query.block_object.name == "Cantrips"
    assert query.block_object.block_data.sql == query.sql


def test_split_button_displays_primary_action_and_dropdown_menu():
    qt_app()
    button = SplitButton("AND")

    button.setMenu(QMenu())

    assert button.text() == "AND"
    assert button.popupMode() == SplitButton.ToolButtonPopupMode.MenuButtonPopup


def test_query_builder_generates_select_without_sql(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (id INTEGER, spell_name TEXT)")
        connection.execute("INSERT INTO spells VALUES (1, 'Shield')")

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)
    workspace.build_query()

    assert workspace.sql_edit.toPlainText() == 'SELECT * FROM "spells"'
    assert workspace.result_model.frame["spell_name"].tolist() == ["Shield"]


def test_query_builder_adds_common_filter_operator(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (id INTEGER, level INTEGER)")
        connection.executemany("INSERT INTO spells VALUES (?, ?)", [(1, 1), (2, 3)])

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)
    workspace.filter_column.setCurrentText("level")
    workspace.filter_operator.setCurrentText("Greater than")
    workspace.filter_value.setText("1")
    workspace.add_filter()
    workspace.build_query()

    assert workspace.sql_edit.toPlainText() == 'SELECT * FROM "spells" WHERE "level" > 1'
    assert workspace.result_model.frame["level"].tolist() == [3]


def test_query_builder_supports_contains_and_case_insensitive_equals(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (name TEXT)")
        connection.executemany(
            "INSERT INTO spells VALUES (?)", [("Fire Bolt",), ("FIREBALL",)]
        )

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)
    workspace.filter_column.setCurrentText("name")
    workspace.filter_operator.setCurrentText("Contains")
    workspace.filter_value.setText("fire")
    workspace.add_filter()
    workspace.build_query()
    assert workspace.result_model.frame["name"].tolist() == ["Fire Bolt", "FIREBALL"]

    workspace.clear_filters()
    workspace.filter_operator.setCurrentText("Equals (case-insensitive)")
    workspace.filter_value.setText("fire bolt")
    workspace.add_filter()
    workspace.build_query()
    assert workspace.result_model.frame["name"].tolist() == ["Fire Bolt"]


def test_query_builder_supports_logical_filter_relationships(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")
        connection.executemany("INSERT INTO spells VALUES (?)", [(1,), (2,), (3,)])

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)

    def add_level_filter(operator, value):
        workspace.filter_column.setCurrentText("level")
        workspace.filter_operator.setCurrentText(operator)
        workspace.filter_value.setText(value)
        workspace.add_filter()

    expected_levels = {
        "AND": [2],
        "OR": [1, 2, 3],
        "NOT": [3],
        "XOR": [1, 3],
        "NAND": [1, 3],
        "NOR": [],
    }
    for logical_operator, levels in expected_levels.items():
        workspace.clear_filters()
        add_level_filter("Greater than or equal", "2")
        workspace.set_relationship(logical_operator)
        add_level_filter("Less than or equal", "2")
        workspace.build_query()
        assert workspace.result_model.frame["level"].tolist() == levels


def test_query_builder_supports_explicit_filter_groups(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")
        connection.executemany("INSERT INTO spells VALUES (?)", [(1,), (2,), (3,)])

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)

    def add_level_filter(value):
        workspace.filter_column.setCurrentText("level")
        workspace.filter_operator.setCurrentText("Equals")
        workspace.filter_value.setText(value)
        workspace.add_filter()

    add_level_filter("1")
    workspace.set_relationship("OR")
    add_level_filter("3")
    assert [
        workspace.filter_list.item(row).text()
        for row in range(workspace.filter_list.count())
    ] == ["level Equals 1", "OR", "level Equals 3"]
    workspace.filter_list.setCurrentRow(0)
    workspace._change_selected_group("open")
    workspace.filter_list.setCurrentRow(2)
    workspace._change_selected_group("close")
    assert [
        workspace.filter_list.item(row).text()
        for row in range(workspace.filter_list.count())
    ] == ["(", "level Equals 1", "OR", "level Equals 3", ")"]
    workspace.build_query()

    assert 'WHERE (("level" = 1) OR ("level" = 3))' in workspace.sql_edit.toPlainText()
    assert workspace.result_model.frame["level"].tolist() == [1, 3]


def test_query_builder_queues_relationship_before_next_filter(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)
    workspace.filter_column.setCurrentText("level")
    workspace.filter_value.setText("1")
    workspace.add_filter()

    workspace.set_relationship("OR")
    workspace.relationship_button.click()

    assert [
        workspace.filter_list.item(row).text()
        for row in range(workspace.filter_list.count())
    ] == ["level Equals 1", "OR"]

    workspace.filter_value.setText("2")
    workspace.add_filter()
    assert [
        workspace.filter_list.item(row).text()
        for row in range(workspace.filter_list.count())
    ] == ["level Equals 1", "OR", "level Equals 2"]


def test_query_builder_defers_filter_validation_until_build(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE spells (level INTEGER)")

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace.table_list.setCurrentRow(0)
    workspace.filter_column.setCurrentText("level")
    workspace.filter_value.clear()
    workspace.add_filter()

    assert workspace.filter_list.count() == 1
    workspace.build_query()
    assert workspace.status.text() == "Filter 1 needs a value."


def test_query_builder_supports_multitable_lookup_with_output_filters(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE dnd5_classes (class_id INTEGER, class_name TEXT)")
        connection.execute(
            "CREATE TABLE dnd5_class_spells (class_id INTEGER, spell_id INTEGER)"
        )
        connection.execute(
            "CREATE TABLE dnd5_spells "
            "(spell_id INTEGER, spell_name TEXT, spell_level INTEGER, spell_type TEXT)"
        )
        connection.execute("INSERT INTO dnd5_classes VALUES (1, 'wizard')")
        connection.executemany(
            "INSERT INTO dnd5_class_spells VALUES (?, ?)", [(1, 10), (1, 11)]
        )
        connection.executemany(
            "INSERT INTO dnd5_spells VALUES (?, ?, ?, ?)",
            [(10, "Shield", 1, "abjuration"), (11, "Fireball", 3, "evocation")],
        )

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    assert any(
        box.title() == "Multi-table lookup"
        for box in workspace.findChildren(QGroupBox)
    )
    workspace.lookup_enabled.setChecked(True)
    workspace.lookup_table.setCurrentText("dnd5_classes")
    workspace.lookup_column.setCurrentText("class_name")
    workspace.lookup_value.setText("wizard")
    workspace.lookup_return_column.setCurrentText("class_id")
    workspace.bridge_table.setCurrentText("dnd5_class_spells")
    workspace.bridge_lookup_column.setCurrentText("class_id")
    workspace.bridge_output_column.setCurrentText("spell_id")
    workspace.output_table.setCurrentText("dnd5_spells")
    workspace.output_column.setCurrentText("spell_id")
    workspace.filter_column.setCurrentText("spell_level")
    workspace.filter_operator.setCurrentText("Greater than")
    workspace.filter_value.setText("2")
    workspace.add_filter()
    workspace.build_query()

    assert workspace.result_model.frame["spell_name"].tolist() == ["Fireball"]
    assert "dnd5_class_spells" in workspace.sql_edit.toPlainText()


def test_row_lookup_uses_text_then_column_inputs(tmp_path):
    qt_app()
    path = tmp_path / "rules.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE dnd5_classes (class_id INTEGER, class_name TEXT)")
        connection.execute("CREATE TABLE dnd5_class_spells (class_id INTEGER, spell_id INTEGER)")
        connection.execute("CREATE TABLE dnd5_spells (spell_id INTEGER, spell_name TEXT)")
        connection.execute("INSERT INTO dnd5_classes VALUES (1, 'Wizard')")
        connection.execute("INSERT INTO dnd5_class_spells VALUES (1, 10)")
        connection.execute("INSERT INTO dnd5_spells VALUES (10, 'Fireball')")

    workspace = DatabaseWorkspaceView(DatabaseObject("Rules", path))
    workspace._add_lookup_step_row()
    workspace._add_lookup_step_row()
    for row, (table, output) in enumerate(
        (
            ("dnd5_classes", "class_id"),
            ("dnd5_class_spells", "spell_id"),
            ("dnd5_spells", "spell_id"),
        )
    ):
        workspace.lookup_steps_table.cellWidget(row, 0).setCurrentText(table)
        workspace.lookup_steps_table.cellWidget(row, 3).setCurrentText(output)
    workspace.lookup_steps_table.cellWidget(0, 2).setText("Wizard")
    workspace.lookup_steps_table.cellWidget(1, 2).setCurrentText("class_id")
    workspace.lookup_steps_table.cellWidget(2, 2).setCurrentText("spell_id")
    workspace._use_last_lookup_output()
    workspace.build_query()

    assert workspace.result_model.frame["spell_name"].tolist() == ["Fireball"]
