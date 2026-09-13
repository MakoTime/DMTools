from projectfoundry import BlockData, BlockObject
from pydantic import Field


class CollectionBlockData(BlockData):
    """Persistent ordered UID references for one entity collection."""

    description: str = ""
    entity_uids: list[str] = Field(default_factory=list)
    dynamic_query_uid: str | None = None


class CollectionBlock(BlockObject):
    """Project-owned collection without duplicated entity payloads."""

    type_name = "collection"

    def __init__(
        self,
        name,
        *,
        description="",
        entity_uids=None,
        dynamic_query_uid=None,
        guid=None,
    ):
        super().__init__(
            name=name,
            guid=guid,
            block_data=CollectionBlockData(
                description=description,
                entity_uids=list(entity_uids or ()),
                dynamic_query_uid=dynamic_query_uid,
            ),
        )

    def prepare(self):
        return self.block_data

    def process(self, prepared, progress_callback=None):
        del progress_callback
        return prepared

    def serialise(self, path):
        del path