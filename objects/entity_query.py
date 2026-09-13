from typing import Any, Literal

from projectfoundry import BlockData, BlockObject
from pydantic import Field


class EntityQueryBlockData(BlockData):
    """Versioned safe-query definition for one entity category."""

    database_uid: str
    entity_type: str
    field: str = "name"
    operator: str = "all"
    value: Any = None
    sort_field: str = "name"
    sort_order: Literal["asc", "desc"] = "asc"
    projection: list[str] = Field(default_factory=lambda: ["name"])
    format_version: int = 1


class EntityQueryBlock(BlockObject):
    """Project-owned saved query that never stores arbitrary SQL."""

    type_name = "entity_saved_query"

    def __init__(
        self,
        name,
        *,
        database_uid,
        entity_type,
        field="name",
        operator="all",
        value=None,
        sort_field="name",
        sort_order="asc",
        projection=None,
        format_version=1,
        guid=None,
    ):
        super().__init__(
            name=name,
            guid=guid,
            block_data=EntityQueryBlockData(
                database_uid=database_uid,
                entity_type=entity_type,
                field=field,
                operator=operator,
                value=value,
                sort_field=sort_field,
                sort_order=sort_order,
                projection=list(projection or ["name"]),
                format_version=format_version,
            ),
        )

    def prepare(self):
        return self.block_data

    def process(self, prepared, progress_callback=None):
        del progress_callback
        return prepared

    def serialise(self, path):
        del path