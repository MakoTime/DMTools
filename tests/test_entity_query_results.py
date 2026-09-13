from dataclasses import replace
from types import SimpleNamespace

from projectfoundry import ArtifactStore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from application.imports import EntityImportService
from application.project_controller import ProjectController
from dialog.base.widget_editor import WidgetEditorView
from dialog.entity_query_results import (
    EntityQueryResultsModel,
    create_entity_query_results,
)


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def qt_app():
    return QApplication.instance() or QApplication([])


def query_rows(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    original = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    second = replace(
        original,
        uid="second-item",
        source_identity="rules:item:second",
        display_name="Abacus",
        payload={**original.payload, "name": "Abacus"},
    )
    controller.commit_imported_entities((original, second))
    return controller, controller.entity_database_store().query("item", operator="all")


def test_query_result_model_retains_uid_after_sort(tmp_path):
    qt_app()
    _, rows = query_rows(tmp_path)
    model = EntityQueryResultsModel(rows)

    model.sort(0, Qt.SortOrder.DescendingOrder)

    first = model.index(0, 0)
    assert model.data(first) == "Backpack"
    assert model.data(first, model.EntityUidRole) == model.entity_row(first).uid


def test_query_result_model_loads_by_uid_and_releases_rows(tmp_path):
    qt_app()
    controller, rows = query_rows(tmp_path)
    loaded_uids = []

    def load_rows(uid):
        loaded_uids.append(uid)
        return rows

    model = EntityQueryResultsModel(
        result_uid="query-uid",
        rows_loader=load_rows,
    )

    assert model.rowCount() == 2
    assert loaded_uids == ["query-uid"]
    model.release_rows()
    assert model.rowCount() == 0

    view = create_entity_query_results(
        project_controller=controller,
        result_uid="query-uid",
        rows_loader=lambda uid: rows,
    )
    assert view.model.rowCount() == 2
    view.close_editor("test")
    assert view.model.rowCount() == 0


def test_query_result_actions_use_selected_canonical_uid(tmp_path):
    qt_app()
    controller, rows = query_rows(tmp_path)
    collection = controller.create_collection("Supplies")
    opened = []
    view = create_entity_query_results(
        rows,
        project_controller=controller,
        collection_uid=collection.guid,
        on_open=opened.append,
    )
    view.model.sort(0, Qt.SortOrder.DescendingOrder)
    view.table.selectRow(0)

    entity = view.open_selected_entity()

    assert isinstance(view, WidgetEditorView)
    assert entity.name == "Backpack"
    assert opened == [entity]
    assert view.add_selected_to_collection() is True
    assert controller.resolve_collection_members(collection.guid) == (entity,)
    assert view.copy_selected_uid() == entity.uid
    assert QApplication.clipboard().text() == entity.uid

    opened.clear()
    index = view.model.index(0, 0)
    assert view.reference_delegate.activate(view.model, index) is True
    assert opened == [entity]


def test_query_result_clone_to_homebrew_preserves_compendium_source(tmp_path):
    qt_app()
    controller, rows = query_rows(tmp_path)
    source = rows[0]
    cloned = []
    view = create_entity_query_results(
        rows,
        project_controller=controller,
        on_clone=cloned.append,
    )
    view.table.selectRow(0)
    source = controller.resolve_entity(view.selected_entity_uid())

    clone = view.clone_selected_to_homebrew()

    assert clone.uid != source.uid
    assert clone.source_namespace == "homebrew"
    assert clone.source_metadata["source_entity_uid"] == source.uid
    assert clone.payload == source.payload
    assert cloned == [clone]
    assert controller.resolve_entity(source.uid).source_namespace == "compendium"


def test_query_result_edit_homebrew_routes_existing_entity(tmp_path):
    qt_app()
    controller, rows = query_rows(tmp_path)
    homebrew = controller.copy_entity_to_homebrew(rows[0].uid)
    homebrew_rows = controller.entity_database_store("homebrew").query(
        "item", operator="all"
    )
    edited = []
    view = create_entity_query_results(
        homebrew_rows,
        project_controller=controller,
        on_edit=edited.append,
    )
    view.table.selectRow(0)

    assert view.edit_selected_homebrew() is None
    assert edited == [homebrew]


def test_query_results_page_boundaries_preserve_uids():
    rows = tuple(
        SimpleNamespace(
            uid=f"item-{index}",
            name=f"Item {index}",
            entity_type="item",
            source_namespace="compendium",
        )
        for index in range(205)
    )
    model = EntityQueryResultsModel(rows)

    assert model.page_count == 3
    assert model.rowCount() == 100
    assert model.entity_uid(model.index(0, 0)) == "item-0"
    assert model.set_page(1) is True
    assert model.entity_uid(model.index(0, 0)) == "item-100"
    assert model.rowCount() == 100
    assert model.set_page(2) is True
    assert model.rowCount() == 5
    assert model.entity_uid(model.index(4, 0)) == "item-204"
    assert model.set_page(99) is False
    assert model.page == 2