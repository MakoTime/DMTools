from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QTableView, QVBoxLayout

from application.entity_references import EntityNavigationController
from dialog.base.widget_editor import WidgetEditorView
from dialog.entity_reference import EntityReferenceDelegate
from tools.widgets.pagination import PaginationControls


class EntityQueryResultsView(WidgetEditorView):
    """Embedded query results with actions routed to the project controller."""

    def __init__(
        self,
        model,
        *,
        project_controller,
        collection_uid=None,
        on_open=None,
        on_clone=None,
        on_edit=None,
        origin_uid=None,
        parent=None,
    ):
        super().__init__(model, parent=parent)
        self.project_controller = project_controller
        self.collection_uid = collection_uid
        self.navigation = EntityNavigationController(
            project_controller, on_open=on_open
        )
        self.origin_uid = origin_uid
        self.on_clone = on_clone
        self.on_edit = on_edit

        self.table = QTableView()
        self.table.setModel(model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self.open_selected_entity)
        self.reference_delegate = EntityReferenceDelegate(
            model.EntityReferenceRole, self.table
        )
        self.reference_delegate.referenceActivated.connect(
            lambda reference: self.navigation.open(
                reference, origin_uid=self.origin_uid
            )
        )
        self.table.setItemDelegateForColumn(0, self.reference_delegate)
        self.pagination = PaginationControls(model, self)

        self.open_action = QAction("Open entity", self)
        self.open_action.triggered.connect(self.open_selected_entity)
        self.add_action = QAction("Add to Collection", self)
        self.add_action.triggered.connect(self.add_selected_to_collection)
        self.copy_action = QAction("Copy UID", self)
        self.copy_action.triggered.connect(self.copy_selected_uid)
        self.clone_action = QAction("Clone to Homebrew", self)
        self.clone_action.triggered.connect(self.clone_selected_to_homebrew)
        self.edit_action = QAction("Edit Homebrew", self)
        self.edit_action.triggered.connect(self.edit_selected_homebrew)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.pagination)

    def closeEvent(self, event):
        self.model.release_rows()
        super().closeEvent(event)

    def selected_entity_uid(self):
        rows = self.table.selectionModel().selectedRows()
        return self.model.entity_uid(rows[0]) if rows else None

    def open_selected_entity(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None:
            return None
        index = self.table.selectionModel().selectedRows()[0]
        reference = self.model.data(index, self.model.EntityReferenceRole)
        return self.navigation.open(reference, origin_uid=self.origin_uid)

    def navigate_back(self):
        return self.navigation.back()

    def add_selected_to_collection(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None or self.collection_uid is None:
            return False
        self.project_controller.add_collection_entity(self.collection_uid, entity_uid)
        return True

    def copy_selected_uid(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None:
            return None
        QApplication.clipboard().setText(entity_uid)
        return entity_uid

    def clone_selected_to_homebrew(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None:
            return None
        entity = self.project_controller.resolve_entity(entity_uid)
        if entity.source_namespace != "compendium":
            return None
        clone = self.project_controller.copy_entity_to_homebrew(entity_uid)
        if self.on_clone is not None:
            self.on_clone(clone)
        return clone

    def edit_selected_homebrew(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None:
            return None
        entity = self.project_controller.resolve_entity(entity_uid)
        if entity.source_namespace != "homebrew":
            return None
        if self.on_edit is not None:
            return self.on_edit(entity)
        return None

    def _show_context_menu(self, position):
        menu = QMenu(self)
        menu.addAction(self.open_action)
        menu.addAction(self.add_action)
        self.add_action.setEnabled(self.collection_uid is not None)
        self.clone_action.setEnabled(self.selected_entity_uid() is not None)
        menu.addAction(self.clone_action)
        selected_uid = self.selected_entity_uid()
        selected = (
            self.project_controller.resolve_entity(selected_uid)
            if selected_uid is not None
            else None
        )
        self.edit_action.setEnabled(
            selected is not None and selected.source_namespace == "homebrew"
        )
        menu.addAction(self.edit_action)
        menu.addAction(self.copy_action)
        menu.exec(self.table.viewport().mapToGlobal(position))