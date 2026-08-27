import json
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

from PySide6.QtGui import QIcon

from components.tree.model import TreeNode


class ObjectData:
    """Persist an object's inline JSON data or an external project payload."""

    DATA_DIRECTORY = "data"

    def __init__(self, value: Any = None):
        self.value = value

    def to_json(
        self,
        project_directory,
        filename: str | None = None,
        writer: Callable[[Path, Any], None] | None = None,
    ) -> dict[str, Any]:
        if filename is None:
            return {"data": self.value}
        data_directory = Path(project_directory) / self.DATA_DIRECTORY
        data_directory.mkdir(parents=True, exist_ok=True)
        path = data_directory / filename
        if writer is None:
            path.write_text(json.dumps(self.value, indent=2), encoding="utf-8")
        else:
            writer(path, self.value)
        return {"data_file": f"{self.DATA_DIRECTORY}/{path.name}"}

    @classmethod
    def from_json(
        cls,
        item: dict[str, Any],
        project_directory,
        loader: Callable[[Path], Any] | None = None,
    ) -> "ObjectData":
        data_file = item.get("data_file")
        if data_file is None:
            return cls(item.get("data"))
        path = Path(project_directory) / data_file
        value = (
            json.loads(path.read_text(encoding="utf-8"))
            if loader is None
            else loader(path)
        )
        return cls(value)


class ObjectBase:
    """Base class for project objects that live directly in the tree.

    Subclasses represent a single kind of project data (JSON, a pandas
    table, or a SQLite database) and are responsible for exporting and
    restoring their own payload alongside the shared JSON metadata.
    """

    type_name = "object"

    def __init__(
        self,
        name: str,
        icon: Optional[QIcon] = None,
        visible: bool = True,
        metadata: Optional[dict[str, Any]] = None,
        guid: Optional[str] = None,
    ):
        self.name = name
        self.guid = guid or str(uuid4())
        self.icon = icon if icon is not None else QIcon()
        self.visible = visible
        self.metadata = metadata if metadata is not None else {}
        self.object_data = ObjectData()
        self.node = TreeNode(name=self.name, icon=self.icon, node_object=self)

    def add_to_tree(self, tree_manager, parent=None):
        """Add this object's tree node as a root or child node."""
        if parent is None:
            tree_manager.add_root_node(self.node)
        elif self.node.parent is not parent:
            parent.add_child(self.node)
        return self.node

    def remove_from_tree(self):
        """Detach this object's node from its current tree parent."""
        parent = self.node.parent
        return parent.remove_child(self.node) if parent is not None else False

    def _on_name_changed(self, name):
        """Handle a rename triggered through the tree model."""
        self.name = name
        self.node.name = name

    def to_json(self, project_directory) -> dict[str, Any]:
        """Return this object's metadata as a JSON-serialisable dict.

        Subclasses should extend this result with their own payload,
        writing any large data into ``project_directory`` as needed.
        """
        return {
            "type": self.type_name,
            "guid": self.guid,
            "name": self.name,
            "visible": self.visible,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any], project_directory):
        """Rebuild an object from its serialised metadata."""
        return cls(
            name=data["name"],
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
