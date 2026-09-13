from projectfoundry import ArtifactMetadata, BlockData, BlockObject


class EntityDatabaseBlockData(BlockData):
    """Metadata for a project-managed, queryable entity database."""

    namespace: str
    schema_version: int = 1
    row_count: int = 0


class EntityDatabaseBlock(BlockObject):
    """Persistent identity for a namespace's SQLite entity artifact."""

    type_name = "entity_database"

    def __init__(
        self,
        name,
        *,
        namespace,
        schema_version=1,
        row_count=0,
        artifact=None,
        guid=None,
    ):
        artifact = artifact or ArtifactMetadata(
            path=f"data/{namespace}.sqlite",
            format="sqlite",
            valid=False,
        )
        super().__init__(
            name=name,
            guid=guid or f"dmtools-{namespace}-entity-database",
            block_data=EntityDatabaseBlockData(
                artifact=artifact,
                namespace=namespace,
                schema_version=schema_version,
                row_count=row_count,
            ),
        )

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        del progress_callback
        return prepared

    def serialise(self, path):
        del path