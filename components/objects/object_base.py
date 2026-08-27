
from contextlib import contextmanager
from typing import Any, Optional
from uuid import uuid4

from PySide6.QtGui import QIcon

from components.tree.model import TreeNode
from components.tree.roots.root_objects import root_objects


class ObjectBase:
    """Base class for project objects that live directly in the tree."""
    def __init__(
        self,
        name: str,
        icon: Optional[QIcon] = None,
        metadata: Optional[dict[str, Any]] = None,
        scene_data: Any = None,
        guid: Optional[str] = None,
        auto_register_root: bool = True,
    ):
        self.name = name
        self.guid = guid or str(uuid4())
        self.icon = icon if icon is not None else QIcon()
        self.metadata = metadata if metadata is not None else {}
        self.scene_data = scene_data
        self._scene = None
        self._table_manager = None
        self._change_depth = 0
        self._destroyed = False

        self.node = TreeNode(
            name=self.name,
            icon=self.icon,
            node_object=self,
        )
        if auto_register_root:
            root_objects.add(self.node)

    def add_to_tree(self, tree_manager, parent=None):
        """Add this object's tree node as a root or child node."""
        if parent is None:
            tree_manager.add_root_node(self.node)
        elif self.node.parent is not parent:
            parent.add_child(self.node)
        return self.node

    def add_to_scene(self, scene):
        """Add this object to a scene container."""
        if self._scene is scene:
            return self
        self._scene = scene
        if hasattr(scene, "add_object"):
            scene.add_object(self)
        elif hasattr(scene, "add"):
            scene.add(self)
        elif hasattr(scene, "append"):
            scene.append(self)
        else:
            raise TypeError(
                "scene must provide add_object(), add(), or append()"
            )
        return self

    def remove_from_scene(self):
        """Remove this object from its registered scene, if any."""
        if self._scene is None or not hasattr(self._scene, "remove_object"):
            return False
        removed = self._scene.remove_object(self)
        if removed:
            self._scene = None
        return removed

    def remove_from_tree(self):
        """Remove this object's node from its current tree parent or roots."""
        return root_objects.remove_object(self)

    def destroy(self):
        """Destroy this object and its engine block, then remove its views."""
        if self._destroyed:
            return self
        self._destroyed = True
        block = getattr(self, "block_object", None)
        if block is not None and not block.is_destroyed():
            block.destroy()
        self._detach_representations()
        return self

    def _detach_representations(self):
        """Remove scene, table, and tree representations owned by this object."""
        self.remove_from_scene()
        self.remove_from_tree()
        for child in tuple(self.node.children):
            self.node.remove_child(child)

    def register(self, table_manager=None, tree_manager=None, scene=None, parent=None):
        """Register this object with any supplied table, tree, and scene targets."""
        if tree_manager is not None:
            self.add_to_tree(tree_manager, parent)
        if scene is not None:
            self.add_to_scene(scene)
        return self

    @contextmanager
    def _changing(self):
        """Allow only the outermost change to update object state."""
        if self._change_depth:
            yield False
            return

        self._change_depth += 1
        try:
            yield True
        finally:
            self._change_depth -= 1

    def _on_name_changed(self, name):
        """Handle changes in name."""
        with self._changing() as is_outermost:
            if not is_outermost:
                return
            self.name = name
            if self.node is not None:
                self.node.name = name

    def _on_icon_changed(self, icon):
        """Handle changes in icon."""
        with self._changing() as is_outermost:
            if not is_outermost:
                return
            self.icon = icon if icon is not None else QIcon()
            if self.node is not None:
                self.node.icon = self.icon
                
from objects.object_base import ObjectData
        

    

    

