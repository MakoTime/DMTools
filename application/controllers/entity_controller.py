import inspect

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox, QMdiArea

from application.entity_queries import EntityQueryFactory
from application.rules_catalog import _RULE_DESCRIPTIONS
from dialog.entity_detail import create_entity_detail_dialog
from dialog.entity_detail.controller import EntityInspectionController
from dialog.entity_search import create_entity_search_dialog
from dialog.entity_query_results import create_entity_query_results
from components.tree.roots.entity_roots import compendium_root
from tools.dropdown.factory import create_dropdown_menu


_BUILTIN_QUERY_BY_TYPE = {
    "item": ("Items by Weight", "item_weight", "Maximum weight"),
    "spell": ("Spells by Level", "spell_level", "Spell level"),
    "monster": (
        "Monsters by Challenge Rating",
        "monster_challenge_rating",
        "Challenge rating",
    ),
}


class EntityTreeController:
    """Coordinate entity root and category commands from the project tree."""

    def __init__(
        self,
        tree_view,
        project_controller,
        import_controller,
        parent=None,
        *,
        input_provider=None,
        search_dialog_factory=create_entity_search_dialog,
        detail_dialog_factory=create_entity_detail_dialog,
        results_factory=create_entity_query_results,
        error_reporter=None,
        inspection_controller=None,
    ):
        self.tree_view = tree_view
        self.project_controller = project_controller
        self.import_controller = import_controller
        self.parent = parent
        self.input_provider = input_provider or self._request_text
        self.search_dialog_factory = search_dialog_factory
        self.detail_dialog_factory = detail_dialog_factory
        self.results_factory = results_factory
        self.error_reporter = error_reporter or self._report_error
        self._search_windows = {}
        self._rule_windows = {}
        if hasattr(project_controller, "add_project_replacement_callback"):
            project_controller.add_project_replacement_callback(
                self.close_search_windows
            )
        mdi_area = getattr(parent, "sceneViewer", None)
        self.inspection_controller = inspection_controller
        if self.inspection_controller is None and isinstance(mdi_area, QMdiArea):
            self.inspection_controller = EntityInspectionController(
                project_controller,
                mdi_area,
                on_edit=self._open_homebrew_editor,
                on_rule=self._open_rule_value,
            )
        if hasattr(tree_view, "doubleClicked"):
            tree_view.doubleClicked.connect(self._open_tree_entity)
        tree_view.add_context_menu_factory(self._create_context_menu_for_index)

    def _open_tree_entity(self, index):
        node = index.internalPointer()
        if getattr(node, "node_type", None) == "rules_value":
            return self._open_rule(node)
        if getattr(node, "node_type", None) != "entity":
            return None
        entity_uid = getattr(node, "entity_uid", None)
        if not entity_uid:
            return None
        try:
            entity = self.project_controller.resolve_entity(entity_uid)
        except ValueError:
            self.project_controller.refresh_project_tree()
            return None
        if entity is None:
            return None
        return self._open_entity(entity)

    def _open_rule(self, node):
        return self._open_rule_value(
            node.category_type, node.value, schema_names=node.schema_names
        )

    def _open_rule_value(self, category, value, *, schema_names=()):
        from dialog.rule_detail import create_rule_detail_dialog

        values = _RULE_DESCRIPTIONS.get(category, {})
        if value not in values or value in {"description", "handbook_reference"}:
            raise ValueError(f"Unknown catalog rule value: {category}/{value}")
        window_uid = f"dmtools-compendium-rules-{category}-{value}"
        existing = self._rule_windows.get(window_uid)
        if existing is not None:
            existing.showNormal()
            existing.raise_()
            existing.activateWindow()
            return existing.widget()
        dialog = create_rule_detail_dialog(
            value,
            category,
            schema_names,
            parent=self.parent,
            related_entities=self._rule_related_entities(category, value),
            on_entity_link=self._open_rule_entity_link,
        )
        mdi_area = getattr(self.parent, "sceneViewer", None)
        if mdi_area is None:
            dialog.exec()
            return dialog
        window = mdi_area.addSubWindow(dialog)
        self._rule_windows[window_uid] = window
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.finished.connect(window.close)
        window.setWindowTitle(dialog.windowTitle())
        window.destroyed.connect(
            lambda _object, uid=window_uid: self._rule_windows.pop(uid, None)
        )
        dialog.show()
        window.showNormal()
        window.raise_()
        return dialog

    def _rule_related_entities(self, category, value):
        if category != "weapons-groups":
            return ()
        return tuple(
            (
                weapon_type.replace("_", " ").title(),
                f"dmtools://rule/weapons-types/{weapon_type}",
            )
            for weapon_type, description in _RULE_DESCRIPTIONS[
                "weapons-types"
            ].items()
            if weapon_type not in {"description", "handbook_reference"}
            and f" {value} " in f" {description} "
        )

    def _open_rule_entity_link(self, url):
        if url.startswith("dmtools://rule/"):
            _scheme, _authority, _kind, category, value = url.split("/", 4)
            return self._open_rule_value(category, value)
        entity = self.project_controller.resolve_entity(url.rsplit("/", 1)[-1])
        return self._open_entity(entity) if entity is not None else None

    def _create_context_menu_for_index(self, index, parent):
        return self.create_context_menu(index.internalPointer(), parent)

    def create_context_menu(self, node, parent=None):
        node_type = getattr(node, "node_type", None)
        namespace = getattr(node, "namespace", None)
        options = []
        if node_type == "entity_root":
            if namespace == "compendium":
                options.extend(
                    (
                        ("Import from XML", self.import_controller.import_xml),
                        ("Import from JSON", self.import_controller.import_json),
                    )
                )
            options.append(("Refresh", self.refresh))
        elif node_type == "entity_category":
            if namespace == "homebrew":
                options.extend(
                    (
                        ("Add", lambda: self.add_homebrew_entity(node)),
                        ("Add from Source", lambda: self.add_from_source(node)),
                    )
                )
            options.append(("Search", lambda: self.search(node)))
            builtin = _BUILTIN_QUERY_BY_TYPE.get(node.entity_type)
            if builtin is not None:
                options.append(
                    (
                        builtin[0],
                        lambda: self.run_builtin(node, builtin[1], builtin[2]),
                    )
                )
            options.append(("Refresh", self.refresh))
        elif node_type == "rules_value":
            options.append(("View", lambda: self._open_rule(node)))
        elif node_type == "entity" and namespace == "homebrew":
            options.append(("Edit Homebrew", lambda: self.edit_entity(node)))
        return create_dropdown_menu(options, parent)

    def refresh(self):
        self.project_controller.refresh_project_tree()
        return True

    def search(self, node):
        existing = self._search_windows.get(node.uid)
        if existing is not None:
            existing.showNormal()
            existing.raise_()
            existing.activateWindow()
            return existing
        store = self.project_controller.entity_database_store(node.namespace)
        dialog = self.search_dialog_factory(
            store,
            node.entity_type,
            project_controller=self.project_controller,
            on_open=self._open_entity,
            origin_uid=node.uid,
            parent=self.parent,
            on_close=lambda model, reason, uid=node.uid: self._search_closed(uid),
        )
        if hasattr(dialog, "exec"):
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            return self._open_results(dialog.model.rows, f"{node.name} Search", node.uid)
        mdi_area = getattr(self.parent, "sceneViewer", None)
        if mdi_area is None:
            dialog.show()
            return dialog
        subwindow = mdi_area.addSubWindow(dialog)
        subwindow.setWindowTitle(f"{node.name} Search")
        subwindow.resize(900, 650)
        subwindow.show()
        self._search_windows[node.uid] = subwindow
        return subwindow

    def _search_closed(self, node_uid):
        self._search_windows.pop(node_uid, None)

    def close_search_windows(self):
        windows = tuple(self._search_windows.values())
        self._search_windows.clear()
        for window in windows:
            window.close()

    def edit_entity(self, node):
        entity = self.project_controller.resolve_entity(node.entity_uid)
        return self._open_homebrew_editor(entity)

    def add_homebrew_entity(self, node):
        from application.homebrew import HomebrewDraft

        return self._open_new_homebrew_editor(HomebrewDraft.blank(node.entity_type))

    def add_from_source(self, node):
        source_node = compendium_root.category(node.entity_type)
        return self.search(source_node)

    def run_builtin(self, node, query_key, prompt):
        value, accepted = self.input_provider(node.name, prompt)
        if not accepted:
            return None
        try:
            value = self._query_value(query_key, value)
            store = self.project_controller.entity_database_store(node.namespace)
            query = EntityQueryFactory().builtin(
                query_key,
                database_uid=store.block.guid,
                value=value,
            )
            rows = EntityQueryFactory.execute(store, query)
        except ValueError as error:
            self.error_reporter(str(error))
            return None
        return self._open_results(rows, query.name, node.uid)

    @staticmethod
    def _query_value(query_key, value):
        if query_key == "spell_level":
            return int(value)
        if query_key in {"item_weight", "monster_challenge_rating"}:
            return float(value)
        return value

    def _open_results(self, rows, title, origin_uid):
        view = self.results_factory(
            rows,
            project_controller=self.project_controller,
            on_open=self._open_entity,
            on_clone=self._open_homebrew_editor,
            on_edit=self._open_homebrew_editor,
            origin_uid=origin_uid,
            parent=getattr(self.parent, "sceneViewer", None),
        )
        mdi_area = getattr(self.parent, "sceneViewer", None)
        if mdi_area is None:
            return view
        subwindow = mdi_area.addSubWindow(view)
        subwindow.setWindowTitle(title)
        subwindow.resize(900, 650)
        subwindow.show()
        return subwindow

    def _open_entity(self, entity):
        if self.inspection_controller is not None:
            return self.inspection_controller.display(entity)
        kwargs = {"parent": self.parent}
        parameters = inspect.signature(self.detail_dialog_factory).parameters
        accepts_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )
        if accepts_kwargs or "project_controller" in parameters:
            kwargs["project_controller"] = self.project_controller
        if accepts_kwargs or "on_clone" in parameters:
            kwargs["on_clone"] = self._open_homebrew_editor
        if accepts_kwargs or "on_edit" in parameters:
            kwargs["on_edit"] = self._open_homebrew_editor
        dialog = self.detail_dialog_factory(entity, **kwargs)
        dialog.exec()
        return dialog

    def open_entity_and_reveal(self, entity):
        """Open an entity inspection and reveal its node in the project tree."""
        result = self._open_entity(entity)
        self.reveal_entity(entity.uid)
        return result

    def reveal_entity(self, entity_uid):
        """Expand the tree to an entity UID and make its node current."""
        model = self.tree_view.model()
        if model is None:
            return QModelIndex()

        def find_index(parent=QModelIndex()):
            for row in range(model.rowCount(parent)):
                index = model.index(row, 0, parent)
                node = index.internalPointer()
                if getattr(node, "object_uid", None) == entity_uid or getattr(
                    node, "entity_uid", None
                ) == entity_uid:
                    return index
                found = find_index(index)
                if found.isValid():
                    return found
            return QModelIndex()

        index = find_index()
        if not index.isValid():
            return index

        ancestors = []
        parent = model.parent(index)
        while parent.isValid():
            ancestors.append(parent)
            parent = model.parent(parent)
        for ancestor in reversed(ancestors):
            self.tree_view.expand(ancestor)
        self.tree_view.setCurrentIndex(index)
        self.tree_view.scrollTo(index)
        return index

    def _open_homebrew_editor(self, entity):
        from application.homebrew import HomebrewDraft
        from dialog.homebrew import create_homebrew_mdi_view

        draft_factory = (
            HomebrewDraft.for_edit
            if entity.source_namespace == "homebrew"
            else HomebrewDraft.from_entity
        )
        view = create_homebrew_mdi_view(
            entity.entity_type,
            draft=draft_factory(entity),
            on_accept=lambda draft: self._commit_homebrew_draft(entity, draft),
            on_clone=(
                self._clone_homebrew_source
                if entity.source_namespace == "homebrew"
                else None
            ),
            parent=getattr(self.parent, "sceneViewer", None),
        )
        mdi_area = getattr(self.parent, "sceneViewer", None)
        if mdi_area is None:
            view.show()
            return view
        subwindow = mdi_area.addSubWindow(view)
        subwindow.setWindowTitle(view.windowTitle())
        subwindow.resize(680, 560)
        subwindow.show()
        return subwindow

    def _clone_homebrew_source(self, source_uid):
        clone = self.project_controller.copy_entity_to_homebrew(source_uid)
        return self._open_homebrew_editor(clone)

    def _open_new_homebrew_editor(self, draft):
        from dialog.homebrew import create_homebrew_mdi_view

        view = create_homebrew_mdi_view(
            draft.entity_type,
            draft=draft,
            on_accept=lambda accepted_draft: self._commit_homebrew_draft(
                None, accepted_draft
            ),
            parent=getattr(self.parent, "sceneViewer", None),
        )
        mdi_area = getattr(self.parent, "sceneViewer", None)
        if mdi_area is None:
            view.show()
            return view
        subwindow = mdi_area.addSubWindow(view)
        subwindow.setWindowTitle(view.windowTitle())
        subwindow.resize(1000, 650)
        subwindow.show()
        return subwindow

    def _commit_homebrew_draft(self, source_entity, draft):
        if source_entity is None:
            return self.project_controller.create_homebrew_entity(draft)
        if source_entity.source_namespace == "homebrew":
            updated = self.project_controller.update_homebrew_entity(
                source_entity.uid,
                draft,
            )
            if self.inspection_controller is not None:
                self.inspection_controller.refresh(updated.uid)
            return updated
        return self.project_controller.create_homebrew_entity(draft)

    def _request_text(self, title, prompt):
        return QInputDialog.getText(self.parent, title, prompt)

    def _report_error(self, message):
        QMessageBox.warning(self.parent, "Entity Query", message)