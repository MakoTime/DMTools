from __future__ import annotations

from math import ceil, sqrt

from PySide6.QtCore import QObject, QEvent, QPoint, QRect
from PySide6.QtWidgets import QMdiArea, QMdiSubWindow


class DisplaySpaceController(QObject):
    """Arrange MDI windows and keep their title bars reachable."""

    MINIMUM_TITLE_BAR_WIDTH = 80
    MINIMUM_TITLE_BAR_HEIGHT = 24

    def __init__(self, mdi_area: QMdiArea, parent=None):
        super().__init__(parent or mdi_area)
        self.mdi_area = mdi_area
        self._adjusting = False
        self.mdi_area.subWindowActivated.connect(self._track_window)
        self.mdi_area.installEventFilter(self)
        for window in self.mdi_area.subWindowList():
            self._track_window(window)
        self.enforce_bounds()

    def minimize_all(self):
        windows = self._windows()
        for window in windows:
            window.showMinimized()
        self._arrange_minimized(windows)
        self.enforce_bounds()

    def rearrange_grid(self):
        windows = self._windows()
        if not windows:
            return
        for window in windows:
            window.showNormal()
        area = self.mdi_area.viewport().rect()
        columns = max(1, ceil(sqrt(len(windows))))
        rows = ceil(len(windows) / columns)
        cell_width = max(220, area.width() // columns)
        cell_height = max(160, area.height() // rows)
        for index, window in enumerate(windows):
            row, column = divmod(index, columns)
            window.setGeometry(
                QRect(
                    column * cell_width,
                    row * cell_height,
                    cell_width,
                    cell_height,
                )
            )
        self.enforce_bounds()

    def enforce_bounds(self):
        if self._adjusting:
            return
        self._adjusting = True
        try:
            area = self.mdi_area.viewport().rect()
            for window in self._windows():
                self._clamp_window(window, area)
        finally:
            self._adjusting = False

    def eventFilter(self, watched, event):
        mdi_area = getattr(self, "mdi_area", None)
        if mdi_area is None:
            return False
        if watched is mdi_area and event.type() == QEvent.Type.Resize:
            self.enforce_bounds()
        elif isinstance(watched, QMdiSubWindow) and event.type() in {
            QEvent.Type.Move,
            QEvent.Type.Resize,
            QEvent.Type.Show,
        }:
            self._clamp_window(watched, mdi_area.viewport().rect())
        return super().eventFilter(watched, event)

    def _track_window(self, window):
        if window is not None:
            window.installEventFilter(self)
            self._clamp_window(window, self.mdi_area.viewport().rect())

    def _windows(self):
        return tuple(self.mdi_area.subWindowList())

    def _arrange_minimized(self, windows):
        area = self.mdi_area.viewport().rect()
        if not windows:
            return
        width = max(self.MINIMUM_TITLE_BAR_WIDTH, min(240, area.width() // len(windows)))
        height = max(self.MINIMUM_TITLE_BAR_HEIGHT, 30)
        for index, window in enumerate(windows):
            window.setGeometry(QRect(index * width, 0, width, height))

    def _clamp_window(self, window: QMdiSubWindow, area):
        if not area.isValid():
            return
        geometry = window.geometry()
        title_width = min(self.MINIMUM_TITLE_BAR_WIDTH, max(1, geometry.width()))
        title_height = min(self.MINIMUM_TITLE_BAR_HEIGHT, max(1, geometry.height()))
        minimum_x = area.left() - geometry.width() + title_width
        maximum_x = area.right() - title_width + 1
        minimum_y = area.top()
        maximum_y = area.bottom() - title_height + 1
        x = min(max(geometry.x(), minimum_x), maximum_x)
        y = min(max(geometry.y(), minimum_y), maximum_y)
        if geometry.topLeft() != QPoint(x, y):
            window.move(x, y)
