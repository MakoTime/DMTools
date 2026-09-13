from typing import Protocol, runtime_checkable


@runtime_checkable
class EntityInspectionMdiContract(Protocol):
    """Contract for a read-only entity inspection hosted in an MDI area."""

    model: object

    def refresh_entity(self, entity: object) -> None:
        ...

    def close_editor(self, reason: str = "window") -> bool:
        ...


@runtime_checkable
class EditableDraftMdiContract(Protocol):
    """Contract for a temporary editable draft hosted in an MDI area."""

    model: object

    def apply_changes(self) -> object:
        ...

    def close_editor(self, reason: str = "window") -> bool:
        ...


@runtime_checkable
class DatabaseWorkspaceMdiContract(Protocol):
    """Contract for a database workspace hosted in an MDI area."""

    model: object

    def refresh_schema(self) -> None:
        ...

    def run_query(self) -> bool:
        ...


@runtime_checkable
class EntityQueryResultsMdiContract(Protocol):
    """Contract for entity query results hosted in an MDI area."""

    model: object

    def selected_entity_uid(self) -> str | None:
        ...

    def open_selected_entity(self) -> object:
        ...

    def navigate_back(self) -> object:
        ...


@runtime_checkable
class TableEditorMdiContract(Protocol):
    """Contract for an editable table hosted in an MDI area."""

    model: object

    def refresh_table(self) -> None:
        ...

    def commit_changes(self) -> bool:
        ...

    def close_editor(self, reason: str = "window") -> bool:
        ...


@runtime_checkable
class ObjectInspectionMdiContract(Protocol):
    """Contract for read-only inspection of a non-entity project object."""

    model: object

    def refresh_object(self) -> None:
        ...

    def close_editor(self, reason: str = "window") -> bool:
        ...
