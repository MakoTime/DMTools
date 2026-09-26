from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from application.imports import EntityImportService
from api.adaptor import SRDAdaptor
from api.client import SRDClient
from dialog.srd_import.factory import create_srd_import_dialog
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
        srd_client=None,
        srd_adaptor=None,
    ):
        self.project_controller = project_controller
        self.parent = parent
        self.service = service or EntityImportService()
        self.progress_factory = progress_factory
        self.preview_factory = preview_factory
        self.file_chooser = file_chooser or self._choose_file
        self.error_reporter = error_reporter or self._report_error
        self.srd_client = srd_client or SRDClient()
        self.srd_adaptor = srd_adaptor or SRDAdaptor()

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

    def import_srd_all(self):
        return self.import_srd(collections=self.srd_client.collections())

    def import_srd_collection(self, collection):
        return self.import_srd(collections=(collection,))

    def import_srd_custom(self):
        if not self.can_import:
            self.error_reporter("Open a project before importing entities.")
            return None
        dialog = create_srd_import_dialog(self.srd_client, parent=self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return self.import_srd(
            collections=(dialog.model.collection,),
            query=dialog.model.query,
        )

    def import_srd(self, *, collections, query=None, duplicate_policy="replace"):
        if not self.can_import:
            self.error_reporter("Open a project before importing entities.")
            return None
        existing = self.project_controller.entity_source_identities("compendium")
        existing_entities = tuple(
            entity
            for namespace in ("compendium", "homebrew")
            for entity in self.project_controller.entity_source_records(namespace)
        )

        collection_list = tuple(collections)
        collection_count = len(collection_list) or 1

        def prepare_preview(set_progress, is_cancelled, set_status):
            records = []
            set_status("Discovering 5eSRD resources")
            for collection_index, collection in enumerate(collection_list):
                set_status(f"Fetching {collection} and recursive URLs")

                def report_collection_progress(current, total):
                    fraction = current / total if total else 0.0
                    global_current = round(
                        (collection_index + fraction) * 1000
                    )
                    set_progress(global_current, collection_count * 1000)

                resources = self.srd_client.fetch_collection_resources(
                    collection,
                    query=query,
                    is_cancelled=is_cancelled,
                    progress_callback=report_collection_progress,
                )
                set_status(f"Adapting {collection} resources")
                for resource in resources:
                    payload = resource["payload"]
                    try:
                        records.append(
                            self.srd_adaptor.record(
                                resource["collection"],
                                payload,
                                parent=resource["parent"],
                            )
                        )
                    except Exception as error:  # noqa: BLE001 - report resource context
                        resource_name = (
                            payload.get("name") or payload.get("index") or "unnamed"
                        )
                        resource_url = payload.get("url", "unknown URL")
                        raise ValueError(
                            f"Failed adapting {resource['collection']} "
                            f"'{resource_name}' ({resource_url}): {error}"
                        ) from error
                if is_cancelled():
                    return self.service.preview_api(
                        [],
                        duplicate_policy=duplicate_policy,
                        existing_source_identities=existing,
                        existing_entities=existing_entities,
                    )
            set_progress(collection_count * 1000, collection_count * 1000)
            set_status("Validating normalized API records")
            return self.service.preview_api(
                records,
                duplicate_policy=duplicate_policy,
                existing_source_identities=existing,
                existing_entities=existing_entities,
            )

        progress_dialog = create_import_task_progress(
            self.project_controller.task_runner,
            prepare_preview,
            ", ".join(collections) or "5eSRD Online",
            operation_name="Fetching and validating 5eSRD entities...",
            parent=self.parent,
        )
        if progress_dialog.exec() != QDialog.DialogCode.Accepted:
            if progress_dialog.model.error:
                self.error_reporter(progress_dialog.model.error)
            return None
        preview = progress_dialog.model.result
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
                lambda batch: batch,
                skip_invalid=getattr(dialog.model, "skip_invalid", False),
            )
            database_store = self.project_controller.entity_database_store(destination)

            def persist_records(set_progress, is_cancelled):
                del is_cancelled
                return self.project_controller.persist_imported_entities(
                    preview.records,
                    namespace=destination,
                    duplicate_policy=duplicate_policy,
                    database_path=database_store.database_path,
                    progress_callback=set_progress,
                )

            task_dialog = create_import_task_progress(
                self.project_controller.task_runner,
                persist_records,
                "5eSRD Online",
                operation_name="Writing imported entities...",
                parent=self.parent,
            )
            if task_dialog.exec() != QDialog.DialogCode.Accepted:
                if task_dialog.model.error:
                    self.error_reporter(task_dialog.model.error)
                return None
            count = self.project_controller.commit_imported_entities(
                preview.records,
                namespace=destination,
                duplicate_policy=duplicate_policy,
                persist=False,
            )
            if destination == "compendium" and self.project_controller.project_file is not None:
                self.project_controller.save_entity_namespace_json(destination)
                self.project_controller.save_project()
            return count
        except (OSError, RuntimeError, ValueError) as error:
            self.error_reporter(str(error))
            return None

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