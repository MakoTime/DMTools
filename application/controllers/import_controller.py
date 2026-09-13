from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from application.imports import EntityImportService
from dialog.import_progress.factory import create_import_progress
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
        progress_dialog = self.progress_factory(
            self.project_controller.task_runner,
            self.service,
            source,
            source_format,
            duplicate_policy=duplicate_policy,
            existing_source_identities=existing,
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
            count = self.service.commit(
                preview,
                lambda records: self.project_controller.commit_imported_entities(
                    records,
                    namespace=dialog.model.destination,
                    duplicate_policy=dialog.model.duplicate_policy,
                ),
                skip_invalid=getattr(dialog.model, "skip_invalid", False),
            )
            if (
                source_format.casefold() == "xml"
                and dialog.model.destination == "compendium"
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