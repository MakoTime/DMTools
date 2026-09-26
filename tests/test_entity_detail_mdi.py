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


def test_entity_detail_view_shows_raw_api_source_alongside_formatted_entity():
    QApplication.instance() or QApplication([])
    entity = type(
        "Entity",
        (),
        {
            "name": "Backpack",
            "entity_type": "item",
            "source_namespace": "compendium",
            "uid": "item-backpack",
            "payload": {"name": "Backpack", "weight": 5},
            "source_metadata": {
                "api_source": {
                    "name": "Backpack",
                    "equipment_category": {"name": "Adventuring Gear"},
                    "weight": 5,
                }
            },
        },
    )()

    view = create_entity_detail_mdi_view(entity)
    view.show()
    QApplication.processEvents()

    assert view.raw_view.isReadOnly()
    assert '"equipment_category"' in view.raw_view.toPlainText()
    assert "Backpack" in view.browser.toHtml()
    assert view.raw_view.isVisible()

    view.raw_button.click()

    assert not view.raw_view.isVisible()
    view.close()


def test_entity_detail_view_refreshes_raw_source_and_formatted_entity():
    QApplication.instance() or QApplication([])
    first = type(
        "Entity",
        (),
        {
            "name": "Backpack",
            "entity_type": "item",
            "source_namespace": "compendium",
            "uid": "item-backpack",
            "payload": {"name": "Backpack"},
            "source_metadata": {"api_source": {"name": "Backpack"}},
        },
    )()
    second = type(
        "Entity",
        (),
        {
            "name": "Rope",
            "entity_type": "item",
            "source_namespace": "compendium",
            "uid": "item-rope",
            "payload": {"name": "Rope"},
            "source_metadata": {"api_source": {"name": "Rope", "length": 60}},
        },
    )()
    view = create_entity_detail_mdi_view(first)

    view.refresh_entity(second)

    assert view.windowTitle() == "Rope"
    assert '"length": 60' in view.raw_view.toPlainText()
    assert "Rope" in view.browser.toHtml()
    view.close()