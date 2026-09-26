from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QVBoxLayout, QComboBox

from dialog.base.popup_editor import PopupEditorView

from .model import SRDImportModel


class SRDImportView(PopupEditorView):
    def __init__(self, model: SRDImportModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle("Import from 5eSRD Online")
        self.resize(480, 260)
        self.collection_combo = QComboBox()
        self.collection_combo.addItems(model.collections)
        self.query_edits = {}
        self.query_form = QFormLayout()
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)
        form = QFormLayout()
        form.addRow("Collection", self.collection_combo)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(self.query_form)
        layout.addWidget(self.error_label)
        layout.addWidget(self.create_button_box())
        self.collection_combo.currentTextChanged.connect(self._show_query_options)
        self._show_query_options(self.collection_combo.currentText())

    def _show_query_options(self, collection):
        while self.query_form.rowCount():
            self.query_form.removeRow(0)
        self.query_edits = {}
        for option in self.model.query_options.get(collection, ()):
            edit = QLineEdit()
            edit.setPlaceholderText(f"Optional {option} filter")
            self.query_edits[option] = edit
            self.query_form.addRow(option.replace("_", " ").title(), edit)

    def update_model(self):
        self.model.collection = self.collection_combo.currentText()
        self.model.query = {
            key: edit.text() for key, edit in self.query_edits.items() if edit.text().strip()
        }
        return self.model

    def apply_model(self):
        self.error_label.clear()
        try:
            return self.model.apply()
        except ValueError as error:
            self.error_label.setText(str(error))
            return None
