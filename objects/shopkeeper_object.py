from .object_base import ObjectBase, ObjectData


class ShopkeeperObject(ObjectBase):
    """A configured consumer of one database and its saved queries."""

    type_name = "shopkeeper"

    def __init__(
        self,
        name,
        database_guid=None,
        query_guids=None,
        filters=None,
        stock_count=10,
        random_seed=None,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.database_guid = database_guid
        self.query_guids = list(query_guids or [])
        self.filters = dict(filters or {})
        self.stock_count = int(stock_count)
        self.random_seed = random_seed
        self.last_database_revision = None
        self.inventory_stale = True
        self.object_data = ObjectData()

    def bind_database(self, database_object):
        """Mark inventory stale whenever its source database changes."""
        self.database_guid = database_object.guid
        self.last_database_revision = database_object.revision
        database_object.add_change_callback(self._on_database_changed)
        self.inventory_stale = True

    def _on_database_changed(self, database_object):
        self.last_database_revision = database_object.revision
        self.inventory_stale = True

    def to_json(self, project_directory):
        item = super().to_json(project_directory)
        item["database_guid"] = self.database_guid
        item["query_guids"] = list(self.query_guids)
        item["filters"] = dict(self.filters)
        item["stock_count"] = self.stock_count
        item["random_seed"] = self.random_seed
        return item

    @classmethod
    def from_json(cls, data, project_directory):
        return cls(
            name=data["name"],
            database_guid=data.get("database_guid"),
            query_guids=data.get("query_guids", []),
            filters=data.get("filters", {}),
            stock_count=data.get("stock_count", 10),
            random_seed=data.get("random_seed"),
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
            guid=data.get("guid"),
        )
