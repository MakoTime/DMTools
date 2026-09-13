from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMenu


def entity_context_menu_factory(
    *,
    import_callback: Callable | None = None,
    refresh_callback: Callable | None = None,
    search_callback: Callable | None = None,
    query_callback: Callable | None = None,
):
    """Build a tree-menu contributor for entity roots and categories.

    The callbacks own application workflows.  This factory only translates
    node metadata into actions and passes the selected node through.
    """

    callbacks = {
        "Import": import_callback,
        "Refresh": refresh_callback,
        "Search": search_callback,
        "Query": query_callback,
    }

    def factory(index, parent_menu):
        node = index.internalPointer()
        namespace = getattr(node, "namespace", None)
        node_type = getattr(node, "node_type", None)
        if namespace not in {"compendium", "homebrew"}:
            return None
        if node_type not in {"entity_root", "entity_category"}:
            return None

        menu = QMenu(parent_menu)
        for label, callback in callbacks.items():
            if callback is None:
                continue
            action = menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, callback=callback, node=node: callback(node)
            )
        return menu

    return factory
