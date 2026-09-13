from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QMdiArea

from application.entity_references import EntityReference
from dialog.entity_detail.controller import EntityInspectionController
from dialog.homebrew.factory import create_homebrew_mdi_view


def qt_app():
    return QApplication.instance() or QApplication([])


def entity(uid, name, entity_type="item", namespace="compendium"):
    return SimpleNamespace(
        uid=uid,
        name=name,
        entity_type=entity_type,
        source_namespace=namespace,
        payload={"name": name, "type": "G", "weight": 1},
        source_metadata={},
    )


def test_mdi_entity_link_homebrew_cancel_and_shutdown_smoke():
    qt_app()
    source = entity("item-source", "Source")
    target = entity("spell-target", "Target", entity_type="spell")
    resolved = {source.uid: source, target.uid: target}

    class Controller:
        def resolve_entity(self, uid):
            return resolved[uid]

        def resolve_entity_reference(self, reference):
            return resolved[reference.target_uid]

    mdi_area = QMdiArea()
    inspection = EntityInspectionController(Controller(), mdi_area)

    source_view = inspection.display(source)
    opened_target = inspection.open_link("dmtools://entity/spell-target")
    target_view = inspection._windows[target.uid].widget()
    assert opened_target is target
    assert source_view is not target_view
    assert inspection.open(EntityReference(target.uid, "spell", "compendium")) is target
    assert inspection.back() is source
    assert inspection.display(target) is target_view

    draft = SimpleNamespace(
        entity_type="item",
        name="Draft Pack",
        payload={"name": "Draft Pack", "type": "G", "weight": 1, "value": 2},
        description="",
        draft_state="draft",
        published=False,
        version=1,
        source_entity_uid=None,
        entity_uid=None,
        source_identity=None,
    )
    editor = create_homebrew_mdi_view("item", draft, parent=mdi_area)
    subwindow = mdi_area.addSubWindow(editor)
    subwindow.show()
    editor.cancel_button.click()

    assert editor.model is None
    mdi_area.closeAllSubWindows()
    assert not mdi_area.subWindowList()
