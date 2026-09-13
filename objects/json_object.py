from typing import Any

from projectfoundry import BlockData, BlockObject
from pydantic import Field

from .object_base import PayloadStore, ProjectObject


class JSONBlockData(BlockData):
    """ProjectFoundry metadata for an inline JSON object."""

    data: dict[str, Any] = Field(default_factory=dict)


class JSONBlock(BlockObject):
    """Registration block for an inline JSON object."""

    type_name = "json"

    def __init__(self, name, data=None, guid=None):
        super().__init__(
            name=name,
            guid=guid,
            block_data=JSONBlockData(data=dict(data or {})),
        )

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        del prepared, progress_callback

    def serialise(self, path):
        del path


class JSONDataObject(ProjectObject):
    """A project object whose payload is arbitrary JSON-serialisable data."""

    type_name = "json"

    def __init__(self, name, data: dict[str, Any] | None = None, **kwargs):
        super().__init__(name, **kwargs)
        self.object_data = PayloadStore(data if data is not None else {})
        self.block_object = JSONBlock(self.name, self.object_data.value, guid=self.guid)

    @property
    def data(self):
        return self.object_data.value

    @data.setter
    def data(self, value):
        self.object_data.value = value
        self.block_object.block_data.data = dict(value or {})
        self.block_object.mark_changed()

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item.update(self.object_data.to_json(project_directory))
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        return cls(
            name=data["name"],
            data=PayloadStore.from_json(data, project_directory).value or {},
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
