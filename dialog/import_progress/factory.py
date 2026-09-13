from pathlib import Path

from .model import ImportProgressModel
from .view import ImportProgressView


def create_import_progress(
    task_runner,
    service,
    source,
    source_format,
    *,
    duplicate_policy,
    existing_source_identities,
    parent=None,
):
    """Build a modal progress dialog around a ProjectFoundry task."""
    model = ImportProgressModel(
        task_runner=task_runner,
        service=service,
        source=source,
        source_format=source_format,
        duplicate_policy=duplicate_policy,
        existing_source_identities=tuple(existing_source_identities),
        source_name=Path(source).name,
    )
    return ImportProgressView(model, parent=parent)