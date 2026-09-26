from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DataFrameModel(QAbstractTableModel):
    """Editable Qt model backed by a pandas DataFrame result."""

    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.frame = frame.copy()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame.index)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self.frame.iloc[index.row(), index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.EditRole:
            return value
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        self.frame.iat[index.row(), index.column()] = value
        self.dataChanged.emit(index, index, [role, Qt.ItemDataRole.DisplayRole])
        return True

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self.frame.columns[section])
        return str(self.frame.index[section])

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if not 0 <= column < len(self.frame.columns):
            return
        self.layoutAboutToBeChanged.emit()
        self.frame = self.frame.sort_values(
            by=self.frame.columns[column],
            ascending=order == Qt.SortOrder.AscendingOrder,
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)
        self.layoutChanged.emit()