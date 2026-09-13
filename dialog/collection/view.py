from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QTableView,
    QVBoxLayout,
)

from application.entity_references import EntityNavigationController
from dialog.base.widget_editor import WidgetEditorView
from dialog.entity_reference import EntityReferenceDelegate
from tools.widgets.pagination import PaginationControls


class CollectionTableView(WidgetEditorView):
    """Collection workspace with filters backed by canonical entity rows."""

    def __init__(self, model, *, on_open=None, origin_uid=None, parent=None):
        super().__init__(model, parent=parent)
        self.navigation = EntityNavigationController(
            model.project_controller, on_open=on_open
        )
        self.origin_uid = origin_uid
        self.type_filter = QComboBox()
        self.type_filter.addItems(
            ("", "item", "spell", "race", "class", "monster", "feat", "background", "ability")
        )
        self.source_filter = QComboBox()
        self.source_filter.addItems(("", "compendium", "homebrew"))
        self.tag_filter = QLineEdit()
        self.text_filter = QLineEdit()
        self.group_combo = QComboBox()
        self.group_combo.addItem("None", None)
        self.group_combo.addItem("Type", "entity_type")
        self.group_combo.addItem("Source", "source_namespace")
        for control in (
            self.type_filter,
            self.source_filter,
            self.tag_filter,
            self.text_filter,
        ):
            signal = getattr(control, "currentTextChanged", None)
            (signal or control.textChanged).connect(self.apply_filters)
        self.group_combo.currentIndexChanged.connect(self.apply_grouping)

        self.table = QTableView()
        self.table.setModel(model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
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

        filters = QFormLayout()
        filters.addRow("Type", self.type_filter)
        filters.addRow("Source", self.source_filter)
        filters.addRow("Tag", self.tag_filter)
        filters.addRow("Search", self.text_filter)
        filters.addRow("Group", self.group_combo)
        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table)
        layout.addWidget(self.pagination)

    def apply_filters(self):
        self.model.set_filters(
            entity_type=self.type_filter.currentText(),
            source_namespace=self.source_filter.currentText(),
            tag=self.tag_filter.text(),
            text=self.text_filter.text(),
        )
        self.pagination.refresh()

    def apply_grouping(self):
        self.model.set_group_by(self.group_combo.currentData())
        self.pagination.refresh()

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

    def remove_selected_entity(self):
        entity_uid = self.selected_entity_uid()
        if entity_uid is None:
            return False
        removed = self.model.project_controller.remove_collection_entity(
            self.model.collection_uid, entity_uid
        )
        self.model.refresh()
        return removed