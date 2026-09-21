from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from dialog.base.popup_editor import PopupEditorView

from .model import RuleDetailModel


class RuleDetailView(PopupEditorView):
    """Read-only HMI view for one schema-backed Rules value."""

    def __init__(self, model: RuleDetailModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle(model.title)
        self.resize(620, 420)

        heading = QLabel(model.title, self)
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        description_heading = QLabel("Rule description", self)
        description_heading.setStyleSheet("font-weight: 600;")
        description = QLabel(model.details["Description"], self)
        description.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addWidget(description_heading)
        layout.addWidget(description)
        layout.addWidget(self.create_button_box(QDialogButtonBox.StandardButton.Close))