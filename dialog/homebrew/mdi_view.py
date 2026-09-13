import json

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from dialog.base.widget_editor import WidgetEditorView

from .model import HomebrewEditorModel


class HomebrewEditorMdiView(WidgetEditorView):
    """Modeless Homebrew draft editor for the main window MDI area."""

    def __init__(self, model: HomebrewEditorModel, *, on_accept=None, parent=None):
        super().__init__(model, parent=parent)
        self.on_accept = on_accept
        self._close_reason = None
        self.setWindowTitle(f"Homebrew {model.entity_type.title()}")

        self.type_label = QLabel(model.entity_type.title())
        self.name_edit = QLineEdit(model.name)
        self.state_combo = QComboBox()
        self.state_combo.addItems(("draft", "published", "archived"))
        self.state_combo.setCurrentText(model.draft_state)
        self.published_check = QCheckBox()
        self.published_check.setChecked(model.published)
        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 9999)
        self.version_spin.setValue(model.version)
        self.payload_edit = QTextEdit(
            json.dumps(model.payload, indent=2, sort_keys=True)
        )
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Type", self.type_label)
        form.addRow("Name", self.name_edit)
        form.addRow("State", self.state_combo)
        form.addRow("Published", self.published_check)
        form.addRow("Version", self.version_spin)
        form.addRow("Entity data", self.payload_edit)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.clicked.connect(self.apply_changes)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self._cancel)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.cancel_button)

    def update_model(self):
        self.model.name = self.name_edit.text()
        self.model.draft_state = self.state_combo.currentText()
        self.model.published = self.published_check.isChecked()
        self.model.version = self.version_spin.value()
        return self.model

    def apply_model(self):
        self.error_label.clear()
        try:
            payload = json.loads(self.payload_edit.toPlainText())
            if not isinstance(payload, dict):
                raise ValueError("Entity data must be a JSON object")
            self.model.payload = payload
            return self.model.apply()
        except (ValueError, json.JSONDecodeError) as error:
            self.error_label.setText(str(error))
            return None

    def apply_changes(self):
        record = super().apply_changes()
        if record is not None and self.on_accept is not None:
            on_accept = self.on_accept
            self.on_accept = None
            on_accept(self.model)
        return record

    def _cancel(self):
        self._close_reason = "cancel"
        self.close()

    def closeEvent(self, event):
        self.notify_closed(self._close_reason or "window")
        self.on_accept = None
        self.model = None
        super().closeEvent(event)
