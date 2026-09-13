from dataclasses import dataclass
from typing import Callable

from dialog.base.editor import EditorModel


@dataclass(init=False)
class EntityDetailModel(EditorModel):
    """Read-only presentation state for one canonical entity row."""

    def __init__(
        self,
        entity=None,
        *,
        entity_uid=None,
        entity_loader: Callable[[str], object] | None = None,
    ):
        if entity is None and (entity_uid is None or entity_loader is None):
            raise ValueError("An entity or UID-backed entity loader is required")
        self._entity = entity
        self.entity_uid = entity_uid or entity.uid
        self._entity_loader = entity_loader

    @property
    def entity(self):
        if self._entity is None:
            self._entity = self._entity_loader(self.entity_uid)
        return self._entity

    @property
    def is_lazy(self):
        return self._entity_loader is not None

    def release_entity(self):
        if self.is_lazy:
            self._entity = None

    @property
    def title(self):
        return self.entity.name

    @property
    def details(self):
        return {
            "Type": self.entity.entity_type,
            "Source": self.entity.source_namespace,
            "UID": self.entity.uid,
            "Data": self.entity.payload,
        }
