from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout

from dialog.base.widget_editor import WidgetEditorView

from .model import ObjectInspectionModel


class ObjectInspectionView(WidgetEditorView):
    """Modeless read-only inspection for a generic project object."""

    def __init__(self, model: ObjectInspectionModel, parent=None, *, on_close=None):
        super().__init__(model, parent=parent, on_close=on_close)
        self.setWindowTitle(model.title)
        self.resize(640, 480)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(model.formatted_details)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit, 1)

    def refresh_object(self):
        self.text_edit.setPlainText(self.model.formatted_details)
        self.setWindowTitle(self.model.title)
        self.model.release_object()

    def closeEvent(self, event):
        self.notify_closed("window")
        self.model.release_object()
        self.model = None
        super().closeEvent(event)
