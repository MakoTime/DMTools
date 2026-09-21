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
    existing_entities=(),
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
        existing_entities=tuple(existing_entities),
        source_name=Path(source).name,
    )
    return ImportProgressView(model, parent=parent)


def create_import_task_progress(
    task_runner,
    work,
    source_name,
    *,
    operation_name,
    parent=None,
):
    model = ImportProgressModel(
        task_runner=task_runner,
        service=None,
        source=None,
        source_format="",
        duplicate_policy="",
        existing_source_identities=(),
        existing_entities=(),
        source_name=source_name,
        work=work,
        operation_name=operation_name,
    )
    return ImportProgressView(model, parent=parent)