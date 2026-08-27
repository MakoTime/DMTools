from typing import Any

from .object_base import ObjectBase, ObjectData


class JSONDataObject(ObjectBase):
    """A project object whose payload is arbitrary JSON-serialisable data."""

    type_name = "json"

    def __init__(self, name, data: dict[str, Any] | None = None, **kwargs):
        super().__init__(name, **kwargs)
        self.object_data = ObjectData(data if data is not None else {})

    @property
    def data(self):
        return self.object_data.value

    @data.setter
    def data(self, value):
        self.object_data.value = value

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item.update(self.object_data.to_json(project_directory))
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        return cls(
            name=data["name"],
            data=ObjectData.from_json(data, project_directory).value or {},
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
