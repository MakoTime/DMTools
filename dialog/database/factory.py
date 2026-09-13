from typing import Optional

from PySide6.QtWidgets import QWidget

from .model import DatabaseWorkspaceModel
from .view import DatabaseWorkspaceView


def create_database_workspace(
    database_object=None,
    parent: Optional[QWidget] = None,
    *,
    database_uid=None,
    database_loader=None,
) -> DatabaseWorkspaceView:
    """Create a database workspace view from its editor model."""
    model = (
        database_object
        if isinstance(database_object, DatabaseWorkspaceModel)
        else DatabaseWorkspaceModel(
            database_object=database_object,
            database_uid=database_uid,
            database_loader=database_loader,
        )
    )
    return DatabaseWorkspaceView(model, parent=parent)
