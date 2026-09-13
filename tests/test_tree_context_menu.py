from PySide6.QtWidgets import QApplication

from components.tree.context_menu import entity_context_menu_factory
from components.tree.model import TreeModel
from components.tree.roots.entity_roots import compendium_root


def test_entity_context_menu_exposes_injected_root_actions():
    app = QApplication.instance() or QApplication([])
    model = TreeModel([compendium_root])
    index = model.index(0, 0)
    calls = []
    factory = entity_context_menu_factory(
        import_callback=lambda node: calls.append(("import", node)),
        refresh_callback=lambda node: calls.append(("refresh", node)),
        search_callback=lambda node: calls.append(("search", node)),
        query_callback=lambda node: calls.append(("query", node)),
    )

    menu = factory(index, None)

    assert [action.text() for action in menu.actions()] == [
        "Import",
        "Refresh",
        "Search",
        "Query",
    ]
    menu.actions()[0].trigger()
    assert calls == [("import", compendium_root)]
    menu.deleteLater()
    app.processEvents()


def test_entity_context_menu_ignores_unrelated_nodes():
    from components.tree.model import TreeNode

    model = TreeModel([TreeNode("Other")])
    index = model.index(0, 0)
    factory = entity_context_menu_factory(import_callback=lambda node: None)

    assert factory(index, None) is None
