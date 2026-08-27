from .model import DatabaseModel
from .view import DatabaseView
from typing import Optional
from PySide6.QtWidgets import QWidget
    
def create_database_dialog(
    model: Optional[DatabaseModel] = None,
    parent: Optional[QWidget] = None,
    project_directory=None,
    is_new=False,
) -> DatabaseView:
    """Build the database creation or editing dialog."""
    return DatabaseView(
        model=model or DatabaseModel(),
        parent=parent,
        project_directory=project_directory,
        is_new=is_new,
    )
