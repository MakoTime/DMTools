from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from dialog.base.popup_editor import PopupEditorView

from .model import ResolveReferencesModel


class ResolveReferencesView(PopupEditorView):
    """Choose a canonical entity for one unresolved reference pattern."""

    def __init__(self, model: ResolveReferencesModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle("Resolve References")
        self.resize(620, 480)

        self.reference_label = QLabel()
        self.reference_list = QListWidget()
        for reference in model.references:
            self.reference_list.addItem(reference.label)
        self.reference_list.currentRowChanged.connect(self._reference_changed)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter entities")
        self.search_edit.textChanged.connect(self._refresh_candidates)
        self.candidate_list = QListWidget()
        self.candidate_list.currentItemChanged.connect(self._candidate_changed)

        buttons = self.create_button_box(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Unresolved reference"))
        layout.addWidget(self.reference_label)
        layout.addWidget(self.reference_list)
        layout.addWidget(QLabel("Choose the entity it refers to"))
        layout.addWidget(self.search_edit)
        layout.addWidget(self.candidate_list, 1)
        layout.addWidget(buttons)
        self._reference_changed(0)
        self._refresh_candidates()

    def _reference_changed(self, row):
        if row < 0:
            return
        self.model.reference_index = row
        reference = self.model.selected_reference
        self.reference_label.setText(reference.label if reference else "")

    def _refresh_candidates(self):
        selected_uid = self.model.target_uid
        self.candidate_list.clear()
        for candidate in self.model.filtered_candidates(self.search_edit.text()):
            item = QListWidgetItem(
                f"{candidate.name} ({candidate.entity_type}; {candidate.source_namespace})"
            )
            item.setData(0x0100, candidate.uid)
            self.candidate_list.addItem(item)
            if candidate.uid == selected_uid:
                self.candidate_list.setCurrentItem(item)

    def _candidate_changed(self, current, _previous):
        self.model.target_uid = current.data(0x0100) if current else None

    def apply_changes(self):
        try:
            return self.model.apply()
        except ValueError as error:
            self.reference_label.setText(str(error))
            return None
