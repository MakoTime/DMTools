from PySide6.QtWidgets import QApplication

from dialog.entity_detail.factory import create_entity_detail_mdi_view


def test_entity_detail_factory_creates_modeless_widget_without_copying_entity():
    QApplication.instance() or QApplication([])
    entity = type(
        "Entity",
        (),
        {
            "name": "Backpack",
            "entity_type": "item",
            "source_namespace": "compendium",
            "uid": "item-backpack",
            "payload": {"weight": 5},
        },
    )()

    view = create_entity_detail_mdi_view(entity)

    assert view.windowTitle() == "Backpack"
    assert view.model.entity is entity
    assert view.isModal() is False
    view.close()