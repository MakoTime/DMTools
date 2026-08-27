from dataclasses import dataclass, field

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from dialog.base.editor import EditorModel


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


@dataclass
class FilterCondition:
    column: str
    operator: str
    value: str
    relationship: str = "AND"
    opening_groups: int = 0
    closing_groups: int = 0
    negated: bool = False


@dataclass
class LookupStep:
    table: str = ""
    operator: str = "Equals"
    input_value: str = ""
    output: str = ""


@dataclass
class MultiTableLookup:
    """Structured lookup path used to build a query without handwritten SQL."""

    enabled: bool = False
    steps: list[LookupStep] = field(default_factory=list)
    lookup_table: str = ""
    lookup_column: str = ""
    lookup_operator: str = "Equals"
    lookup_value: str = ""
    lookup_return_column: str = ""
    bridge_table: str = ""
    bridge_lookup_column: str = ""
    bridge_output_column: str = ""
    output_table: str = ""
    output_column: str = ""


@dataclass
class DatabaseWorkspaceModel(EditorModel):
    """State edited and displayed by the database workspace view."""

    database_object: object
    filters: list[FilterCondition] = field(default_factory=list)
    lookup: MultiTableLookup = field(default_factory=MultiTableLookup)
    result_frame: object = None
    original_frame: object = None

    def validate(self):
        if self.database_object is None:
            raise ValueError("A database is required")

    def apply(self):
        self.validate()
        return self
