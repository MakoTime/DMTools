from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QAbstractItemView,
)

from dialog.base.popup_editor import PopupEditorView

from .model import ManualReferencesModel, ReferenceEntry


class ManualReferencesView(PopupEditorView):
    """Review stored references and match unresolved links to entities."""

    def __init__(
        self,
        model: ManualReferencesModel,
        parent=None,
        *,
        on_open_entity=None,
    ):
        super().__init__(model, parent=parent)
        self.on_open_entity = on_open_entity
        self.setWindowTitle("Manual References")
        self.resize(980, 620)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All references", "all")
        self.status_combo.addItem("Manually resolved", "manual")
        self.status_combo.addItem("Resolved references", "resolved")
        self.status_combo.addItem("Unresolved references", "unresolved")
        self.status_combo.setCurrentIndex(3)
        self.status_combo.currentIndexChanged.connect(self._refresh_references)
        self.reference_search = QLineEdit()
        self.reference_search.setPlaceholderText("Filter references or source entities")
        self.reference_search.setClearButtonEnabled(True)
        self.reference_search.textChanged.connect(self._refresh_references)
        self.reference_list = QListWidget()
        self.reference_list.currentItemChanged.connect(self._reference_changed)
        self.open_source_button = QPushButton("Open source entity")
        self.open_source_button.clicked.connect(self._open_source_entity)

        reference_group = QGroupBox("References")
        reference_layout = QVBoxLayout(reference_group)
        reference_layout.addWidget(self.status_combo)
        reference_layout.addWidget(self.reference_search)
        reference_layout.addWidget(self.open_source_button)
        reference_layout.addWidget(self.reference_list, 1)

        self.selection_label = QLabel()
        self.selection_label.setWordWrap(True)
        self.target_label = QLabel()
        self.target_label.setWordWrap(True)
        self.open_match_button = QPushButton("Open match entity")
        self.open_match_button.clicked.connect(self._open_match_entity)
        self.candidate_type_combo = QComboBox()
        self.candidate_type_combo.addItem("All entity types", None)
        entity_types = sorted({candidate.entity_type for candidate in model.candidates})
        for entity_type in entity_types:
            self.candidate_type_combo.addItem(
                entity_type.replace("_", " ").title(), entity_type
            )
        self.candidate_type_combo.currentIndexChanged.connect(
            self._refresh_candidates
        )
        self.candidate_search = QLineEdit()
        self.candidate_search.setPlaceholderText("Search entities to match")
        self.candidate_search.setClearButtonEnabled(True)
        self.candidate_search.textChanged.connect(self._refresh_candidates)
        self.candidate_list = QListWidget()
        self.candidate_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self.candidate_list.itemSelectionChanged.connect(self._update_selected_targets)
        self.candidate_list.itemChanged.connect(self._update_selected_targets)
        self.resolve_button = QPushButton("Match Selected Reference")
        self.resolve_button.clicked.connect(self._resolve_selected)
        self.intended_button = QPushButton("Mark as intended")
        self.intended_button.setFixedWidth(120)
        self.intended_button.clicked.connect(self._mark_intended)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        matching_group = QGroupBox("Match Reference")
        matching_layout = QVBoxLayout(matching_group)
        matching_layout.addWidget(self.selection_label)
        matching_layout.addWidget(self.target_label)
        matching_layout.addWidget(self.open_match_button)
        matching_layout.addWidget(self.candidate_type_combo)
        matching_layout.addWidget(self.candidate_search)
        matching_layout.addWidget(self.candidate_list, 1)
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.resolve_button, 1)
        action_layout.addWidget(self.intended_button)
        matching_layout.addLayout(action_layout)
        matching_layout.addWidget(self.status_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(reference_group)
        splitter.addWidget(matching_group)
        splitter.setSizes((420, 560))
        splitter.setStretchFactor(1, 1)

        buttons = self.create_button_box(QDialogButtonBox.StandardButton.Close)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)
        layout.addWidget(buttons)

        self._refresh_references()

    def _refresh_references(self):
        current = self.model.selected_reference
        references = self.model.filtered_references(
            self.status_combo.currentData(), self.reference_search.text()
        )
        self.reference_list.blockSignals(True)
        self.reference_list.clear()
        selected_row = -1
        for row, reference in enumerate(references):
            item = QListWidgetItem(
                f"{reference.display_fallback}  |  {reference.source_name}"
            )
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(Qt.ItemDataRole.UserRole, reference)
            self.reference_list.addItem(item)
            if reference == current:
                selected_row = row
        self.reference_list.blockSignals(False)
        if selected_row < 0 and references:
            selected_row = 0
        if selected_row >= 0:
            self.reference_list.setCurrentRow(selected_row)
        else:
            self.model.selected_reference = None
            self._show_reference(None)

    def _reference_changed(self, current, _previous):
        reference = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.model.selected_reference = reference
        self._show_reference(reference)

    def _show_reference(self, reference: ReferenceEntry | None):
        self.status_label.clear()
        self.candidate_search.clear()
        self.candidate_list.clear()
        self.resolve_button.setProperty("target_uids", ())
        if reference is None:
            self.selection_label.setText("No references match the current filter.")
            self.open_source_button.setEnabled(False)
            self.open_match_button.setEnabled(False)
            self.target_label.clear()
            self.resolve_button.setEnabled(False)
            self.intended_button.setEnabled(False)
            return
        self.selection_label.setText(
            f"{reference.label}\nFrom: {reference.source_label}\nPath: {reference.path}"
        )
        self._select_candidate_type(reference.reference_type)
        self.open_source_button.setEnabled(self.on_open_entity is not None)
        if reference.status == "resolved":
            self.target_label.setText(
                f"Current match: {reference.target_name}"
                f" ({reference.target_namespace or 'unknown namespace'})"
            )
            self.resolve_button.setEnabled(True)
            self.intended_button.setEnabled(False)
            self.open_match_button.setText("Open match entity")
            self.open_match_button.setEnabled(self.on_open_entity is not None)
            self._refresh_candidates()
        else:
            self.target_label.clear()
            self.resolve_button.setEnabled(True)
            self.intended_button.setEnabled(True)
            self.open_match_button.setEnabled(False)
            self.open_match_button.setText("Open selected candidate")
            self._refresh_candidates()

    def _select_candidate_type(self, entity_type):
        index = self.candidate_type_combo.findData(entity_type)
        self.candidate_type_combo.setCurrentIndex(index if index >= 0 else 0)

    def _open_source_entity(self):
        reference = self.model.selected_reference
        if reference is None or self.on_open_entity is None:
            return None
        entity = self.model.project_controller.resolve_entity(reference.source_uid)
        return self.on_open_entity(entity)

    def _open_match_entity(self):
        reference = self.model.selected_reference
        if reference is None or self.on_open_entity is None:
            return None
        target_uid = reference.target_uid
        if target_uid is None:
            target_uids = self.resolve_button.property("target_uids") or ()
            if len(target_uids) != 1:
                return None
            target_uid = target_uids[0]
        entity = self.model.project_controller.resolve_entity(target_uid)
        return self.on_open_entity(entity)

    def _refresh_candidates(self):
        reference = self.model.selected_reference
        self.candidate_list.clear()
        if reference is None:
            return
        for candidate in self.model.filtered_candidates(
            self.candidate_search.text(),
            entity_type=self.candidate_type_combo.currentData(),
        ):
            item = QListWidgetItem(
                f"{candidate.name} ({candidate.entity_type}; {candidate.source_namespace})"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if candidate.uid == reference.target_uid
                else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, candidate.uid)
            self.candidate_list.addItem(item)

    def _update_selected_targets(self):
        target_uids = tuple(
            item.data(Qt.ItemDataRole.UserRole)
            for item in (
                self.candidate_list.item(row)
                for row in range(self.candidate_list.count())
            )
            if item.checkState() == Qt.CheckState.Checked
        )
        self.resolve_button.setProperty("target_uids", target_uids)
        reference = self.model.selected_reference
        self.open_match_button.setEnabled(
            self.on_open_entity is not None
            and reference is not None
            and (
                reference.status == "resolved"
                or (reference.status == "unresolved" and len(target_uids) == 1)
            )
        )

    def _resolve_selected(self):
        target_uids = self.resolve_button.property("target_uids") or ()
        try:
            updated = self.model.resolve(target_uids)
        except ValueError as error:
            self.status_label.setStyleSheet("color: #b42318;")
            self.status_label.setText(str(error))
            return None
        self.status_label.setStyleSheet("")
        self.status_label.setText(f"Updated {len(updated)} source reference(s).")
        self._refresh_references()
        return updated

    def _mark_intended(self):
        try:
            updated = self.model.mark_intended()
        except ValueError as error:
            self.status_label.setStyleSheet("color: #b42318;")
            self.status_label.setText(str(error))
            return None
        self.status_label.setStyleSheet("")
        self.status_label.setText("Marked reference as intended.")
        self._refresh_references()
        return updated

    def apply_changes(self):
        return self.model
