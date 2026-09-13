from PySide6.QtWidgets import QApplication, QMdiArea

from application.entity_references import EntityReference
from dialog.entity_detail.controller import EntityInspectionController


def test_entity_inspection_controller_reuses_mdi_view_for_uid():
    QApplication.instance() or QApplication([])
    entity_fields = {
        "name": "Entity",
        "entity_type": "item",
        "source_namespace": "compendium",
        "payload": {},
    }
    first = type("Entity", (), {**entity_fields, "uid": "first"})()
    second = type("Entity", (), {**entity_fields, "uid": "second"})()

    class ProjectController:
        def resolve_entity_reference(self, reference):
            return {"first": first, "second": second}[reference.target_uid]

        def resolve_entity(self, uid):
            return {"first": first, "second": second}[uid]

    mdi_area = QMdiArea()
    controller = EntityInspectionController(ProjectController(), mdi_area)
    reference = EntityReference("second", "item", "compendium")

    first_view = controller.open(reference, origin_uid="first")
    second_view = controller.open(reference)

    assert first_view is second_view
    browser = controller._windows["second"].widget().browser
    assert "Entity" in browser.toHtml()
    assert ".dmtools-inspection" in browser.document().defaultStyleSheet()
    assert controller._windows["second"].widget().model._entity is None
    second.name = "Updated Entity"
    controller.refresh("second")
    assert "Updated Entity" in browser.toHtml()
    assert controller.open_link("dmtools://entity/second") is second_view
    for link in ("https://example.test/entity/second", "dmtools://entity/"):
        try:
            controller.open_link(link)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid link to fail: {link}")
    assert len(controller._windows) == 1
    mdi_area.closeAllSubWindows()