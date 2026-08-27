import json
from pathlib import Path

from application.project_version import CURRENT_PROJECT_VERSION, upgrade_project_data
from components.tree.model import TreeNode
from components.tree.roots.db_root import database_root
from objects.database_object import DatabaseObject
from objects.query_object import QueryObject
from objects.json_object import JSONDataObject
from objects.table_object import TableDataObject
from objects.shopkeeper_object import ShopkeeperObject


PROJECT_FILE = "project.json"

OBJECT_TYPES = {
    JSONDataObject.type_name: JSONDataObject,
    TableDataObject.type_name: TableDataObject,
    DatabaseObject.type_name: DatabaseObject,
    QueryObject.type_name: QueryObject,
    ShopkeeperObject.type_name: ShopkeeperObject,
}


class ProjectSerializer:
    """Save and load a project as a single JSON tree of objects.

    Every project object lives directly in the tree, so the tree's
    parent/child structure doubles as the persisted project structure -
    there is no separate task or block bookkeeping to reconcile.
    """

    def save(self, project_path, tree_manager):
        requested_path = Path(project_path)
        if requested_path.suffix.lower() == ".json":
            directory = requested_path.parent
            project_file = requested_path
        else:
            directory = requested_path
            project_file = directory / PROJECT_FILE
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "data").mkdir(exist_ok=True)
        data = {
            "version": CURRENT_PROJECT_VERSION,
            "roots": [
                self._serialize_node(node, directory)
                for node in tree_manager.get_root_nodes()
            ],
        }
        project_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return project_file

    def load(self, project_path, tree_manager, tree_model=None):
        project_file = Path(project_path)
        data = upgrade_project_data(
            json.loads(project_file.read_text(encoding="utf-8"))
        )
        directory = project_file.parent
        for node in tree_manager.get_root_nodes():
            node.children.clear()
        tree_manager.root_nodes = []
        loaded = [
            self._deserialize_node(item, directory, tree_manager, parent=None)
            for item in data.get("roots", [])
        ]
        if tree_model is not None:
            tree_model.root_data = tree_manager.get_root_nodes()
            tree_model.refresh()
        return loaded

    def _serialize_node(self, node, project_directory):
        object_base = node.node_object
        if object_base is None:
            item = {"type": "folder", "name": node.name}
        else:
            item = object_base.to_json(project_directory)
        item["children"] = [
            self._serialize_node(child, project_directory) for child in node.children
        ]
        return item

    def _deserialize_node(self, item, project_directory, tree_manager, parent):
        object_type = item.get("type")
        if object_type == "folder":
            node = database_root if item.get("name") == database_root.name else TreeNode(
                name=item.get("name", "Folder")
            )
            if parent is None:
                tree_manager.add_root_node(node)
            else:
                parent.add_child(node)
            for child_item in item.get("children", []):
                self._deserialize_node(
                    child_item, project_directory, tree_manager, parent=node
                )
            return node
        try:
            object_class = OBJECT_TYPES[object_type]
        except KeyError as error:
            raise TypeError(
                f"Unsupported project object type: {object_type}"
            ) from error
        object_base = object_class.from_json(item, project_directory)
        object_base.add_to_tree(tree_manager, parent)
        if parent is not None and object_type == QueryObject.type_name:
            parent_object = parent.node_object
            if isinstance(parent_object, DatabaseObject):
                parent_object.query_objects.append(object_base)
        for child_item in item.get("children", []):
            self._deserialize_node(
                child_item, project_directory, tree_manager, object_base.node
            )
        return object_base
