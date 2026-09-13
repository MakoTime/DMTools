from components.tree.roots.root_objects import root_objects

from .project_tree import rebuild_project_tree


class LegacyTreeProjectionAdapter:
    """Expose legacy root nodes as a projection of a canonical Project tree."""

    def __init__(self, project, roots=root_objects):
        self.project = project
        self.roots = roots

    def refresh(self):
        return rebuild_project_tree(self.project, self.roots.get_nodes())

    def roots_for_compatibility(self):
        return self.roots.get_nodes()
