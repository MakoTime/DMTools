from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from dialog.base.widget_editor import WidgetEditorView
from dialog.collection import CollectionTableModel, create_collection_table


def qt_app():
    return QApplication.instance() or QApplication([])


class CollectionController:
    def __init__(self):
        self.rows = {
            "item-1": SimpleNamespace(
                uid="item-1",
                name="Backpack",
                entity_type="item",
                source_namespace="compendium",
                payload={"tags": ["gear"], "weight": 5},
            ),
            "spell-1": SimpleNamespace(
                uid="spell-1",
                name="Alarm",
                entity_type="spell",
                source_namespace="homebrew",
                payload={"tags": ["ritual"], "level": 1},
            ),
        }
        self.resolve_calls = []
        self.reordered = None

    def resolve_collection_members(self, collection_uid):
        assert collection_uid == "collection"
        return tuple(self.rows.values())

    def resolve_entity(self, entity_uid):
        self.resolve_calls.append(entity_uid)
        return self.rows[entity_uid]

    def resolve_entity_reference(self, reference):
        entity = self.resolve_entity(reference.target_uid)
        if entity.entity_type != reference.entity_type:
            raise ValueError("Entity reference type does not match its target")
        if entity.source_namespace != reference.source_namespace:
            raise ValueError("Entity reference source namespace does not match its target")
        return entity

    def reorder_collection_entities(self, collection_uid, entity_uids):
        self.reordered = (collection_uid, list(entity_uids))

    def remove_collection_entity(self, collection_uid, entity_uid):
        del self.rows[entity_uid]
        return True


def test_collection_model_resolves_rows_lazily_and_filters_common_fields():
    qt_app()
    controller = CollectionController()
    model = CollectionTableModel(controller, "collection")

    assert controller.resolve_calls == []
    assert model.data(model.index(0, 0)) == "Backpack"
    assert controller.resolve_calls == ["item-1"]

    model.set_filters(source_namespace="homebrew", tag="ritual", text="alarm")

    assert model.rowCount() == 1
    assert model.entity_uid(model.index(0, 0)) == "spell-1"
    model.set_filters(entity_type="item")
    assert model.rowCount() == 1
    assert model.entity_uid(model.index(0, 0)) == "item-1"


def test_collection_model_groups_and_routes_reordering():
    qt_app()
    controller = CollectionController()
    model = CollectionTableModel(controller, "collection")

    model.set_group_by("source_namespace")
    assert model.entity_uid(model.index(0, 0)) == "item-1"
    model.set_group_by(None)
    model.move_member(0, 1)

    assert controller.reordered == ("collection", ["spell-1", "item-1"])


def test_collection_factory_builds_embedded_selectable_view():
    qt_app()
    controller = CollectionController()
    opened = []
    view = create_collection_table(
        "collection", project_controller=controller, on_open=opened.append
    )
    view.table.selectRow(1)

    entity = view.open_selected_entity()

    assert isinstance(view, WidgetEditorView)
    assert entity.uid == "spell-1"
    assert opened == [entity]


def test_collection_model_pages_large_membership_without_losing_uid_order():
    controller = CollectionController()
    controller.rows = {
        f"item-{index}": SimpleNamespace(
            uid=f"item-{index}",
            name=f"Item {index}",
            entity_type="item",
            source_namespace="compendium",
            payload={},
        )
        for index in range(205)
    }
    model = CollectionTableModel(controller, "collection")

    assert model.page_count == 3
    assert model.rowCount() == 100
    assert model.entity_uid(model.index(0, 0)) == "item-0"
    model.set_page(2)
    assert model.rowCount() == 5
    assert model.entity_uid(model.index(4, 0)) == "item-204"