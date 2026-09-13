from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout

from dialog.base.popup_editor import PopupEditorView

from .model import QueryEditorModel


class QueryEditorView(PopupEditorView):
    """Edit one saved-query draft without mutating persistent state."""

    def __init__(self, model: QueryEditorModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle("Saved Query")
        self.resize(640, 420)

        self.name_edit = QLineEdit(model.name)
        self.sql_edit = QTextEdit(model.sql)
        self.sql_edit.setPlaceholderText("SELECT * FROM table_name")
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("SQL", self.sql_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(self.create_button_box())

    def update_model(self):
        self.model.name = self.name_edit.text()
        self.model.sql = self.sql_edit.toPlainText()
        return self.model

    def apply_model(self):
        self.error_label.clear()
        try:
            return self.model.apply()
        except ValueError as error:
            self.error_label.setText(str(error))
            return None