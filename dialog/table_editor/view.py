from PySide6.QtWidgets import QTableView, QVBoxLayout

from dialog.base.widget_editor import WidgetEditorView
from dialog.database.model import DataFrameModel

from .model import TableEditorModel


class TableEditorView(WidgetEditorView):
    """Modeless editable view for a ProjectFoundry table artifact."""

    def __init__(self, model: TableEditorModel, parent=None, *, on_close=None):
        super().__init__(model, parent=parent, on_close=on_close)
        self.setWindowTitle(f"Table: {model.table_uid}")
        self.resize(760, 520)
        self.table_view = QTableView(self)
        self.table_model = DataFrameModel(model.frame, self.table_view)
        self.table_view.setModel(self.table_model)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view, 1)

    def refresh_table(self):
        frame = self.model.refresh_table()
        self.table_model = DataFrameModel(frame, self.table_view)
        self.table_view.setModel(self.table_model)

    def commit_changes(self):
        return self.model.commit_changes(self.table_model.frame)

    def closeEvent(self, event):
        self.notify_closed("window")
        self.model.release_table()
        self.model = None
        super().closeEvent(event)
