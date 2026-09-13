from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class EntityReferenceDelegate(QStyledItemDelegate):
    """Render entity names as links and publish their canonical reference."""

    referenceActivated = Signal(object)

    def __init__(self, reference_role, parent=None):
        super().__init__(parent)
        self.reference_role = reference_role

    def paint(self, painter, option, index):
        link_option = QStyleOptionViewItem(option)
        link_option.palette.setColor(
            QPalette.ColorRole.Text,
            link_option.palette.color(QPalette.ColorRole.Link),
        )
        link_option.font.setUnderline(True)
        super().paint(painter, link_option, index)

    def editorEvent(self, event, model, option, index):
        del option
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
        ):
            return self.activate(model, index)
        return False

    def activate(self, model, index):
        reference = model.data(index, self.reference_role)
        if reference is None:
            return False
        self.referenceActivated.emit(reference)
        return True