from __future__ import annotations

import json
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from components.tree.roots.entity_roots import canonical_entity_type
from parsers.dispatcher import dispatch_root
from parsers.xml_parser import parse_xml

from .record import ImportIssue, ImportPreview, ImportedEntityRecord
from .registry import ENTITY_REGISTRY
from application.entity_references import normalize_entity_references


ENTITY_UID_NAMESPACE = UUID("4950ffdc-9787-4b80-95ad-634caf79ca51")


class EntityImportService:
    """Validate complete entity batches without owning persistence or Qt state."""

    def __init__(self, registry=None):
        self.registry = registry or ENTITY_REGISTRY

    def preview_xml(
        self,
        source,
        *,
        source_name: str | None = None,
        duplicate_policy: str = "reject",
        existing_source_identities: Collection[str] = (),
        existing_entities=(),
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> ImportPreview:
        provenance = source_name or self._source_name(source, "XML input")
        self._report_status(status_callback, "Reading and parsing XML structure")
        root = parse_xml(source)
        self._report_status(status_callback, "Parsing source entities")
        results = dispatch_root(
            root,
            is_cancelled=is_cancelled,
            progress_callback=progress_callback,
        )
        if is_cancelled is not None and is_cancelled():
            return ImportPreview(tuple(), tuple(), provenance, cancelled=True)
        self._report_status(status_callback, "Validating normalized records")
        return self._preview_results(
            results,
            provenance,
            duplicate_policy,
            existing_source_identities,
            existing_entities,
            is_cancelled,
            progress_callback,
            status_callback,
        )

    def preview_json(
        self,
        source,
        *,
        source_name: str | None = None,
        duplicate_policy: str = "reject",
        existing_source_identities: Collection[str] = (),
        existing_entities=(),
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> ImportPreview:
        self._report_status(status_callback, "Reading and parsing JSON document")
        document, inferred_name = self._json_document(source)
        provenance = source_name or inferred_name
        entries = self._json_entries(document)
        self._report_status(status_callback, "Normalizing JSON entities")
        results = [self._json_result(entry) for entry in entries]
        self._report_status(status_callback, "Validating normalized records")
        return self._preview_results(
            results,
            provenance,
            duplicate_policy,
            existing_source_identities,
            existing_entities,
            is_cancelled,
            progress_callback,
            status_callback,
        )

    @staticmethod
    def commit(
        preview: ImportPreview,
        commit_batch: Callable[[tuple], Any],
        *,
        skip_invalid: bool = False,
    ):
        """Publish one validated batch through a transaction-owning callback."""
        if not skip_invalid and not preview.can_commit:
            raise ValueError("Import preview contains blocking issues")
        if preview.cancelled or not preview.records:
            raise ValueError("Import preview has no valid records to commit")
        return commit_batch(preview.records)

    def _preview_results(
        self,
        results,
        provenance,
        duplicate_policy,
        existing_source_identities,
        existing_entities,
        is_cancelled,
        progress_callback,
        status_callback,
    ):
        if duplicate_policy not in {"reject", "skip", "replace"}:
            raise ValueError(f"Unsupported duplicate policy: {duplicate_policy}")
        records = []
        issues = []
        record_indexes = {}
        existing = set(existing_source_identities)
        total = len(results)
        for index, result in enumerate(results):
            if is_cancelled is not None and is_cancelled():
                return ImportPreview(tuple(), tuple(issues), provenance, cancelled=True)
            if progress_callback is not None:
                progress_callback(index, total)
            status = result.get("status", "success")
            entity_type = result.get("entity_type", result.get("tag"))
            name = result.get("display_name", result.get("name"))
            if status != "success":
                issues.append(
                    self._issue(index, entity_type, name, status, result, provenance)
                )
                continue
            try:
                entity_type = canonical_entity_type(entity_type)
                definition = self.registry[entity_type]
                payload = definition.validate_payload(
                    result.get("payload", result.get("data", {}))
                )
                name = name or payload.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("Entity requires a display name")
                source_identity = result.get("source_identity") or (
                    f"{provenance}:{entity_type}:{name.strip().casefold()}"
                )
                record = ImportedEntityRecord(
                    entity_type=entity_type,
                    uid=result.get("uid") or str(uuid5(ENTITY_UID_NAMESPACE, source_identity)),
                    source_identity=source_identity,
                    display_name=name.strip(),
                    payload=payload,
                    source_metadata=dict(result.get("source_metadata", {})),
                    provenance=result.get("provenance", provenance),
                )
            except Exception as error:  # noqa: BLE001 - preserve record-level validation errors
                issues.append(
                    ImportIssue(
                        index=index,
                        entity_type=entity_type,
                        display_name=name,
                        status="failed",
                        error=str(error),
                        source_location=f"{provenance} record {index + 1}",
                    )
                )
                continue
            duplicate_index = record_indexes.get(record.source_identity)
            is_existing = record.source_identity in existing
            if duplicate_index is not None or is_existing:
                if duplicate_policy == "reject":
                    issues.append(
                        ImportIssue(
                            index=index,
                            entity_type=record.entity_type,
                            display_name=record.display_name,
                            status="duplicate",
                            error=f"Duplicate source identity: {record.source_identity}",
                            source_location=f"{provenance} record {index + 1}",
                        )
                    )
                    continue
                if duplicate_policy == "skip":
                    issues.append(
                        ImportIssue(
                            index=index,
                            entity_type=record.entity_type,
                            display_name=record.display_name,
                            status="skipped",
                            error=f"Skipped source identity: {record.source_identity}",
                            source_location=f"{provenance} record {index + 1}",
                            blocking=False,
                        )
                    )
                    continue
                if duplicate_index is not None:
                    records[duplicate_index] = record
                    continue
            record_indexes[record.source_identity] = len(records)
            records.append(record)
        self._report_status(status_callback, "Resolving entity references")
        records = normalize_entity_references(
            records,
            existing_entities,
            is_cancelled=is_cancelled,
            progress_callback=progress_callback,
        )
        if is_cancelled is not None and is_cancelled():
            return ImportPreview(tuple(), tuple(issues), provenance, cancelled=True)
        if progress_callback is not None and not total:
            progress_callback(total, total)
        updated_count = sum(
            record.source_identity in existing for record in records
        )
        return ImportPreview(
            records,
            tuple(issues),
            provenance,
            created_count=len(records) - updated_count,
            updated_count=updated_count,
        )

    @staticmethod
    def _issue(index, entity_type, name, status, result, provenance):
        return ImportIssue(
            index=index,
            entity_type=entity_type,
            display_name=name,
            status=status,
            error=result.get("error", f"Entity status is {status}"),
            source_location=f"{provenance} record {index + 1}",
        )

    @staticmethod
    def _report_status(callback, status):
        if callback is not None:
            callback(status)

    @staticmethod
    def _source_name(source, fallback):
        if isinstance(source, Path):
            return str(source.resolve())
        if isinstance(source, str) and "<" not in source:
            return str(Path(source).resolve())
        return fallback

    @staticmethod
    def _json_document(source):
        if isinstance(source, Path):
            return json.loads(source.read_text(encoding="utf-8")), str(source.resolve())
        if isinstance(source, str):
            stripped = source.lstrip()
            if stripped.startswith(("{", "[")):
                return json.loads(source), "JSON input"
            path = Path(source)
            return json.loads(path.read_text(encoding="utf-8")), str(path.resolve())
        return source, "JSON input"

    @staticmethod
    def _json_entries(document):
        if isinstance(document, list):
            return document
        if not isinstance(document, dict):
            raise ValueError("JSON import must contain an object or array")
        for key in ("records", "entities", "results"):
            if key in document:
                if not isinstance(document[key], list):
                    raise ValueError(f"JSON {key} must be an array")
                return document[key]
        return [document]

    @staticmethod
    def _json_result(entry):
        if not isinstance(entry, dict):
            return {
                "status": "failed",
                "error": "JSON entity record must be an object",
            }
        result = dict(entry)
        result.setdefault("status", "success")
        entity_type = result.get("entity_type", result.get("tag", result.get("type")))
        result["entity_type"] = entity_type
        if "payload" not in result and "data" not in result:
            metadata_fields = {
                "entity_type",
                "tag",
                "type",
                "uid",
                "source_identity",
                "display_name",
                "status",
                "source_metadata",
                "provenance",
            }
            result["payload"] = {
                key: value for key, value in entry.items() if key not in metadata_fields
            }
        return result