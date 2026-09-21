from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from application.imports import EntityImportService
from dialog.import_progress.factory import (
    create_import_progress,
    create_import_task_progress,
)
from dialog.import_preview.factory import create_import_preview


class EntityImportController:
    """Coordinate source selection, preview, confirmation, and atomic commit."""

    def __init__(
        self,
        project_controller,
        parent=None,
        *,
        service=None,
        progress_factory=create_import_progress,
        preview_factory=create_import_preview,
        file_chooser=None,
        error_reporter=None,
    ):
        self.project_controller = project_controller
        self.parent = parent
        self.service = service or EntityImportService()
        self.progress_factory = progress_factory
        self.preview_factory = preview_factory
        self.file_chooser = file_chooser or self._choose_file
        self.error_reporter = error_reporter or self._report_error

    @property
    def can_import(self):
        return (
            self.project_controller.project_file is not None
            and self.project_controller.project.artifact_store is not None
        )

    def import_xml(self):
        return self._choose_and_import("xml")

    def import_json(self):
        return self._choose_and_import("json")

    def _choose_and_import(self, source_format):
        if not self.can_import:
            self.error_reporter("Open a project before importing entities.")
            return None
        source = self.file_chooser(source_format)
        if not source:
            return None
        return self.import_source(Path(source), source_format)

    def import_source(self, source, source_format, *, duplicate_policy="replace"):
        existing = self.project_controller.entity_source_identities("compendium")
        existing_entities = tuple(
            self.project_controller.entity_source_records(namespace)
            for namespace in ("compendium", "homebrew")
        )
        existing_entities = tuple(
            entity for namespace_records in existing_entities for entity in namespace_records
        )
        progress_dialog = self.progress_factory(
            self.project_controller.task_runner,
            self.service,
            source,
            source_format,
            duplicate_policy=duplicate_policy,
            existing_source_identities=existing,
            existing_entities=existing_entities,
            parent=self.parent,
        )
        if progress_dialog.exec() != QDialog.DialogCode.Accepted:
            if progress_dialog.model.error:
                self.error_reporter(progress_dialog.model.error)
            return None
        preview = progress_dialog.model.preview
        dialog = self.preview_factory(
            preview,
            parent=self.parent,
            duplicate_policy=duplicate_policy,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        try:
            destination = dialog.model.destination
            duplicate_policy = dialog.model.duplicate_policy
            self.service.commit(
                preview,
                lambda records: records,
                skip_invalid=getattr(dialog.model, "skip_invalid", False),
            )
            records = preview.records
            database_store = self.project_controller.entity_database_store(destination)
            task_dialog = create_import_task_progress(
                self.project_controller.task_runner,
                lambda set_progress: self.project_controller.persist_imported_entities(
                    records,
                    namespace=destination,
                    duplicate_policy=duplicate_policy,
                    database_path=database_store.database_path,
                    progress_callback=lambda current, total: set_progress(
                        current / total if total else 0.0
                    ),
                ),
                Path(source).name,
                operation_name="Writing imported entities...",
                parent=self.parent,
            )
            if task_dialog.exec() != QDialog.DialogCode.Accepted:
                if task_dialog.model.error:
                    self.error_reporter(task_dialog.model.error)
                return None
            count = self.project_controller.commit_imported_entities(
                records,
                namespace=destination,
                duplicate_policy=duplicate_policy,
                persist=False,
            )
            if (
                source_format.casefold() == "xml"
                and destination == "compendium"
                and self.project_controller.project_file is not None
            ):
                self.project_controller.save_entity_namespace_json("compendium")
                self.project_controller.save_project()
        except (OSError, RuntimeError, ValueError) as error:
            self.error_reporter(str(error))
            return None
        return count

    def _choose_file(self, source_format):
        filters = {
            "xml": "XML files (*.xml)",
            "json": "JSON files (*.json)",
        }
        path, _ = QFileDialog.getOpenFileName(
            self.parent,
            f"Import from {source_format.upper()}",
            filter=filters[source_format],
        )
        return path

    def _report_error(self, message):
        QMessageBox.warning(self.parent, "Entity Import", message)