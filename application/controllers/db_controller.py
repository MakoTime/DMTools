from typing import Optional

from PySide6.QtWidgets import QDialog, QTreeView, QWidget

from common.icons import get_icon
from components.tree.model import TreeNode, TreeModel
from components.tree.roots.db_root import database_root
from components.tree.roots.root_objects import root_objects
from dialog.db_base.factory import create_database_dialog
from dialog.db_base.model import DatabaseModel
from dialog.database.factory import create_database_workspace
from objects.database_object import DatabaseObject
from objects.query_object import QueryObject
from tools.dropdown.factory import create_dropdown_menu

class DataBaseController:
    """Create, edit and remove database entries in a QTreeView dialog."""
    
    def __init__(self, tree_view: QTreeView, parent: Optional[QWidget] = None):
        self.tree_view = tree_view
        self.parent = parent
        tree_model = tree_view.model()
        if isinstance(tree_model, TreeModel):
            tree_model.root_data = root_objects.get_nodes()
            tree_model.refresh()
        
        if hasattr(tree_view, "add_context_menu_factory"):
            tree_view.add_context_menu_factory(self._create_context_menu_for_index)
        elif hasattr(tree_view, "set_context_menu_factory"):
            tree_view.set_context_menu_factory(self._create_context_menu_for_index)
            
    def _create_context_menu_for_index(self, index, parent):
        return self.create_context_menu(index.internalPointer(), parent)
    
    def create_context_menu(self, node: TreeNode, parent=None):
        options = []
        if node is database_root:
            options.append(("New Database", self.create_database))
        elif isinstance(node.node_object, DatabaseObject):
            options.extend(
                (
                    ("Open", lambda: self.open_database(node.node_object)),
                    ("Edit", lambda: self.edit(node.node_object)),
                    ("Delete", lambda: self.delete(node.node_object), get_icon("bin")),
                )
            )
        elif isinstance(node.node_object, QueryObject):
            options.extend(
                (
                    ("Open", lambda: self.open_query(node.node_object)),
                    ("Delete", lambda: self.delete_query(node.node_object), get_icon("bin")),
                )
            )
        return create_dropdown_menu(options, parent)

    def open_database(self, database_object):
        """Open the database workspace in the main window's MDI area."""
        mdi_area = self.parent.sceneViewer
        workspace = create_database_workspace(database_object, parent=mdi_area)
        subwindow = mdi_area.addSubWindow(workspace)
        subwindow.setWindowTitle(database_object.name)
        subwindow.resize(900, 650)
        subwindow.show()
        return subwindow

    def open_query(self, query_object):
        """Open the owning database workspace with a saved query selected."""
        node = query_object.node.parent
        database_object = node.node_object if node is not None else None
        if not isinstance(database_object, DatabaseObject):
            return None
        subwindow = self.open_database(database_object)
        workspace = subwindow.widget()
        for index in range(workspace.query_list.count()):
            if workspace.query_list.itemData(index) is query_object:
                workspace.query_list.setCurrentIndex(index)
                break
        return subwindow
    
    def create_database(self):
        """Open the editor and register the confirmed database definition."""
        project_file = getattr(
            getattr(self.parent, "project_controller", None), "project_file", None
        )
        project_directory = project_file.parent if project_file else None
        dialog = create_database_dialog(
            parent=self.parent,
            project_directory=project_directory,
            is_new=True,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return self._register(dialog.update_model().to_object())
    
    def edit(self, database_object):
        dialog = create_database_dialog(
            model=DatabaseModel.from_object(database_object),
            parent=self.parent,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.update_model()
            database_object._on_name_changed(updated.name)
            database_object.database_path = updated.database_path
            database_object.queries = [
                {"name": query.name, "sql": query.sql}
                for query in updated.queries
                if query.sql.strip()
            ]
            self._refresh_and_select(database_object)
            
    def delete(self, database_object):
        database_object.remove_from_tree()
        self.tree_view.model().refresh()

    def delete_query(self, query_object):
        database_node = query_object.node.parent
        if database_node is None or not isinstance(database_node.node_object, DatabaseObject):
            return
        database = database_node.node_object
        database.query_objects = [query for query in database.query_objects if query is not query_object]
        query_object.remove_from_tree()
        database._changed()
        self.tree_view.model().refresh()
    
    def _refresh_and_select(self, database):
        tree_model = self.tree_view.model()
        if not isinstance(tree_model, TreeModel):
            return
        tree_model.refresh()
        if database is None:
            return
        root_index = tree_model.index(
            tree_model.root_data.index(database_root),
            0,
        )
        child_index = tree_model.index(
            database_root.children.index(database.node),
            0,
            root_index,
        )
        self.tree_view.expand(root_index)
        self.tree_view.setCurrentIndex(child_index)
        self.tree_view.scrollTo(child_index)

    def _register(self, database_object):
        database_object.add_to_tree(None, database_root)
        self._refresh_and_select(database_object)
        return database_object
        
    def _tree_search(self):
        from components.tree import TreeSearch

        return TreeSearch(root_objects.get_nodes())