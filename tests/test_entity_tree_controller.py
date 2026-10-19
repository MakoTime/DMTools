from types import SimpleNamespace

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QMdiArea,
    QTabWidget,
    QWidget,
)

from application.controllers.entity_controller import EntityTreeController
from application.display_space import DisplaySpaceController, mdi_content_widget
from application.homebrew import HomebrewDraft
from components.tree.model import TreeModel, TreeNode
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


def test_homebrew_editors_open_in_mdi_not_workspace_tabs():
    app = qt_app()
    mdi_area = QMdiArea()
    mdi_area.setObjectName("sceneViewer")
    workspace_tabs = QTabWidget()
    workspace_tabs.addTab(mdi_area, "Scene")
    display_space = DisplaySpaceController(
        mdi_area,
        workspace_tabs=workspace_tabs,
    )
    parent = SimpleNamespace(
        sceneViewer=mdi_area,
        display_space_controller=display_space,
    )
    controller = EntityTreeController(
        FakeTreeView(),
        FakeProjectController(),
        FakeImportController(),
        parent=parent,
    )

    entity = SimpleNamespace(
        uid="item-1",
        name="Test Item",
        entity_type="item",
        source_namespace="compendium",
        payload={"name": "Test Item", "type": "G", "weight": 1},
    )
    edit_window = controller._open_homebrew_editor(entity)
    new_window = controller._open_new_homebrew_editor(
        HomebrewDraft.blank("item")
    )
    app.processEvents()

    assert edit_window in mdi_area.subWindowList()
    assert new_window in mdi_area.subWindowList()
    assert workspace_tabs.count() == 1
    assert not edit_window.isMaximized()
    assert not new_window.isMaximized()
    mdi_area.closeAllSubWindows()
    app.processEvents()
    workspace_tabs.close()


def test_class_progression_editor_uses_the_shared_mdi_frame():
    app = qt_app()
    mdi_area = QMdiArea()
    mdi_area.setObjectName("sceneViewer")
    workspace_tabs = QTabWidget()
    workspace_tabs.addTab(mdi_area, "Scene")
    display_space = DisplaySpaceController(
        mdi_area,
        workspace_tabs=workspace_tabs,
    )
    parent = SimpleNamespace(
        sceneViewer=mdi_area,
        display_space_controller=display_space,
    )
    controller = EntityTreeController(
        FakeTreeView(),
        FakeProjectController(),
        FakeImportController(),
        parent=parent,
    )
    entity = SimpleNamespace(uid="class-1", payload={})

    window = controller._open_class_progression_editor(entity)
    app.processEvents()

    assert window in mdi_area.subWindowList()
    assert getattr(window.widget(), "mdi_window_frame", False)
    assert workspace_tabs.count() == 1
    window.close()
    app.processEvents()
    workspace_tabs.close()


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


def test_homebrew_entity_menu_offers_confirmed_delete(monkeypatch):
    qt_app()
    entity = SimpleNamespace(
        uid="homebrew-spell-1", name="Test Spell", source_namespace="homebrew"
    )
    project = FakeProjectController()
    project.resolve_entity = lambda uid: entity
    deleted = []
    project.delete_homebrew_entity = deleted.append
    monkeypatch.setattr(
        "application.controllers.entity_controller.QMessageBox.question",
        lambda *args: QMessageBox.StandardButton.Yes,
    )
    controller = EntityTreeController(
        FakeTreeView(), project, FakeImportController()
    )
    node = SimpleNamespace(
        node_type="entity",
        namespace="homebrew",
        entity_uid=entity.uid,
    )

    menu = controller.create_context_menu(node)

    assert action_labels(menu) == ["Edit Homebrew", "Delete Homebrew"]
    menu.actions()[1].trigger()
    assert deleted == [entity.uid]


def test_add_from_source_routes_selected_entity_to_homebrew_clone():
    qt_app()
    source = SimpleNamespace(uid="compendium-spell-1")
    store = SimpleNamespace(block=SimpleNamespace(guid="compendium-database"))
    project = FakeProjectController()
    project.entity_database_store = lambda namespace: store
    dialog_requests = []

    def create_dialog(_store, entity_type, **kwargs):
        dialog_requests.append((entity_type, kwargs))
        return SimpleNamespace(
            model=SimpleNamespace(rows=()),
            exec=lambda: QDialog.DialogCode.Rejected,
        )

    controller = EntityTreeController(
        FakeTreeView(),
        project,
        FakeImportController(),
        search_dialog_factory=create_dialog,
    )
    cloned = []
    controller._clone_homebrew_source = lambda uid: cloned.append(uid)
    normal_search = SimpleNamespace(
        showNormal=lambda: None,
        raise_=lambda: None,
        activateWindow=lambda: None,
    )
    controller._search_windows[compendium_root.category("spell").uid] = normal_search

    controller.add_from_source(homebrew_root.category("spell"))

    entity_type, kwargs = dialog_requests[0]
    assert entity_type == "spell"
    assert kwargs["open_action_text"] == "Add to Homebrew"
    assert kwargs["on_open"](source) is None
    assert cloned == [source.uid]


def test_weapon_group_related_entities_link_groups_to_subgroups_and_types():
    qt_app()
    controller = EntityTreeController(
        FakeTreeView(), FakeProjectController(), FakeImportController()
    )

    simple_links = controller._rule_related_entities("weapons-groups", "simple")
    simple_melee_links = controller._rule_related_entities(
        "weapons-groups", "simple_melee"
    )

    assert simple_links == (
        ("Simple Melee Weapons", "dmtools://rule/weapons-groups/simple_melee"),
        ("Simple Ranged Weapons", "dmtools://rule/weapons-groups/simple_ranged"),
    )
    assert ("Club", "dmtools://rule/weapons-types/club") in simple_melee_links
    assert ("Crossbow Light", "dmtools://rule/weapons-types/crossbow_light") not in simple_melee_links


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


def test_reveal_entity_expands_ancestors_and_selects_node():
    qt_app()

    root = TreeNode("Compendium")
    category = TreeNode("Spells")
    entity_node = TreeNode("Fireball", uid="node-fireball")
    entity_node.object_uid = "spell-fireball"
    root.add_child(category)
    category.add_child(entity_node)
    tree_model = TreeModel([root])

    class RevealTreeView(FakeTreeView):
        def __init__(self):
            super().__init__()
            self.expanded = []
            self.current = None
            self.scrolled = None

        def model(self):
            return tree_model

        def expand(self, index):
            self.expanded.append(index.internalPointer())

        def setCurrentIndex(self, index):
            self.current = index

        def scrollTo(self, index):
            self.scrolled = index

    tree = RevealTreeView()
    controller = EntityTreeController(
        tree, FakeProjectController(), FakeImportController()
    )

    index = controller.reveal_entity("spell-fireball")

    assert index.internalPointer() is entity_node
    assert tree.expanded == [root, category]
    assert tree.current == index
    assert tree.scrolled == index


def test_search_is_hosted_as_non_modal_mdi_child():
    qt_app()
    mdi_area = QMdiArea()
    parent = QWidget()
    parent.sceneViewer = mdi_area
    parent.workspaceTabs = QTabWidget()
    parent.workspaceTabs.addTab(mdi_area, "Scene")
    parent.display_space_controller = DisplaySpaceController(
        mdi_area,
        parent=parent,
        workspace_tabs=parent.workspaceTabs,
    )
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
    assert mdi_content_widget(search_window).isModal() is False
    assert getattr(search_window.widget(), "mdi_window_frame", False)
    assert parent.workspaceTabs.count() == 1
    assert len(mdi_area.subWindowList()) == 1
    assert controller.search(homebrew_root.category("spell")) is search_window
    search_window.close()
    assert controller._search_windows == {}
    parent.close()


def test_rule_view_is_hosted_as_reusable_mdi_child():
    qt_app()
    mdi_area = QMdiArea()
    parent = QWidget()
    parent.sceneViewer = mdi_area
    parent.workspaceTabs = QTabWidget()
    parent.workspaceTabs.addTab(mdi_area, "Scene")
    parent.display_space_controller = DisplaySpaceController(
        mdi_area,
        parent=parent,
        workspace_tabs=parent.workspaceTabs,
    )
    controller = EntityTreeController(
        FakeTreeView(), FakeProjectController(), FakeImportController(), parent=parent
    )
    node = compendium_root.rules.category("conditions").children[0]

    first = controller._open_rule(node)
    window = mdi_area.subWindowList()[0]
    assert first is mdi_content_widget(window)
    assert getattr(window.widget(), "mdi_window_frame", False)
    assert parent.workspaceTabs.count() == 1
    assert first.isModal() is False
    assert "blinded" in first.windowTitle().lower()
    assert controller._open_rule(node) is first
    assert len(mdi_area.subWindowList()) == 1
    first.button_box.button(QDialogButtonBox.StandardButton.Close).click()
    qt_app().processEvents()
    assert mdi_area.subWindowList() == []
    parent.close()