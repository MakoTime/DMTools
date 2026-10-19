from PySide6.QtCore import QObject, QSize, Qt
from PySide6.QtWidgets import QTabWidget, QToolButton, QWidget
from shiboken6 import isValid

from common.icons import get_icon

from .model import WorkspaceTabModel


def _close_workspace_tab(tabs: QTabWidget, widget: QWidget):
    if not isValid(widget):
        return
    index = tabs.indexOf(widget)
    if index >= 0:
        tabs.removeTab(index)
    widget.close()
    widget.deleteLater()


class WorkspaceTabView(QObject):
    """Qt presentation adapter for one tab-hosted workspace view."""

    def __init__(
        self,
        model: WorkspaceTabModel,
        tabs: QTabWidget,
        widget: QWidget,
        *,
        on_restore=None,
        insert_index=None,
    ):
        super().__init__(tabs)
        self.model = model
        self.tabs = tabs
        self.workspace_content_widget = widget
        self.restore_callback = on_restore
        widget.setWindowTitle(model.title)
        widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        index = (
            tabs.addTab(widget, model.title)
            if insert_index is None
            else tabs.insertTab(insert_index, widget, model.title)
        )
        model.attach()
        self.restore_button = self._create_restore_button(index)
        self.close_button = self._create_close_button(index)
        widget.windowTitleChanged.connect(self._update_title)
        widget.destroyed.connect(self._remove_tab)
        self.show()

    def __getattr__(self, name):
        return getattr(self.workspace_content_widget, name)

    @property
    def is_valid(self):
        return isValid(self.workspace_content_widget)

    def _create_restore_button(self, index):
        if not self.model.can_restore:
            return None
        button = QToolButton(self.tabs.tabBar())
        button.setObjectName("workspaceTabRestoreButton")
        button.setAutoRaise(True)
        button.setFixedSize(22, 22)
        button.setIcon(get_icon("window_restore"))
        button.setIconSize(QSize(12, 12))
        button.setToolTip("Restore to MDI area")
        button.clicked.connect(lambda _checked=False: self.restore_callback())
        self.tabs.tabBar().setTabButton(
            index, self.tabs.tabBar().ButtonPosition.LeftSide, button
        )
        return button

    def _create_close_button(self, index):
        button = QToolButton(self.tabs.tabBar())
        button.setObjectName("workspaceTabCloseButton")
        button.setAutoRaise(True)
        button.setFixedSize(22, 22)
        button.setIcon(get_icon("window_close"))
        button.setIconSize(QSize(12, 12))
        button.setToolTip("Close tab")
        button.setStyleSheet(
            "QToolButton { background: transparent; border: none; padding: 0; }"
            "QToolButton:hover { background: transparent; border: none; }"
        )
        button.clicked.connect(
            lambda _checked=False: _close_workspace_tab(
                self.tabs,
                self.workspace_content_widget,
            )
        )
        self.tabs.tabBar().setTabButton(
            index, self.tabs.tabBar().ButtonPosition.RightSide, button
        )
        return button

    def _update_title(self, title):
        self.model.set_title(title)
        index = self.tabs.indexOf(self.workspace_content_widget)
        if index >= 0:
            self.tabs.setTabText(index, title)

    def _remove_tab(self, *_args):
        if self.is_valid:
            index = self.tabs.indexOf(self.workspace_content_widget)
            if index >= 0:
                self.tabs.removeTab(index)
        self.model.detach()

    def show(self):
        if self.is_valid:
            self.tabs.setCurrentWidget(self.workspace_content_widget)
            self.workspace_content_widget.show()

    def showNormal(self):
        self.show()

    def raise_(self):
        self.show()

    def activateWindow(self):
        self.show()
        self.workspace_content_widget.activateWindow()

    def close(self):
        _close_workspace_tab(self.tabs, self.workspace_content_widget)

    def detach(self):
        index = self.tabs.indexOf(self.workspace_content_widget)
        if index >= 0:
            self.tabs.removeTab(index)
        self.model.detach()
        for button in (self.restore_button, self.close_button):
            if button is not None:
                button.deleteLater()
        self.workspace_content_widget.setParent(None)
        return self.workspace_content_widget