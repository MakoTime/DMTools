from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QComboBox


class MultiSelectComboBox(QComboBox):
    """Compact checkable dropdown that exposes selected item data."""

    valuesChanged = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select one or more")
        self.view().viewport().installEventFilter(self)

    def set_options(self, options):
        self.clear()
        for label, value in options:
            self.addItem(label, value)
            item = self.model().item(self.count() - 1)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        self._update_text()

    def checked_values(self):
        return tuple(
            self.itemData(index)
            for index in range(self.count())
            if self.model().item(index).checkState() == Qt.CheckState.Checked
        )

    def set_checked_values(self, values):
        selected = set(values)
        for index in range(self.count()):
            state = (
                Qt.CheckState.Checked
                if self.itemData(index) in selected
                else Qt.CheckState.Unchecked
            )
            self.model().item(index).setCheckState(state)
        self._update_text()
        self.valuesChanged.emit(self.checked_values())

    def eventFilter(self, watched, event):
        if watched is self.view().viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.position().toPoint())
            if index.isValid():
                item = self.model().itemFromIndex(index)
                state = (
                    Qt.CheckState.Unchecked
                    if item.checkState() == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                item.setCheckState(state)
                self._update_text()
                self.valuesChanged.emit(self.checked_values())
            return True
        return super().eventFilter(watched, event)

    def _update_text(self):
        labels = [
            self.itemText(index)
            for index in range(self.count())
            if self.model().item(index).checkState() == Qt.CheckState.Checked
        ]
        self.lineEdit().setText(", ".join(labels))
