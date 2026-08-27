from typing import Optional

from PySide6.QtWidgets import QWidget

from .model import DatabaseWorkspaceModel
from .view import DatabaseWorkspaceView


def create_database_workspace(
    database_object,
    parent: Optional[QWidget] = None,
) -> DatabaseWorkspaceView:
    """Create a database workspace view from its editor model."""
    model = DatabaseWorkspaceModel(database_object=database_object)
    return DatabaseWorkspaceView(model, parent=parent)
