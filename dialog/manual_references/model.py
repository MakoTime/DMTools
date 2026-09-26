from __future__ import annotations

from dataclasses import dataclass

from dialog.base.editor import EditorModel


@dataclass(frozen=True)
class ReferenceEntry:
    source_uid: str
    source_name: str
    source_type: str
    source_namespace: str
    path: str
    reference_type: str
    display_fallback: str
    status: str
    target_uid: str | None = None
    target_name: str | None = None
    target_namespace: str | None = None
    is_manual: bool = False

    @property
    def label(self):
        return f"{self.display_fallback} ({self.reference_type})"

    @property
    def source_label(self):
        return f"{self.source_name} ({self.source_type}; {self.source_namespace})"


class ManualReferencesModel(EditorModel):
    """Workspace model for reviewing and resolving stored entity references."""

    def __init__(self, project_controller):
        self.project_controller = project_controller
        self.references = ()
        self.candidates = ()
        self.selected_reference = None
        self.refresh()

    def _stores(self):
        for namespace in ("compendium", "homebrew"):
            block_uid = f"dmtools-{namespace}-entity-database"
            if self.project_controller.project.blocks.contains(block_uid):
                yield namespace, self.project_controller.entity_database_store(namespace)

    def refresh(self):
        records = []
        candidates = []
        for namespace, store in self._stores():
            rows = tuple(store.all_records())
            candidates.extend(rows)
            records.extend((namespace, row) for row in rows)

        target_by_uid = {row.uid: row for row in candidates}
        references = []
        for namespace, row in records:
            metadata = row.source_metadata or {}
            seen_resolved = set()
            manual_keys = {
                (reference.get("path", ""), reference.get("target_uid"))
                for reference in metadata.get("manual_entity_references", ()) or ()
            }
            resolved_references = [
                *(metadata.get("entity_references", ()) or ()),
                *(metadata.get("manual_entity_references", ()) or ()),
            ]
            for reference in resolved_references:
                resolved_key = (
                    reference.get("path", ""),
                    reference.get("target_uid"),
                )
                if resolved_key in seen_resolved:
                    continue
                seen_resolved.add(resolved_key)
                target = target_by_uid.get(reference.get("target_uid"))
                references.append(
                    ReferenceEntry(
                        source_uid=row.uid,
                        source_name=row.name,
                        source_type=row.entity_type,
                        source_namespace=namespace,
                        path=reference.get("path", ""),
                        reference_type=reference.get("entity_type", ""),
                        display_fallback=reference.get("display_fallback", ""),
                        status="resolved",
                        target_uid=reference.get("target_uid"),
                        target_name=target.name if target else reference.get("target_uid"),
                        target_namespace=(
                            target.source_namespace if target else reference.get("source_namespace")
                        ),
                        is_manual=resolved_key in manual_keys,
                    )
                )
            for diagnostic in metadata.get("reference_diagnostics", ()) or ():
                references.append(
                    ReferenceEntry(
                        source_uid=row.uid,
                        source_name=row.name,
                        source_type=row.entity_type,
                        source_namespace=namespace,
                        path=diagnostic.get("path", ""),
                        reference_type=diagnostic.get("entity_type", ""),
                        display_fallback=diagnostic.get("display_fallback", ""),
                        status="unresolved",
                    )
                )

        self.references = tuple(references)
        self.candidates = tuple(candidates)
        if self.selected_reference not in self.references:
            self.selected_reference = self.references[0] if self.references else None
        return self.references

    def filtered_references(self, status="all", text=""):
        query = str(text).strip().casefold()
        return tuple(
            reference
            for reference in self.references
            if (
                status == "all"
                or (status == "manual" and reference.is_manual)
                or (status == "resolved" and reference.status == "resolved")
                or (status == "unresolved" and reference.status == "unresolved")
            )
            and (
                not query
                or query in reference.display_fallback.casefold()
                or query in reference.source_name.casefold()
                or query in reference.path.casefold()
                or query in reference.reference_type.casefold()
            )
        )

    def filtered_candidates(self, text="", entity_type=None):
        query = str(text).strip().casefold()
        return tuple(
            candidate
            for candidate in self.candidates
            if (entity_type is None or candidate.entity_type == entity_type)
            and (
                not query
                or query in candidate.name.casefold()
                or query in candidate.entity_type.casefold()
                or query in candidate.source_namespace.casefold()
            )
        )

    def resolve(self, target_uids):
        reference = self.selected_reference
        if reference is None or reference.status != "unresolved":
            raise ValueError("Select an unresolved reference first")
        if isinstance(target_uids, str):
            target_uids = (target_uids,)
        else:
            target_uids = tuple(target_uids or ())
        if not target_uids:
            raise ValueError("Select at least one entity to match this reference")
        target_argument = target_uids[0] if len(target_uids) == 1 else target_uids
        result = self.project_controller.resolve_unresolved_reference(
            reference.reference_type,
            reference.display_fallback,
            target_argument,
        )
        self.refresh()
        return result

    def mark_intended(self):
        reference = self.selected_reference
        if reference is None or reference.status != "unresolved":
            raise ValueError("Select an unresolved reference first")
        result = self.project_controller.mark_reference_intended(
            reference.source_uid, reference.path
        )
        if not result:
            raise ValueError("The unresolved reference could not be found")
        self.refresh()
        return result
