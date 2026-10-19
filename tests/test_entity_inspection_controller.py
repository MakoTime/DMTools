from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QMdiArea, QTabWidget, QToolButton

from application.display_space import DisplaySpaceController, mdi_content_widget
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
    mdi_area.setObjectName("sceneViewer")
    workspace_tabs = QTabWidget()
    workspace_tabs.addTab(mdi_area, "Scene")
    display_space = DisplaySpaceController(
        mdi_area,
        workspace_tabs=workspace_tabs,
    )
    workspace_tabs.resize(900, 700)
    workspace_tabs.show()
    controller = EntityInspectionController(
        ProjectController(),
        mdi_area,
        display_space_controller=display_space,
    )
    reference = EntityReference("second", "item", "compendium")

    first_view = controller.open(reference, origin_uid="first")
    second_view = controller.open(reference)

    assert first_view is second_view
    browser = mdi_content_widget(controller._windows["second"]).browser
    assert "Entity" in browser.toHtml()
    assert ".dmtools-inspection" in browser.document().defaultStyleSheet()
    assert mdi_content_widget(controller._windows["second"]).model._entity is None
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
    assert workspace_tabs.count() == 1
    assert mdi_area.subWindowList() == [controller._windows["second"]]
    old_window = controller._windows["second"]
    maximize_button = old_window.findChild(QToolButton, "mdiMaximizeButton")
    assert maximize_button is not None
    maximize_button.click()
    QApplication.processEvents()
    assert workspace_tabs.count() == 2
    assert workspace_tabs.tabText(1) == "Updated Entity"
    assert mdi_area.viewMode() == QMdiArea.ViewMode.SubWindowView
    restore_button = workspace_tabs.tabBar().tabButton(
        1, workspace_tabs.tabBar().ButtonPosition.LeftSide
    )
    assert restore_button is not None
    restore_button.click()
    QApplication.processEvents()
    assert workspace_tabs.count() == 1
    assert mdi_area.viewMode() == QMdiArea.ViewMode.SubWindowView
    assert old_window in mdi_area.subWindowList()
    assert browser.isVisible()
    old_window.close()
    QApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    reopened_view = controller.display(second)
    assert reopened_view is not second_view
    assert controller._windows["second"] is not old_window
    controller._windows["second"].close()
    workspace_tabs.close()