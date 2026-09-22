from dataclasses import dataclass

@dataclass(frozen=True)
class UnresolvedReferenceChoice:
    entity_type: str
    display_fallback: str
    path: str

    @property
    def label(self):
        return f"{self.display_fallback} ({self.entity_type}; {self.path})"


class ResolveReferencesModel:
    """Draft state for resolving stored unresolved entity references."""

    def __init__(self, entity, project_controller):
        self.entity = entity
        self.project_controller = project_controller
        self.references = tuple(
            UnresolvedReferenceChoice(
                diagnostic["entity_type"],
                diagnostic["display_fallback"],
                diagnostic["path"],
            )
            for diagnostic in (entity.source_metadata.get("reference_diagnostics", ()) or ())
        )
        self.candidates = tuple(
            row
            for namespace in ("compendium", "homebrew")
            if project_controller.project.blocks.contains(
                f"dmtools-{namespace}-entity-database"
            )
            for row in project_controller.entity_database_store(namespace).all_records()
        )
        self.reference_index = 0
        self.target_uid = None
        self.result = ()

    @property
    def selected_reference(self):
        if not self.references:
            return None
        return self.references[self.reference_index]

    def filtered_candidates(self, text=""):
        query = str(text).strip().casefold()
        return tuple(
            candidate
            for candidate in self.candidates
            if not query
            or query in candidate.name.casefold()
            or query in candidate.entity_type.casefold()
            or query in candidate.source_namespace.casefold()
        )

    def apply(self):
        reference = self.selected_reference
        if reference is None:
            raise ValueError("There are no unresolved references to resolve")
        if self.target_uid is None:
            raise ValueError("Select an entity to resolve this reference")
        self.result = self.project_controller.resolve_unresolved_reference(
            reference.entity_type,
            reference.display_fallback,
            self.target_uid,
        )
        return self.result
