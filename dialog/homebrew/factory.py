from typing import Optional

from PySide6.QtWidgets import QWidget

from .model import create_homebrew_editor_model
from .mdi_view import HomebrewEditorMdiView
from .view import HomebrewEditorView


def create_homebrew_dialog(entity_type, draft=None, parent: Optional[QWidget] = None):
    """Create the shared editor configured for one canonical entity type."""
    model = create_homebrew_editor_model(entity_type, draft=draft)
    return HomebrewEditorView(model, parent=parent)


def create_homebrew_mdi_view(
    entity_type,
    draft=None,
    *,
    on_accept=None,
    on_clone=None,
    parent: Optional[QWidget] = None,
):
    """Create a modeless Homebrew editor for a QMdiArea subwindow."""
    model = create_homebrew_editor_model(entity_type, draft=draft)
    return HomebrewEditorMdiView(
        model,
        on_accept=on_accept,
        on_clone=on_clone,
        parent=parent,
    )