from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog

from application.project_serializer import ProjectSerializer
from components.tree import TreeManager, TreeModel
from components.tree.roots.root_objects import root_objects


class ProjectController:
    """Own the tree manager/model and drive project save/load/open.

    This is deliberately decoupled from any specific main window - wire its
    ``tree_model`` into a ``TreeView`` and call the save/open methods from
    menu actions once the application window exists.
    """

    def __init__(self, duplicate_name_dialog=None):
        self.tree_manager = TreeManager()
        self.tree_manager.root_nodes = root_objects.get_nodes()
        self.tree_model = TreeModel(
            self.tree_manager.root_nodes,
            duplicate_name_handler=self._resolve_duplicate_name,
        )
        self.project_serializer = ProjectSerializer()
        self.project_file = None
        self._duplicate_name_dialog = duplicate_name_dialog

    def _resolve_duplicate_name(self, name, object_base):
        next_name = self.tree_model.next_name(name, exclude=object_base)
        if self._duplicate_name_dialog is None:
            return next_name
        dialog = self._duplicate_name_dialog(name, next_name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return next_name

    def new_project(self):
        """Reset to an empty, unsaved project."""
        for node in root_objects.get_nodes():
            node.children.clear()
        self.tree_manager.root_nodes = root_objects.get_nodes()
        self.tree_model.root_data = self.tree_manager.root_nodes
        self.tree_model.refresh()
        self.project_file = None

    def create_project(self, project_directory):
        """Create and save a new project directory."""
        self.new_project()
        self.project_file = self.project_serializer.save(
            project_directory, self.tree_manager
        )
        return self.project_file

    def save_project(self, parent=None):
        """Save the current project to its active project file."""
        if self.project_file is None:
            return self.save_project_as(parent)
        return self.project_serializer.save(self.project_file, self.tree_manager)

    def save_project_as(self, parent=None):
        """Save the current project to a newly selected project file."""
        project_file, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Project As",
            filter="Project files (project.json);;JSON files (*.json)",
        )
        if not project_file:
            return None
        saved_file = self.project_serializer.save(project_file, self.tree_manager)
        self.project_file = saved_file
        return saved_file

    def open_project(self, parent=None):
        """Ask the user for a project file, then load it."""
        project_file, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Project",
            filter="Project files (project.json);;JSON files (*.json)",
        )
        if not project_file:
            return None
        return self.load_project(project_file)

    def load_project(self, project_file):
        """Load a project and make its file the active save target."""
        loaded = self.project_serializer.load(
            project_file, self.tree_manager, self.tree_model
        )
        self.project_file = Path(project_file)
        return loaded
