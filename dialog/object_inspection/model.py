from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable

from dialog.base.editor import EditorModel


@dataclass(init=False)
class ObjectInspectionModel(EditorModel):
    """UID-backed, read-only metadata for a non-entity project object."""

    def __init__(
        self,
        inspected_object=None,
        *,
        object_uid=None,
        object_loader: Callable[[str], object] | None = None,
    ):
        if inspected_object is None and (object_uid is None or object_loader is None):
            raise ValueError("An object or UID-backed object loader is required")
        self._object = inspected_object
        self.object_uid = object_uid or getattr(inspected_object, "guid", None)
        if not self.object_uid:
            raise ValueError("An inspected object UID is required")
        self._object_loader = object_loader

    @property
    def inspected_object(self):
        if self._object is None:
            self._object = self._object_loader(self.object_uid)
        return self._object

    def release_object(self):
        if self._object_loader is not None:
            self._object = None

    @property
    def title(self):
        return str(getattr(self.inspected_object, "name", self.object_uid))

    @property
    def details(self):
        inspected = self.inspected_object
        if isinstance(inspected, Mapping):
            values = dict(inspected)
        elif hasattr(inspected, "block_data"):
            values = inspected.block_data.model_dump(mode="json")
        else:
            values = {
                key: value
                for key, value in vars(inspected).items()
                if not key.startswith("_") and not callable(value)
            }
        values.setdefault("UID", self.object_uid)
        return values

    @property
    def formatted_details(self):
        return json.dumps(self.details, indent=2, sort_keys=True, default=str)
