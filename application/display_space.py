from __future__ import annotations

from math import ceil, sqrt
from pathlib import Path

from PySide6.QtCore import QObject, QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QBrush, QCursor, QPalette
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QMdiArea, QMdiSubWindow, QToolButton, QWidget

from common.icons import get_icon


MDI_FRAME_UI = Path(__file__).resolve().parents[1] / "UI" / "mdi_window_frame.ui"


def mdi_content_widget(window: QMdiSubWindow):
    """Return the original view hosted inside an optional MDI frame."""
    frame = window.widget()
    return getattr(frame, "mdi_content_widget", frame)


class DisplaySpaceController(QObject):
    """Arrange MDI windows and keep their title bars reachable."""

    MINIMUM_TITLE_BAR_WIDTH = 80
    MINIMUM_TITLE_BAR_HEIGHT = 24
    RESIZE_MARGIN = 7

    def __init__(self, mdi_area: QMdiArea, parent=None):
        super().__init__(parent or mdi_area)
        self.mdi_area = mdi_area
        if self.mdi_area.objectName() == "sceneViewer":
            self.mdi_area.setBackground(
                QBrush(self.mdi_area.palette().color(QPalette.ColorRole.Window))
            )
            self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
            self.mdi_area.setTabsClosable(True)
            self.mdi_area.setTabsMovable(True)
            self.mdi_area.setDocumentMode(True)
        self._adjusting = False
        self._title_bar_windows = {}
        self._frame_windows = {}
        self._maximize_buttons = {}
        self._drag_offsets = {}
        self._resize_states = {}
        self.mdi_area.subWindowActivated.connect(self._track_window)
        self.mdi_area.installEventFilter(self)
        for window in self.mdi_area.subWindowList():
            self._track_window(window)
        self.enforce_bounds()

    def minimize_all(self):
        if not self.supports_arrangement:
            return
        windows = self._windows()
        for window in windows:
            window.showMinimized()
        self._arrange_minimized(windows)
        self.enforce_bounds()

    def rearrange_grid(self):
        if not self.supports_arrangement:
            return
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
        if not self.supports_arrangement:
            return
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
        title_window = getattr(self, "_title_bar_windows", {}).get(watched)
        window = (
            title_window
            or getattr(self, "_frame_windows", {}).get(watched)
            or (watched if isinstance(watched, QMdiSubWindow) else None)
        )
        if window is not None and watched is window:
            if event.type() == QEvent.Type.WindowStateChange:
                maximize_button = getattr(self, "_maximize_buttons", {}).get(window)
                if maximize_button is not None:
                    icon_name = "window_restore" if window.isMaximized() else "window_maximize"
                    maximize_button.setIcon(get_icon(icon_name))
                return False
        if window is not None:
            if (
                title_window is not None
                and event.type() == QEvent.Type.MouseButtonDblClick
            ):
                if window.isMaximized():
                    window.showNormal()
                else:
                    window.showMaximized()
                return True
            if event.type() == QEvent.Type.MouseButtonPress:
                if not window.isMaximized():
                    global_position = event.globalPosition().toPoint()
                    edges = (
                        Qt.Edges()
                        if isinstance(watched, QToolButton)
                        else self._resize_edges(window, global_position)
                    )
                    if edges:
                        self._resize_states[window] = (
                            edges,
                            global_position,
                            window.geometry(),
                        )
                        watched.grabMouse()
                        return True
                    if title_window is not None:
                        self._drag_offsets[window] = (
                            global_position - window.frameGeometry().topLeft()
                        )
                        watched.grabMouse()
                        return True
            elif event.type() == QEvent.Type.MouseMove:
                global_position = event.globalPosition().toPoint()
                if window in getattr(self, "_resize_states", {}):
                    self._resize_window(window, global_position)
                    return True
                if window in getattr(self, "_drag_offsets", {}):
                    window.move(global_position - self._drag_offsets[window])
                    return True
                if not window.isMaximized() and not isinstance(watched, QToolButton):
                    edges = self._resize_edges(window, global_position)
                    if edges:
                        watched.setCursor(self._resize_cursor(edges))
                    else:
                        watched.unsetCursor()
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if window in getattr(self, "_resize_states", {}):
                    self._resize_states.pop(window, None)
                    watched.releaseMouse()
                    watched.unsetCursor()
                    return True
                if window in getattr(self, "_drag_offsets", {}):
                    self._drag_offsets.pop(window, None)
                    watched.releaseMouse()
                    return True

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
        if self.mdi_area.viewMode() == QMdiArea.ViewMode.TabbedView:
            return
        if window is not None:
            if not getattr(window.widget(), "mdi_window_frame", False):
                self._install_frame(window)
            window.installEventFilter(self)
            self._clamp_window(window, self.mdi_area.viewport().rect())

    @property
    def supports_arrangement(self):
        return self.mdi_area.viewMode() == QMdiArea.ViewMode.SubWindowView

    def _install_frame(self, window):
        content_widget = window.widget()
        frame = QUiLoader().load(str(MDI_FRAME_UI))
        if frame is None or content_widget is None:
            return
        frame.mdi_window_frame = True
        frame.mdi_content_widget = content_widget
        content_host = frame.findChild(QWidget, "mdiContentHost")
        content_host.layout().addWidget(content_widget)
        title_bar = frame.findChild(QWidget, "mdiTitleBar")
        title_label = frame.findChild(QLabel, "mdiWindowTitle")
        minimize_button = title_bar.findChild(QToolButton, "mdiMinimizeButton")
        maximize_button = title_bar.findChild(QToolButton, "mdiMaximizeButton")
        close_button = title_bar.findChild(QToolButton, "mdiCloseButton")
        for button, icon_name in (
            (minimize_button, "window_minimize"),
            (maximize_button, "window_maximize"),
            (close_button, "window_close"),
        ):
            button.setText("")
            button.setIcon(get_icon(icon_name))
            button.setIconSize(QSize(18, 18))
        title_label.setText(window.windowTitle())
        window.windowTitleChanged.connect(title_label.setText)
        minimize_button.clicked.connect(window.showMinimized)
        maximize_button.clicked.connect(
            lambda _checked=False: (
                window.showNormal() if window.isMaximized() else window.showMaximized()
            )
        )
        close_button.clicked.connect(window.close)
        self._maximize_buttons[window] = maximize_button
        for surface in (title_bar, title_label):
            surface.installEventFilter(self)
            self._title_bar_windows[surface] = window
        window.setWidget(frame)
        window.setWindowFlags(
            window.windowFlags() | Qt.WindowType.FramelessWindowHint
        )
        for widget in (frame, *frame.findChildren(QWidget)):
            widget.installEventFilter(self)
            widget.setMouseTracking(True)
            self._frame_windows[widget] = window
        window.show()

    def _resize_edges(self, window, global_position):
        if window.isMaximized() or window.isMinimized():
            return Qt.Edges()
        position = window.mapFromGlobal(global_position)
        edges = Qt.Edges()
        if position.x() < self.RESIZE_MARGIN:
            edges |= Qt.Edge.LeftEdge
        elif position.x() >= window.width() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.RightEdge
        if position.y() < self.RESIZE_MARGIN:
            edges |= Qt.Edge.TopEdge
        elif position.y() >= window.height() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _resize_cursor(edges):
        left = bool(edges & Qt.Edge.LeftEdge)
        right = bool(edges & Qt.Edge.RightEdge)
        top = bool(edges & Qt.Edge.TopEdge)
        bottom = bool(edges & Qt.Edge.BottomEdge)
        if (left or right) and (top or bottom):
            if (left and top) or (right and bottom):
                return QCursor(Qt.CursorShape.SizeFDiagCursor)
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if left or right:
            return QCursor(Qt.CursorShape.SizeHorCursor)
        return QCursor(Qt.CursorShape.SizeVerCursor)

    def _resize_window(self, window, global_position):
        edges, start_position, original = self._resize_states[window]
        delta = global_position - start_position
        left, top = original.left(), original.top()
        right, bottom = original.right(), original.bottom()
        minimum_width = max(320, window.minimumWidth())
        minimum_height = max(220, window.minimumHeight())
        if edges & Qt.Edge.LeftEdge:
            left = min(left + delta.x(), right - minimum_width + 1)
        if edges & Qt.Edge.RightEdge:
            right = max(right + delta.x(), left + minimum_width - 1)
        if edges & Qt.Edge.TopEdge:
            top = min(top + delta.y(), bottom - minimum_height + 1)
        if edges & Qt.Edge.BottomEdge:
            bottom = max(bottom + delta.y(), top + minimum_height - 1)
        window.setGeometry(QRect(QPoint(left, top), QPoint(right, bottom)))

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
