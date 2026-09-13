from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from application.entity_database import EntityDatabaseStore
from dialog.entity_search import EntitySearchModel, EntitySearchView


class FakeStore:
    FIELD_PROJECTIONS = {
        "spell": {"name": "name", "level": "level"},
    }

    def __init__(self):
        self.calls = []
        self.rows = (
            SimpleNamespace(
                uid="spell-1",
                name="Shield",
                entity_type="spell",
                source_namespace="compendium",
            ),
        )

    def query(self, entity_type, **kwargs):
        self.calls.append((entity_type, kwargs))
        return self.rows


def qt_app():
    return QApplication.instance() or QApplication([])


def test_search_model_builds_category_aware_criteria_and_executes_them():
    store = FakeStore()
    model = EntitySearchModel(store, "spell")

    model.add_criterion("name", "contains", "shield")
    model.add_criterion("level", "eq", "1")
    rows = model.execute()

    assert model.fields == ("name", "level")
    assert rows == store.rows
    assert store.calls[-1] == (
        "spell",
        {"criteria": (("name", "contains", "shield"), ("level", "eq", 1))},
    )
    with pytest.raises(ValueError, match="valid value for level"):
        model.add_criterion("level", "eq", "first")


def test_search_view_adds_parameter_and_refreshes_results():
    qt_app()
    store = FakeStore()
    view = EntitySearchView(EntitySearchModel(store, "spell"))
    view.field_combo.setCurrentIndex(view.field_combo.findData("level"))
    view.operator_combo.setCurrentIndex(view.operator_combo.findData("eq"))
    view.value_edit.setText("1")

    view.add_parameter()

    assert view.parameter_list.count() == 1
    assert view.parameter_list.item(0).text() == "Level equals 1"
    assert view.results_table.model().rowCount() == 1
    assert view.status_label.text() == "1 result(s)"


def test_search_view_opens_the_selected_result():
    qt_app()
    store = FakeStore()
    entity = store.rows[0]
    opened = []

    class ProjectController:
        @staticmethod
        def resolve_entity_reference(reference):
            assert reference.target_uid == entity.uid
            return entity

    view = EntitySearchView(
        EntitySearchModel(store, "spell"),
        project_controller=ProjectController(),
        on_open=opened.append,
        origin_uid="spell-category",
    )
    view.results_table.selectRow(0)

    view.model.add_criterion("name", "contains", "shield")
    assert view.open_selected_entity() is entity
    assert opened == [entity]
    assert view.model.criteria[0].value == "shield"


def test_fixed_enum_parameter_accepts_multiple_selected_values():
    qt_app()
    store = FakeStore()
    store.FIELD_PROJECTIONS = EntityDatabaseStore.FIELD_PROJECTIONS
    store.QUERY_FIELDS = EntityDatabaseStore.QUERY_FIELDS
    model = EntitySearchModel(store, "item")
    view = EntitySearchView(model)
    view.field_combo.setCurrentIndex(view.field_combo.findData("rarity"))
    view.value_combo.set_checked_values(("rare", "legendary"))

    criterion = view.add_parameter()

    assert criterion.operator == "any_of"
    assert criterion.value == ("rare", "legendary")
    assert view.parameter_list.item(0).text() == (
        "Rarity is any of Rare, Legendary"
    )