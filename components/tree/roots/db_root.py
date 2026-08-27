from ..model import TreeNode
from common.icons import get_icon


class DatabaseRoot(TreeNode):
    """Persistent root category for database objects."""

    def __init__(self):
        super().__init__(
            name="Databases",
            icon=get_icon("folder"),
            parent=None,
            node_object=None,
        )


database_root = DatabaseRoot()