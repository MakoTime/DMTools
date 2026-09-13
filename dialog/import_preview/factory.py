from .model import ImportPreviewModel
from .view import ImportPreviewView


def create_import_preview(preview, parent=None, duplicate_policy="replace"):
    """Build a confirmation dialog from an immutable dry-run preview."""
    model = ImportPreviewModel(
        preview=preview,
        duplicate_policy=duplicate_policy,
    )
    return ImportPreviewView(model, parent=parent)