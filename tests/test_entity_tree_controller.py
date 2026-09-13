from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QDialog, QMdiArea, QWidget

from application.controllers.entity_controller import EntityTreeController
from components.tree.roots.entity_roots import compendium_root, homebrew_root


def qt_app():
    return QApplication.instance() or QApplication([])


class FakeTreeView:
    def __init__(self):
        self.factories = []

    def add_context_menu_factory(self, factory):
        self.factories.append(factory)


class FakeProjectController:
    def __init__(self):
        self.refresh_count = 0

    def refresh_project_tree(self):
        self.refresh_count += 1


class FakeImportController:
    def __init__(self):
        self.calls = []

    def import_xml(self):
        self.calls.append("xml")

    def import_json(self):
        self.calls.append("json")


def action_labels(menu):
    return [action.text() for action in menu.actions()]


def test_entity_root_menus_route_import_and_refresh_commands():
    qt_app()
    tree = FakeTreeView()
    project = FakeProjectController()
    imports = FakeImportController()
    controller = EntityTreeController(tree, project, imports)

    compendium_menu = controller.create_context_menu(compendium_root)
    homebrew_menu = controller.create_context_menu(homebrew_root)

    assert tree.factories == [controller._create_context_menu_for_index]
    assert action_labels(compendium_menu) == [
        "Import from XML",
        "Import from JSON",
        "Refresh",
    ]
    assert action_labels(homebrew_menu) == ["Refresh"]
    compendium_menu.actions()[0].trigger()
    compendium_menu.actions()[1].trigger()
    compendium_menu.actions()[2].trigger()
    assert imports.calls == ["xml", "json"]
    assert project.refresh_count == 1


def test_category_menus_offer_only_applicable_quick_queries():
    qt_app()
    controller = EntityTreeController(
        FakeTreeView(), FakeProjectController(), FakeImportController()
    )

    item_menu = controller.create_context_menu(compendium_root.category("item"))
    race_menu = controller.create_context_menu(compendium_root.category("race"))

    assert action_labels(item_menu) == [
        "Search",
        "Items by Weight",
        "Refresh",
    ]
    assert action_labels(race_menu) == ["Search", "Refresh"]


def test_category_search_executes_against_its_namespace_and_opens_results():
    qt_app()
    rows = (SimpleNamespace(uid="entity-1"),)
    store = SimpleNamespace(block=SimpleNamespace(guid="database"))
    project = FakeProjectController()
    project.entity_database_store = lambda namespace: (
        store if namespace == "homebrew" else None
    )
    opened = []
    details = []
    dialog_requests = []

    def create_dialog(_store, entity_type, **kwargs):
        dialog_requests.append((_store, entity_type, kwargs))
        return SimpleNamespace(
            model=SimpleNamespace(rows=rows),
            exec=lambda: QDialog.DialogCode.Accepted,
        )

    def create_detail(entity, parent=None):
        detail = SimpleNamespace(
            entity=entity,
            parent=parent,
            exec=lambda: details.append(entity),
        )
        return detail

    controller = EntityTreeController(
        FakeTreeView(),
        project,
        FakeImportController(),
        search_dialog_factory=create_dialog,
        detail_dialog_factory=create_detail,
        results_factory=lambda results, **kwargs: opened.append((results, kwargs)),
    )

    result = controller.search(homebrew_root.category("spell"))

    assert result is None
    assert dialog_requests[0][0:2] == (store, "spell")
    assert dialog_requests[0][2]["project_controller"] is project
    assert dialog_requests[0][2]["origin_uid"] == "dmtools-homebrew-spell-category"
    assert callable(dialog_requests[0][2]["on_open"])
    assert opened[0][0] == rows
    assert opened[0][1]["origin_uid"] == "dmtools-homebrew-spell-category"
    opened[0][1]["on_open"](rows[0])
    assert details == [rows[0]]


def test_invalid_quick_query_input_reports_error_without_opening_results():
    qt_app()
    errors = []
    opened = []
    controller = EntityTreeController(
        FakeTreeView(),
        FakeProjectController(),
        FakeImportController(),
        input_provider=lambda title, prompt: ("not-a-number", True),
        results_factory=lambda *args, **kwargs: opened.append(args),
        error_reporter=errors.append,
    )

    result = controller.run_builtin(
        compendium_root.category("item"), "item_weight", "Maximum weight"
    )

    assert result is None
    assert errors
    assert opened == []


def test_entity_tree_activation_resolves_uid_and_opens_entity():
    qt_app()
    entity = SimpleNamespace(uid="entity-1", name="Shield")
    opened = []
    project = FakeProjectController()
    project.resolve_entity = lambda uid: entity if uid == entity.uid else None
    controller = EntityTreeController(
        FakeTreeView(),
        project,
        FakeImportController(),
        inspection_controller=SimpleNamespace(display=opened.append),
    )
    node = SimpleNamespace(node_type="entity", entity_uid=entity.uid)
    index = SimpleNamespace(internalPointer=lambda: node)

    assert controller._open_tree_entity(index) is None
    assert opened == [entity]


def test_search_is_hosted_as_non_modal_mdi_child():
    qt_app()
    mdi_area = QMdiArea()
    parent = QWidget()
    parent.sceneViewer = mdi_area
    project = FakeProjectController()
    project.entity_database_store = lambda namespace: SimpleNamespace(
        FIELD_PROJECTIONS={"spell": {"name": "name"}},
        query=lambda entity_type, **kwargs: (),
    )
    controller = EntityTreeController(
        FakeTreeView(), project, FakeImportController(), parent=parent
    )

    search_window = controller.search(homebrew_root.category("spell"))

    assert search_window in mdi_area.subWindowList()
    assert search_window.widget().isModal() is False
    assert len(mdi_area.subWindowList()) == 1
    assert controller.search(homebrew_root.category("spell")) is search_window
    search_window.close()
    assert controller._search_windows == {}
    parent.close()