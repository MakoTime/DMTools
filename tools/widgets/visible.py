from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton

from common.icons import get_icon


class VisibleWidget(QToolButton):
    """Checkable eye control for showing or hiding an object."""

    def __init__(self, visible=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("visibleControl")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setAccessibleName("Object visibility")
        self.toggled.connect(self._update_icon)
        self.set_visible(visible)

    def is_visible(self):
        return self.isChecked()

    def set_visible(self, visible):
        visible = bool(visible)
        self.setChecked(visible)
        self._update_icon(visible)

    def _update_icon(self, visible):
        icon_name = "visible" if visible else "invisible"
        self.setIcon(get_icon(icon_name))
        self.setToolTip("Hide object" if visible else "Show object")
