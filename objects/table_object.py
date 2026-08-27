from pathlib import Path

import pandas as pd

from .object_base import ObjectBase, ObjectData


class TableDataObject(ObjectBase):
    """A project object whose payload is a pandas DataFrame."""

    type_name = "table"

    def __init__(self, name, data: pd.DataFrame | None = None, **kwargs):
        super().__init__(name, **kwargs)
        self.object_data = ObjectData(data if data is not None else pd.DataFrame())

    @property
    def data(self):
        return self.object_data.value

    @data.setter
    def data(self, value):
        self.object_data.value = value

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item.update(self.object_data.to_json(
            project_directory,
            filename=f"{self.guid}.csv",
            writer=lambda path, value: value.to_csv(path, index=False),
        ))
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        table = ObjectData.from_json(
            data, project_directory, loader=pd.read_csv
        ).value
        return cls(
            name=data["name"],
            data=table if table is not None else pd.DataFrame(),
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
