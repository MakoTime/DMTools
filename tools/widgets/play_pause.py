from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton

from common.icons import get_icon


class PlayPauseWidget(QToolButton):
    """Checkable play/pause control for starting and pausing work."""

    def __init__(self, playing=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("playPauseControl")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setAccessibleName("Play or pause")
        self.toggled.connect(self._update_icon)
        self.set_playing(playing)

    def is_playing(self):
        return self.isChecked()

    def set_playing(self, playing):
        self.setChecked(bool(playing))
        self._update_icon(bool(playing))

    def reset(self):
        self.set_playing(False)

    def _update_icon(self, playing):
        icon_name = "pause" if playing else "play"
        self.setIcon(get_icon(icon_name))
        self.setToolTip("Pause" if playing else "Play")
