import sys
from pathlib import Path

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from application import ProjectController
from application.controllers.db_controller import DataBaseController
from application.file_window import FileWindow, ProjectPreview
from components.tree import TreeView
from menu import setup_menu


def load_main_window(project_file=None):
	"""Load the main Designer UI and connect its project controller."""
	if project_file is None:
		raise ValueError("A saved project directory is required")
	project_file = Path(project_file)
	if project_file.is_dir():
		project_file = project_file / "project.json"
	if not project_file.is_file():
		raise FileNotFoundError(project_file)
	loader = QUiLoader()
	loader.registerCustomWidget(TreeView)
	ui_path = Path(__file__).parent / "UI" / "main.ui"
	window = loader.load(str(ui_path))
	if window is None:
		raise RuntimeError(loader.errorString())

	controller = ProjectController()
	window.treeWidget.setModel(controller.tree_model)
	database_controller = DataBaseController(window.treeWidget, parent=window)
	setup_menu(window)
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
	window.database_controller = database_controller

	if project_file is not None:
		controller.load_project(project_file)
	return window


def load_file_window():
	"""Load the project launcher from its Designer UI."""
	loader = QUiLoader()
	loader.registerCustomWidget(ProjectPreview)
	ui_path = Path(__file__).parent / "UI" / "file_window.ui"
	window = loader.load(str(ui_path))
	if window is None:
		raise RuntimeError(loader.errorString())
	return FileWindow(window)


def main():
	app = QApplication(sys.argv)
	file_window = load_file_window()
	project_windows = []

	def open_project(project_directory):
		project_path = Path(project_directory)
		project_file = (
			project_path
			if project_path.name == "project.json"
			else project_path / "project.json"
		)
		if not project_file.is_file():
			return
		file_window.close()
		window = load_main_window(project_file)
		project_windows.append(window)
		window.show()

	def create_project(project_directory):
		controller = ProjectController()
		project_file = controller.create_project(project_directory)
		file_window.close()
		window = load_main_window(project_file)
		project_windows.append(window)
		window.show()

	file_window.on_project_opened = open_project
	file_window.on_project_created = create_project
	file_window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
