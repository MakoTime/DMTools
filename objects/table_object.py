import pandas as pd
from projectfoundry import ArtifactMetadata, BlockData, BlockObject
from pydantic import Field

from .object_base import PayloadStore, ProjectObject


def _read_csv(path):
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


class TableBlockData(BlockData):
    """ProjectFoundry metadata for a disk-backed table artifact."""

    row_count: int = 0
    columns: list[str] = Field(default_factory=list)


class TableBlock(BlockObject):
    """Persistent table identity whose DataFrame is stored as a CSV artifact."""

    type_name = "table"

    def __init__(
        self,
        name,
        *,
        row_count=0,
        columns=None,
        artifact=None,
        guid=None,
    ):
        data = TableBlockData(
            artifact=artifact,
            row_count=row_count,
            columns=list(columns or []),
        )
        if data.artifact is None:
            data.artifact = ArtifactMetadata(
                path=f"artifacts/{guid or 'pending'}.csv",
                format="csv",
                valid=False,
            )
        super().__init__(name=name, guid=guid, block_data=data)
        if "pending" in data.artifact.path:
            data.artifact = data.artifact.model_copy(
                update={"path": f"artifacts/{self.guid}.csv"}
            )

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        del progress_callback
        return prepared

    def persist_result(self, result, path):
        if not isinstance(result, pd.DataFrame):
            raise TypeError("Table artifacts require a pandas DataFrame")
        result.to_csv(path, index=False)

    @staticmethod
    def load_artifact(path):
        return _read_csv(path)

    def serialise(self, path):
        del path


class TableDataObject(ProjectObject):
    """A project object whose payload is a pandas DataFrame."""

    type_name = "table"

    def __init__(self, name, data: pd.DataFrame | None = None, **kwargs):
        super().__init__(name, **kwargs)
        initial_data = data.copy() if data is not None else pd.DataFrame()
        self._draft_data = initial_data if data is not None else None
        self.block_object = TableBlock(
            self.name,
            row_count=len(initial_data.index),
            columns=[str(column) for column in initial_data.columns],
            guid=self.guid,
        )

    @property
    def data(self):
        if self._draft_data is not None:
            return self._draft_data
        project = getattr(self.block_object, "_project", None)
        artifact = self.block_object.block_data.artifact
        if project is not None and artifact.valid:
            return project.load_block_artifact(
                self.block_object.guid, self.block_object.load_artifact
            )
        return pd.DataFrame()

    @data.setter
    def data(self, value):
        self._draft_data = value.copy()
        artifact = self.block_object.block_data.artifact.model_copy(
            update={"valid": False}
        )
        self.block_object.block_data = TableBlockData(
            artifact=artifact,
            row_count=len(value.index),
            columns=[str(column) for column in value.columns],
        )
        self.block_object.mark_changed()

    def release_data(self):
        """Release the editable DataFrame after a successful artifact commit."""
        self._draft_data = None

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        payload = PayloadStore(self.data)
        item.update(payload.to_json(
            project_directory,
            filename=f"{self.guid}.csv",
            writer=lambda path, value: value.to_csv(path, index=False),
        ))
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        table = PayloadStore.from_json(
            data, project_directory, loader=_read_csv
        ).value
        return cls(
            name=data["name"],
            data=table if table is not None else pd.DataFrame(),
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
