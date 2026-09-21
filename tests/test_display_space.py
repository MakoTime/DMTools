from PySide6.QtWidgets import QApplication, QMainWindow, QMdiArea, QWidget

from application.display_space import DisplaySpaceController
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