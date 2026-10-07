from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMdiArea,
    QTabBar,
    QToolButton,
    QWidget,
)

from application.display_space import DisplaySpaceController, mdi_content_widget
from common import dev_mode
from components.tree import TreeView
from menu import setup_menu


def qt_app():
    return QApplication.instance() or QApplication([])


def test_display_space_menu_has_arrangement_actions():
    qt_app()
    window = QMainWindow()
    window.menuFile = window.menuBar().addMenu("File")
    window.menuEdit = window.menuBar().addMenu("Edit")
    window.sceneViewer = QMdiArea(window)
    controller = DisplaySpaceController(window.sceneViewer, parent=window)
    window.display_space_controller = controller

    setup_menu(window)

    assert window.minimize_all_action.text() == "Minimise all"
    assert window.rearrange_grid_action.text() == "Rearrange grid"
    assert window.minimize_all_action.isEnabled()
    assert window.rearrange_grid_action.isEnabled()


def test_development_menu_toggles_global_dev_mode():
    qt_app()
    dev_mode.set_enabled(False)
    window = QMainWindow()
    window.menuFile = window.menuBar().addMenu("File")
    window.menuEdit = window.menuBar().addMenu("Edit")

    setup_menu(window)

    assert window.development_menu.title() == "Development"
    assert not window.dev_mode_action.isChecked()
    window.dev_mode_action.trigger()
    assert dev_mode.is_enabled()
    window.dev_mode_action.trigger()
    assert not dev_mode.is_enabled()


def test_display_space_grid_and_minimize_keep_windows_reachable():
    qt_app()
    mdi_area = QMdiArea()
    mdi_area.resize(600, 400)
    controller = DisplaySpaceController(mdi_area)
    windows = [mdi_area.addSubWindow(QWidget()) for _ in range(4)]
    for window in windows:
        window.resize(300, 240)
        window.show()

    controller.rearrange_grid()

    assert all(window.geometry().top() >= 0 for window in windows)
    assert all(window.geometry().left() < mdi_area.viewport().width() for window in windows)

    windows[0].move(-500, -500)
    controller.enforce_bounds()
    geometry = windows[0].geometry()
    assert geometry.top() >= 0
    assert geometry.right() >= 0

    controller.minimize_all()

    assert all(window.isMinimized() for window in windows)
    assert all(window.geometry().top() >= 0 for window in windows)


def test_scene_viewport_uses_the_workspace_theme_surface():
    app = qt_app()
    previous_stylesheet = app.styleSheet()
    root = Path(__file__).resolve().parents[1]
    stylesheet_path = root / "views" / "app_theme.qss"
    app.setStyleSheet(stylesheet_path.read_text(encoding="utf-8"))
    loader = QUiLoader()
    loader.registerCustomWidget(TreeView)
    window = loader.load(str(root / "UI" / "main.ui"))
    window.resize(1280, 820)
    DisplaySpaceController(window.sceneViewer)
    window.show()
    app.processEvents()

    image = window.sceneViewer.viewport().grab().toImage()
    center = image.pixelColor(image.width() // 2, image.height() // 2)
    tab_bar = window.workspaceTabs.findChild(QTabBar)
    tab_image = tab_bar.grab().toImage()
    scene_tab = tab_bar.tabRect(0)
    active_indicator = tab_image.pixelColor(
        scene_tab.center().x(), scene_tab.bottom()
    )

    window.close()
    app.setStyleSheet(previous_stylesheet)
    assert center == QColor("#242a32")
    assert active_indicator == QColor("#61b3a2")


def test_scene_documents_are_closable_tabs_inside_the_scene_workspace():
    app = qt_app()
    previous_stylesheet = app.styleSheet()
    root = Path(__file__).resolve().parents[1]
    stylesheet_path = root / "views" / "app_theme.qss"
    app.setStyleSheet(stylesheet_path.read_text(encoding="utf-8"))
    loader = QUiLoader()
    loader.registerCustomWidget(TreeView)
    window = loader.load(str(root / "UI" / "main.ui"))
    window.display_space_controller = DisplaySpaceController(window.sceneViewer)
    setup_menu(window)
    content = QWidget()
    content.setObjectName("entityDetailContent")
    document = window.sceneViewer.addSubWindow(content)
    document.setWindowTitle("Copper (cp)")
    window.show()
    document.show()
    app.processEvents()

    tab_bar = window.sceneViewer.findChild(QTabBar)
    close_button = tab_bar.tabButton(0, QTabBar.ButtonPosition.RightSide)
    assert window.workspaceTabs.tabText(0) == "Scene"
    assert not window.minimize_all_action.isEnabled()
    assert not window.rearrange_grid_action.isEnabled()
    assert window.sceneViewer.tabsClosable()
    assert window.sceneViewer.viewMode() == QMdiArea.ViewMode.TabbedView
    assert tab_bar.count() == 1
    assert close_button is not None
    close_button.click()
    app.processEvents()
    assert not document.isVisible()

    window.close()
    app.setStyleSheet(previous_stylesheet)


def test_frameless_mdi_window_has_sized_controls_and_resize_edges():
    app = qt_app()
    previous_stylesheet = app.styleSheet()
    stylesheet_path = Path(__file__).resolve().parents[1] / "views" / "app_theme.qss"
    app.setStyleSheet(stylesheet_path.read_text(encoding="utf-8"))
    mdi_area = QMdiArea()
    mdi_area.resize(800, 600)
    controller = DisplaySpaceController(mdi_area)
    content = QWidget()
    content.setObjectName("entityDetailContent")
    window = mdi_area.addSubWindow(content)
    window.setWindowTitle("Resizable")
    window.resize(420, 320)
    mdi_area.show()
    window.show()
    controller._track_window(window)
    app.processEvents()

    assert mdi_content_widget(window) is content
    frame = window.widget()
    title_bar = frame.findChild(QWidget, "mdiTitleBar")
    title_color = title_bar.grab().toImage().pixelColor(
        title_bar.width() // 2, title_bar.height() // 2
    )
    content_image = content.grab().toImage()
    content_color = content_image.pixelColor(
        content_image.width() // 2, content_image.height() // 2
    )
    frame_image = frame.grab().toImage()
    outline_color = frame_image.pixelColor(0, frame_image.height() // 2)
    assert title_color == QColor("#3a4654")
    assert content_color == QColor("#20262e")
    assert outline_color == QColor("#9aa8b8")
    buttons = {}
    for button_name in (
        "mdiMinimizeButton",
        "mdiMaximizeButton",
        "mdiCloseButton",
    ):
        button = window.findChild(QToolButton, button_name)
        assert button.width() >= 44
        assert button.height() >= 38
        assert not button.icon().isNull()
        icon_image = button.icon().pixmap(button.iconSize()).toImage()
        assert any(
            icon_image.pixelColor(x, y).alpha()
            for x in range(icon_image.width())
            for y in range(icon_image.height())
        )
        buttons[button_name] = button

    maximize_button = buttons["mdiMaximizeButton"]
    maximize_icon = maximize_button.icon().cacheKey()
    maximize_button.click()
    app.processEvents()
    assert window.isMaximized()
    restore_icon = maximize_button.icon().cacheKey()
    assert restore_icon != maximize_icon
    maximize_button.click()
    app.processEvents()
    assert not window.isMaximized()
    assert maximize_button.icon().cacheKey() == maximize_icon

    frame = window.widget()
    original_width = window.width()
    edge_position = QPoint(frame.width() - 2, frame.height() // 2)
    QTest.mousePress(frame, Qt.MouseButton.LeftButton, pos=edge_position)
    QTest.mouseMove(
        frame,
        QPoint(frame.width() + 38, edge_position.y()),
        delay=10,
    )
    QTest.mouseRelease(
        frame,
        Qt.MouseButton.LeftButton,
        pos=QPoint(frame.width() + 38, edge_position.y()),
    )
    app.processEvents()
    assert window.width() >= original_width + 30

    original = window.geometry()
    right_edge = controller._resize_edges(
        window,
        window.mapToGlobal(QPoint(window.width() - 1, window.height() // 2)),
    )
    assert right_edge & Qt.Edge.RightEdge
    controller._resize_states[window] = (right_edge, QPoint(0, 0), original)
    controller._resize_window(window, QPoint(-500, 0))
    assert window.width() >= 320

    left_edge = controller._resize_edges(
        window, window.mapToGlobal(QPoint(0, window.height() // 2))
    )
    assert left_edge & Qt.Edge.LeftEdge
    buttons["mdiCloseButton"].click()
    app.processEvents()
    assert not window.isVisible()
    window.close()
    mdi_area.close()
    app.setStyleSheet(previous_stylesheet)