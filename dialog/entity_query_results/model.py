from typing import Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from application.entity_references import EntityReference


class EntityQueryResultsModel(QAbstractTableModel):
    """Sortable presentation adapter retaining canonical entity rows and UIDs."""

    EntityUidRole = Qt.ItemDataRole.UserRole + 1
    EntityReferenceRole = Qt.ItemDataRole.UserRole + 2
    COLUMNS = (
        ("Name", "name"),
        ("Type", "entity_type"),
        ("Source", "source_namespace"),
    )

    def __init__(
        self,
        rows=(),
        parent=None,
        *,
        result_uid=None,
        rows_loader: Callable[[str], object] | None = None,
        page_size=100,
    ):
        super().__init__(parent)
        self.result_uid = result_uid
        self._rows_loader = rows_loader
        self._rows = list(rows) if rows else None
        self.page_size = max(1, int(page_size))
        self._page = 0

    def _ensure_rows(self):
        if self._rows is None:
            if self.result_uid is None or self._rows_loader is None:
                self._rows = []
            else:
                self._rows = list(self._rows_loader(self.result_uid))
        return self._rows

    def release_rows(self):
        """Release loaded result records when the results view closes."""
        self.beginResetModel()
        self._rows = None
        self._rows_loader = None
        self.endResetModel()

    @property
    def page(self):
        return self._page

    @property
    def page_count(self):
        rows = self._ensure_rows()
        return max(1, (len(rows) + self.page_size - 1) // self.page_size)

    def set_page(self, page):
        page = max(0, min(int(page), self.page_count - 1))
        if page == self._page:
            return False
        self.beginResetModel()
        self._page = page
        self.endResetModel()
        return True

    def _visible_rows(self):
        start = self._page * self.page_size
        return self._ensure_rows()[start : start + self.page_size]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._visible_rows())

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._visible_rows()[index.row()]
        if role == self.EntityUidRole:
            return row.uid
        if role == self.EntityReferenceRole:
            return EntityReference(
                row.uid, row.entity_type, row.source_namespace, row.name
            )
        if role == Qt.ItemDataRole.DisplayRole:
            return str(getattr(row, self.COLUMNS[index.column()][1]))
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section][0]
        return section + 1

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if not 0 <= column < len(self.COLUMNS):
            return
        attribute = self.COLUMNS[column][1]
        self.layoutAboutToBeChanged.emit()
        self._ensure_rows().sort(
            key=lambda row: (str(getattr(row, attribute)).casefold(), row.uid),
            reverse=order == Qt.SortOrder.DescendingOrder,
        )
        self._page = min(self._page, self.page_count - 1)
        self.layoutChanged.emit()

    def entity_uid(self, index):
        if not index.isValid():
            return None
        return self._visible_rows()[index.row()].uid

    def entity_row(self, index):
        if not index.isValid():
            return None
        return self._visible_rows()[index.row()]