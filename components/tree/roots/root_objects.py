from ..model import TreeNode
from .db_root import database_root


class RootObjects:
    """Singleton registry for nodes displayed at the tree root."""

    def __init__(self):
        self.nodes = [database_root]
        self._protected_nodes = set(self.nodes)

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

    # def _ensure_special_roots_last(self):
    #     """Keep persistent category roots ordered before WorldConfig."""
    #     from .world_config_root import world_config

    #     for node in (database_root, world_config.node):
    #         if node in self.nodes:
    #             self.nodes.remove(node)
    #     self.nodes.extend((database_root, world_config.node))


root_objects = RootObjects()