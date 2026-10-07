from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from application.class_presentation import class_progression_rows
from application.entity_rendering import render_entity_markdown
from application.project_controller import ProjectController
from dialog.progression_editor import ProgressionEditorModel
from dialog.progression_editor.view import ProgressionEditorView
from application.progression_table import custom_progression_rows, validate_formula


def test_editor_draft_is_detached_and_reorders_columns():
    payload = {
        "name": "Wizard",
        "presentation_progression": {
            "table_id": "class_progression",
            "columns": [
                {"key": "first", "label": "First", "values": {"1": "A"}},
                {"key": "second", "label": "Second", "values": {"1": "B"}},
            ],
        },
    }
    model = ProgressionEditorModel(payload)
    model.reorder_columns(("second", "first"))
    accepted = model.apply()

    assert [column["key"] for column in accepted["columns"]] == ["second", "first"]
    assert payload["presentation_progression"]["columns"][0]["key"] == "first"


def test_editor_rejects_duplicate_keys_and_invalid_levels():
    model = ProgressionEditorModel({})
    model.add_column("resource", "Resource")
    with pytest.raises(ValueError, match="unique"):
        model.add_column("resource", "Duplicate")

    model = ProgressionEditorModel({})
    model.add_column("resource", "Resource")
    model._draft["columns"][0]["values"] = {"21": 1}
    with pytest.raises(ValueError, match="levels"):
        model.apply()


def test_progression_editor_view_constructs_with_formula_controls():
    QApplication.instance() or QApplication([])
    view = ProgressionEditorView(ProgressionEditorModel({"features": []}))
    assert view.formula_edit.placeholderText() == "2 * [level] + [Wisdom]"
    assert not view.value_add.isEnabled()
    assert not view.value_remove.isEnabled()
    wisdom_action = view.add_variable_button.menu().actions()[7]
    assert wisdom_action.text() == "Wisdom [WIS]"
    wisdom_action.trigger()
    assert view.formula_edit.text() == "[WIS]"
    assert view.values.horizontalHeaderItem(0).text() == "Level"
    assert not view.values.verticalHeader().isVisible()
    assert view.values.horizontalHeader().sectionResizeMode(0).name == "Stretch"
    assert not view.preview.verticalHeader().isVisible()
    assert view.preview.horizontalHeader().minimumSectionSize() == 70
    assert not view.preview.horizontalHeader().stretchLastSection()
    assert view.preview.horizontalScrollMode().name == "ScrollPerPixel"
    assert view.preview.columnWidth(2) > view.preview.columnWidth(0)
    view.close()


def test_formula_edit_refreshes_preview_table():
    QApplication.instance() or QApplication([])
    model = ProgressionEditorModel({"features": []})
    model.add_column("bonus", "Bonus")
    view = ProgressionEditorView(model)
    view._selected_key = "bonus"
    view._load_editor("bonus")
    view.method.setCurrentText("formula")
    view.formula_edit.setText("2 * [level]")
    assert view.values.rowCount() == 0
    preview_column = list(view._preview_keys()).index("bonus")
    assert view.preview.item(0, preview_column).text() == "2"
    view.formula_edit.setText("2 * [level] +")
    assert view.formula_edit.property("formulaInvalid") is True
    assert "valid arithmetic" in view.validation_label.text()
    view.close()


def test_formula_change_updates_preview_without_level_rows():
    QApplication.instance() or QApplication([])
    model = ProgressionEditorModel({})
    model.add_column("bonus", "Bonus")
    model.update_column("bonus", method="formula", formula="[level]")
    view = ProgressionEditorView(model)
    view._selected_key = "bonus"
    view._load_editor("bonus")
    assert view.values.rowCount() == 0
    view.formula_edit.setText("2 * [level]")
    preview_column = list(view._preview_keys()).index("bonus")
    assert view.preview.item(0, preview_column).text() == "2"
    view.close()


def test_table_values_override_formula_output_at_explicit_levels():
    rows = class_progression_rows({
        "features": [],
        "presentation_progression": {
            "columns": [{
                "key": "bonus",
                "label": "Bonus",
                "method": "formula",
                "formula": "[level]",
                "values": {"3": "+9"},
            }],
        },
    })
    assert rows[1]["bonus"] == 2
    assert rows[2]["bonus"] == "+9"
    assert rows[3]["bonus"] == 4


def test_formula_blank_level_override_does_not_carry_forward():
    rows = class_progression_rows({
        "features": [],
        "presentation_progression": {
            "columns": [{
                "key": "ki_points",
                "label": "Ki Points",
                "method": "formula",
                "formula": "[level] + 1",
                "values": {"1": ""},
            }],
        },
    })
    assert rows[0]["ki_points"] == "-"
    assert rows[1]["ki_points"] == 3


def test_formula_columns_do_not_require_or_seed_level_one():
    model = ProgressionEditorModel({})
    model.add_column("bonus", "Bonus")
    model.update_column("bonus", method="formula", formula="[level]")
    model.update_column("bonus", recharge_values={"5": "dawn"})
    accepted = model.apply()
    assert accepted["columns"][0]["values"] == {}
    assert accepted["columns"][0]["recharge_values"] == {"5": "dawn"}


def test_custom_rows_and_markdown_use_saved_order_labels_and_visibility():
    payload = {
        "name": "Custom Class",
        "presentation_progression": {
            "columns": [
                {"key": "reset", "label": "Reset", "values": {"1": "Dawn"}},
                {"key": "charges", "label": "Charges", "values": {"1": "1d6"}},
                {"key": "hidden", "label": "Hidden", "values": {"1": "no"}, "visible": False},
            ],
        },
        "features": [],
    }
    rows = class_progression_rows(payload)
    assert list(rows[0]) == ["level", "proficiency_bonus", "features", "reset", "charges"]
    assert rows[0]["reset"] == "Dawn"
    assert "Hidden" not in render_entity_markdown(
        SimpleNamespace(
            uid="class-1", name="Custom Class", entity_type="class",
            source_namespace="homebrew", payload=payload, source_metadata={},
        )
    )
    rendered = render_entity_markdown(
        SimpleNamespace(
            uid="class-1", name="Custom Class", entity_type="class",
            source_namespace="homebrew", payload=payload, source_metadata={},
        )
    )
    assert "| Level | Proficiency Bonus | Features | Reset | Charges |" in rendered


def test_unconfigured_class_keeps_default_progression():
    rows = class_progression_rows({"features": [{"level": 1, "name": "Spellcasting"}]})
    assert rows[0]["proficiency_bonus"] == "+2"
    assert rows[0]["features"] == "Spellcasting"


def test_generated_columns_are_fixed_and_custom_values_forward_fill():
    model = ProgressionEditorModel({})
    model.add_column("Uses")
    model.update_column("uses", values={"1": 2, "5": 4})
    with pytest.raises(ValueError, match="cannot be removed"):
        model.remove_column("level")
    with pytest.raises(ValueError, match="must remain first"):
        model.reorder_columns(("uses", "level", "proficiency_bonus", "features"))
    rows = custom_progression_rows({"presentation_progression": model.configuration})
    assert rows[0]["level"] == "1st"
    assert rows[0]["uses"] == 2
    assert rows[3]["uses"] == 2
    assert rows[4]["uses"] == 4


def test_custom_column_can_move_before_features_and_level_editor_ignores_output_visibility():
    model = ProgressionEditorModel({})
    model.add_column("Uses")
    model.move_column("uses", "left")
    assert [column["key"] for column in model.editor_columns] == [
        "level", "proficiency_bonus", "uses", "features",
    ]

    QApplication.instance() or QApplication([])
    view = ProgressionEditorView(model)
    view._selected_key = "uses"
    view._load_editor("uses")
    view.show_value.setChecked(False)
    assert view.values.horizontalHeaderItem(0).text() == "Level"
    assert view.values.horizontalHeaderItem(1).text() == "Value"
    view.close()


def test_formula_and_visibility_modes_render_expected_values():
    payload = {
        "features": [],
        "presentation_progression": {
            "columns": [
                {"key": "bonus", "label": "Bonus", "method": "formula", "formula": "proficiency + level"},
                {"key": "charges", "label": "Charges", "values": {"1": 1, "3": 2}, "visibility_mode": "changes"},
                {"key": "resource", "label": "Resource", "values": {"1": "A"}, "visibility_mode": "both"},
            ]
        },
    }
    rows = class_progression_rows(payload)
    assert rows[0]["bonus"] == 3
    assert rows[1]["bonus"] == 4
    assert rows[0]["charges"] == 1
    assert rows[1]["charges"] == ""
    assert rows[0]["resource_values"] == "A"


def test_formula_uses_bedmas_parentheses_and_bracket_variables():
    payload = {
        "features": [],
        "presentation_progression": {
            "columns": [{
                "key": "bonus",
                "label": "Bonus",
                "method": "formula",
                "formula": "2 * [level] + [proficiency_bonus]",
            }, {
                "key": "grouped",
                "label": "Grouped",
                "method": "formula",
                "formula": "([level] + 2) * 3",
            }],
        },
    }
    rows = class_progression_rows(payload)
    assert rows[0]["bonus"] == 4
    assert rows[1]["bonus"] == 6
    assert rows[0]["grouped"] == 9


def test_formula_validation_rejects_invalid_syntax_and_unsafe_nodes():
    validate_formula("2 * [level] + ([proficiency_bonus] - 1)")
    with pytest.raises(ValueError, match="valid arithmetic"):
        validate_formula("2 * [level] +")
    with pytest.raises(ValueError, match="valid arithmetic"):
        validate_formula("__import__('os').system('bad')")


def test_progression_validation_checks_formula_and_recharge_levels():
    model = ProgressionEditorModel({})
    model.add_column("resource", "Resource")
    model.update_column("resource", method="formula", formula="2 * [level] +")
    with pytest.raises(ValueError, match="valid arithmetic"):
        model.apply()

    model.update_column("resource", method="formula", formula="2 * [level]")
    model.update_column("resource", recharge_values={"21": "dawn"})
    with pytest.raises(ValueError, match="Recharge values"):
        model.apply()


def test_resource_values_support_roll_strings_objects_and_recharge_columns():
    payload = {
        "features": [],
        "presentation_progression": {
            "columns": [{
                "key": "uses",
                "label": "Uses",
                "values": {
                    "1": "2d8",
                    "5": {"dice_roll": {"count": 1, "dice": 6, "modifier": 3}},
                },
                "recharge_values": {"1": "short_rest", "5": "dawn"},
            }]
        },
    }
    rows = class_progression_rows(payload)
    assert rows[0]["uses"] == "2d8"
    assert rows[0]["uses_recharge"] == "short_rest"
    assert rows[4]["uses"] == "1d6+3"
    assert rows[4]["uses_recharge"] == "dawn"


def test_controller_updates_only_progression_payload():
    row = SimpleNamespace(
        uid="class-1", entity_type="class", name="Wizard",
        source_identity="source:wizard", source_namespace="homebrew",
        payload={"name": "Wizard", "features": [{"name": "Spellcasting"}]},
        source_metadata={"xml_source": {"name": "Wizard"}}, provenance="test",
    )

    class Store:
        def __init__(self):
            self.records = []

        def commit_records(self, records, *, duplicate_policy):
            assert duplicate_policy == "replace"
            self.records.extend(records)

    store = Store()
    controller = object.__new__(ProjectController)
    controller.project_file = None
    controller.resolve_entity = lambda _uid: row
    controller.entity_database_store = lambda _namespace: store
    configuration = {"columns": [{"key": "charges", "label": "Charges", "values": {"1": "1d6"}}]}

    controller.update_class_progression("class-1", configuration)
    updated = store.records[-1]

    assert updated.payload["features"] == row.payload["features"]
    assert updated.payload["presentation_progression"]["columns"][0]["key"] == "charges"
    assert row.payload == {"name": "Wizard", "features": [{"name": "Spellcasting"}]}


def test_controller_restores_previous_record_when_project_save_fails():
    original_payload = {"name": "Wizard", "features": []}
    row = SimpleNamespace(
        uid="class-1", entity_type="class", name="Wizard",
        source_identity="source:wizard", source_namespace="homebrew",
        payload=original_payload, source_metadata={}, provenance="test",
    )

    class Store:
        def __init__(self):
            self.records = []

        def commit_records(self, records, *, duplicate_policy):
            self.records.append(records[0])

    store = Store()
    controller = object.__new__(ProjectController)
    controller.project_file = "project.json"
    controller.resolve_entity = lambda _uid: row
    controller.entity_database_store = lambda _namespace: store
    controller.save_project = lambda: (_ for _ in ()).throw(RuntimeError("disk full"))

    with pytest.raises(RuntimeError, match="disk full"):
        controller.update_class_progression(
            "class-1",
            {"columns": [{"key": "charges", "label": "Charges", "values": {}}]},
        )

    assert store.records[-1].payload == original_payload