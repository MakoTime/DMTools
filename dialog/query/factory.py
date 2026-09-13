from typing import Optional

from PySide6.QtWidgets import QWidget

from .model import QueryEditorModel
from .view import QueryEditorView


def create_query_dialog(
    model: Optional[QueryEditorModel] = None,
    parent: Optional[QWidget] = None,
) -> QueryEditorView:
    """Create a saved-query editor from temporary draft state."""
    return QueryEditorView(model or QueryEditorModel(), parent=parent)