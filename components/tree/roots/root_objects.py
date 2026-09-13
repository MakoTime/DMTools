from ..model import TreeNode
from .collections_root import collections_root
from .db_root import database_root
from .entity_roots import compendium_root, homebrew_root


class RootObjects:
    """Singleton registry for nodes displayed at the tree root."""

    def __init__(self):
        self.nodes = [database_root, compendium_root, homebrew_root, collections_root]
        self._protected_nodes = set(self.nodes)

    def reset(self):
        """Restore persistent roots and empty their project-owned contents."""
        database_root.children.clear()
        database_root.child_uids.clear()
        compendium_root.reset()
        homebrew_root.reset()
        collections_root.children.clear()
        collections_root.child_uids.clear()
        self.nodes = [database_root, compendium_root, homebrew_root, collections_root]
        return self.nodes

    def node_for_uid(self, uid):
        for root in self.nodes:
            if root.uid == uid:
                return root
            for child in root.children:
                if child.uid == uid:
                    return child
        return None

    def ensure_tree_roots(self, tree_manager):
        """Keep persistent roots present and ordered ahead of custom roots."""
        persistent_uids = {node.uid for node in self.nodes}
        extras = [
            node
            for node in tree_manager.root_nodes
            if node.uid not in persistent_uids
        ]
        tree_manager.root_nodes = [*self.nodes, *extras]
        return tree_manager.root_nodes

    def add(self, node: TreeNode):
        if node not in self.nodes:
            self.nodes.append(node)
        return node

    def protect(self, node: TreeNode):
        """Keep a persistent root node from being removed."""
        self._protected_nodes.add(node)
        return self.add(node)

    def remove(self, node: TreeNode):
        if node in self._protected_nodes:
            return False
        if node not in self.nodes:
            return False
        self.nodes.remove(node)
        return True

    def remove_object(self, node_object):
        """Remove all tree nodes representing a project object."""
        removed = False
        for root in tuple(self.nodes):
            if root.node_object is node_object:
                removed = self.remove(root) or removed
                continue
            removed = root.remove_object_nodes(node_object) or removed
        return removed

    def get_nodes(self):
        # self._ensure_special_roots_last()
        return self.nodes

    def get_visible_nodes(self):
        """Return roots intended for the main project tree."""
        return [node for node in self.nodes if node is not database_root]

    # def _ensure_special_roots_last(self):
    #     """Keep persistent category roots ordered before WorldConfig."""
    #     from .world_config_root import world_config

    #     for node in (database_root, world_config.node):
    #         if node in self.nodes:
    #             self.nodes.remove(node)
    #     self.nodes.extend((database_root, world_config.node))


root_objects = RootObjects()