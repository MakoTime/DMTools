from common.icons import get_icon
from components.tree.model import TreeNode


class CollectionsRoot(TreeNode):
    """Protected root for project-owned entity collections."""

    node_type = "collections_root"
    protected = True

    def __init__(self):
        super().__init__(
            "Collections",
            icon=get_icon("folder"),
            uid="dmtools-collections-root",
        )


collections_root = CollectionsRoot()