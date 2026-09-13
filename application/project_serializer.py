import json
from pathlib import Path

from application.project_version import CURRENT_PROJECT_VERSION, upgrade_project_data
from components.tree.model import TreeNode
from components.tree.roots.db_root import database_root
from components.tree.roots.root_objects import root_objects
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
    """Save and load a project tree with namespace data in shareable files.

    Every project object lives directly in the tree, so the tree's
    parent/child structure doubles as the persisted project structure -
    there is no separate task or block bookkeeping to reconcile.
    """

    def save(self, project_path, tree_manager, framework_document=None):
        requested_path = Path(project_path)
        if requested_path.suffix.lower() == ".json":
            directory = requested_path.parent
            project_file = requested_path
        else:
            directory = requested_path
            project_file = directory / PROJECT_FILE
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "data").mkdir(exist_ok=True)
        self._namespace_payloads = {}
        data = {
            "version": CURRENT_PROJECT_VERSION,
            "roots": [
                self._serialize_node(node, directory, namespace=None)
                for node in tree_manager.get_root_nodes()
            ],
        }
        if self._namespace_payloads:
            data["data_files"] = {
                namespace: f"data/{namespace}.json"
                for namespace in sorted(self._namespace_payloads)
            }
            for namespace, payloads in self._namespace_payloads.items():
                self._atomic_write_json(
                    directory / "data" / f"{namespace}.json", payloads
                )
        existing_data_files = {
            namespace: f"data/{namespace}.json"
            for namespace in ("compendium", "homebrew")
            if (directory / "data" / f"{namespace}.json").is_file()
        }
        if existing_data_files:
            data.setdefault("data_files", {}).update(existing_data_files)
        if framework_document is not None:
            data["framework"] = framework_document
        self._atomic_write_json(project_file, data)
        return project_file

    def load(self, project_path, tree_manager, tree_model=None):
        project_file = Path(project_path)
        data = upgrade_project_data(
            json.loads(project_file.read_text(encoding="utf-8"))
        )
        directory = project_file.parent
        self._namespace_payloads = self._load_namespace_payloads(data, directory)
        root_objects.reset()
        tree_manager.root_nodes = []
        loaded = [
            self._deserialize_node(item, directory, tree_manager, parent=None)
            for item in data.get("roots", [])
        ]
        root_objects.ensure_tree_roots(tree_manager)
        if tree_model is not None:
            tree_model.root_data = tree_manager.get_root_nodes()
            tree_model.refresh()
        return loaded

    def _serialize_node(self, node, project_directory, namespace):
        namespace = getattr(node, "namespace", None) or namespace
        object_base = node.node_object
        if object_base is None:
            item = {"type": "folder", "name": node.name, "uid": node.uid}
            for field in ("node_type", "namespace", "entity_type", "protected"):
                value = getattr(node, field, None)
                if value is not None:
                    item[field] = value
        else:
            item = object_base.to_json(project_directory)
            if (
                item.get("type") == JSONDataObject.type_name
                and namespace in {"compendium", "homebrew"}
                and "data" in item
            ):
                self._namespace_payloads.setdefault(namespace, {})[object_base.guid] = item.pop("data")
                item["data_file"] = f"data/{namespace}.json"
                item["data_key"] = object_base.guid
        item["children"] = [
            self._serialize_node(child, project_directory, namespace)
            for child in node.children
        ]
        return item

    def _deserialize_node(self, item, project_directory, tree_manager, parent):
        object_type = item.get("type")
        if object_type == "folder":
            node = root_objects.node_for_uid(item.get("uid"))
            if node is None:
                node = database_root if item.get("name") == database_root.name else TreeNode(
                    name=item.get("name", "Folder"), uid=item.get("uid")
                )
            for field in ("node_type", "namespace", "entity_type", "protected"):
                if field in item:
                    setattr(node, field, item[field])
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
        item = self._with_external_payload(item, project_directory)
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

    def _load_namespace_payloads(self, document, project_directory):
        payloads = {}
        for namespace, relative_path in document.get("data_files", {}).items():
            if namespace not in {"compendium", "homebrew"}:
                raise ValueError(f"Unsupported project data namespace: {namespace}")
            path = (project_directory / relative_path).resolve()
            if project_directory.resolve() not in path.parents:
                raise ValueError(f"Project data file escapes project directory: {relative_path}")
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"Project data file must contain an object: {relative_path}")
            payloads[namespace] = value
        return payloads

    def _with_external_payload(self, item, project_directory):
        if item.get("data_key") is None or item.get("data_file") is None:
            return item
        relative_path = item["data_file"]
        path = (project_directory / relative_path).resolve()
        if project_directory.resolve() not in path.parents:
            raise ValueError(f"Project data file escapes project directory: {relative_path}")
        namespace = Path(relative_path).stem
        payloads = self._namespace_payloads.get(namespace, {})
        key = item["data_key"]
        if key not in payloads:
            raise ValueError(f"Missing payload {key} in project data file {relative_path}")
        restored = dict(item)
        restored.pop("data_file", None)
        restored.pop("data_key", None)
        restored["data"] = payloads[key]
        return restored

    @staticmethod
    def _atomic_write_json(path, value):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(path)
