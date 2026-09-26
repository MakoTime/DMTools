from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from application import ProjectController
from application.controllers.entity_controller import EntityTreeController
from application.controllers.import_controller import EntityImportController
from application.display_space import DisplaySpaceController
from application.file_window import FileWindow, ProjectPackageAdapter, ProjectPreview
from components.tree import TreeView
from menu import setup_menu


BASE_DIRECTORY = Path(__file__).resolve().parent.parent


def load_main_window(project_file):
    """Construct and wire one project window around an active controller."""
    project_file = Path(project_file)
    if project_file.is_dir():
        project_file = project_file / "project.json"
    if not project_file.is_file():
        raise FileNotFoundError(project_file)

    loader = QUiLoader()
    loader.registerCustomWidget(TreeView)
    window = loader.load(str(BASE_DIRECTORY / "UI" / "main.ui"))
    if window is None:
        raise RuntimeError(loader.errorString())

    controller = ProjectController()
    window.treeWidget.setModel(controller.project_tree_model)
    controller.load_project(project_file)
    display_space_controller = DisplaySpaceController(window.sceneViewer, parent=window)
    window.display_space_controller = display_space_controller
    import_controller = EntityImportController(controller, parent=window)
    entity_controller = EntityTreeController(
        window.treeWidget,
        controller,
        import_controller,
        parent=window,
    )
    setup_menu(
        window,
        import_controller,
        controller,
        on_open_entity=entity_controller.open_entity_and_reveal,
    )
    window.open_action.triggered.connect(
        lambda checked=False: controller.open_project(window)
    )
    window.save_action.triggered.connect(
        lambda checked=False: controller.save_project(window)
    )
    window.save_as_action.triggered.connect(
        lambda checked=False: controller.save_project_as(window)
    )
    window.project_controller = controller
    window.import_controller = import_controller
    window.entity_controller = entity_controller
    return window


def load_file_window():
    """Construct the project launcher from its Designer UI."""
    loader = QUiLoader()
    loader.registerCustomWidget(ProjectPreview)
    window = loader.load(str(BASE_DIRECTORY / "UI" / "file_window.ui"))
    if window is None:
        raise RuntimeError(loader.errorString())
    return FileWindow(window)


class ApplicationLauncher:
    """Compose launcher, project windows, and application-level commands."""

    def __init__(self, argv=None):
        self.argv = list(sys.argv if argv is None else argv)
        self.app = QApplication(self.argv)
        self.file_window = load_file_window()
        self.project_windows = []
        self.file_window.on_project_opened = self.open_project
        self.file_window.on_project_created = self.create_project

    @staticmethod
    def _project_file(project_directory):
        return ProjectPackageAdapter.from_selection(project_directory).project_file

    def open_project(self, project_directory):
        project_file = self._project_file(project_directory)
        if not project_file.is_file():
            return None
        self.file_window.close()
        window = load_main_window(project_file)
        self.project_windows.append(window)
        window.show()
        return window

    def create_project(self, project_directory):
        controller = ProjectController()
        project_file = controller.create_project(project_directory)
        self.file_window.close()
        window = load_main_window(project_file)
        self.project_windows.append(window)
        window.show()
        return window

    def run(self):
        self.file_window.show()
        try:
            return self.app.exec()
        finally:
            for window in self.project_windows:
                controller = getattr(window, "project_controller", None)
                if controller is not None:
                    controller.close()
