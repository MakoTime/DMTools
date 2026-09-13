from PySide6.QtWidgets import QCheckBox, QLabel, QPlainTextEdit, QVBoxLayout

from dialog.base.popup_editor import PopupEditorView

from .model import ImportPreviewModel


class ImportPreviewView(PopupEditorView):
    """Display validated import counts and require explicit confirmation."""

    def __init__(self, model: ImportPreviewModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle("Import Preview")
        self.resize(620, 440)

        summary = QPlainTextEdit(model.summary)
        summary.setReadOnly(True)
        self.skip_invalid_check = QCheckBox(
            "Skip invalid and unsupported records"
        )
        self.skip_invalid_check.setChecked(model.skip_invalid)
        self.skip_invalid_check.setVisible(
            any(issue.blocking for issue in model.preview.issues)
        )
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(summary)
        layout.addWidget(self.skip_invalid_check)
        layout.addWidget(self.error_label)
        layout.addWidget(self.create_button_box())
        self.skip_invalid_check.toggled.connect(self._update_commit_state)
        self._update_commit_state()

    def update_model(self):
        self.model.skip_invalid = self.skip_invalid_check.isChecked()
        return self.model

    def _update_commit_state(self):
        can_commit_valid = bool(self.model.preview.records) and not self.model.preview.cancelled
        issues_allowed = (
            self.model.preview.can_commit or self.skip_invalid_check.isChecked()
        )
        self.ok_button.setEnabled(can_commit_valid and issues_allowed)

    def apply_model(self):
        self.error_label.clear()
        try:
            return self.model.apply()
        except ValueError as error:
            self.error_label.setText(str(error))
            return None