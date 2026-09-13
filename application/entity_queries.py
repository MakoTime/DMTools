from dataclasses import dataclass

from application.entity_database import EntityDatabaseStore
from objects.entity_query import EntityQueryBlock


@dataclass(frozen=True)
class QuickQueryTemplate:
    name: str
    entity_type: str
    field: str
    operator: str
    sort_field: str = "name"


BUILTIN_QUERIES = {
    "item_weight": QuickQueryTemplate("Items by Weight", "item", "weight", "lte", "weight"),
    "spell_level": QuickQueryTemplate("Spells by Level", "spell", "level", "eq", "level"),
    "monster_challenge_rating": QuickQueryTemplate(
        "Monsters by Challenge Rating",
        "monster",
        "challenge_rating",
        "eq",
        "challenge_rating",
    ),
}


class EntityQueryFactory:
    """Construct only query definitions supported by an entity category."""

    def __init__(self, field_projections=None):
        self.field_projections = field_projections or EntityDatabaseStore.FIELD_PROJECTIONS

    def fields_for(self, entity_type):
        try:
            return tuple(self.field_projections[entity_type])
        except KeyError as error:
            raise ValueError(f"Unsupported entity type: {entity_type}") from error

    def create(
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
        fields = self.fields_for(entity_type)
        if field not in fields:
            raise ValueError(f"Unsupported field for {entity_type}: {field}")
        if sort_field not in fields:
            raise ValueError(f"Unsupported sort field for {entity_type}: {sort_field}")
        if operator not in {*EntityDatabaseStore.OPERATORS, "all"}:
            raise ValueError(f"Unsupported query operator: {operator}")
        projection = list(projection or ["name"])
        invalid = [item for item in projection if item not in fields]
        if invalid:
            raise ValueError(f"Unsupported projection for {entity_type}: {invalid[0]}")
        return EntityQueryBlock(
            name.strip() or "Query",
            database_uid=database_uid,
            entity_type=entity_type,
            field=field,
            operator=operator,
            value=value,
            sort_field=sort_field,
            sort_order=sort_order,
            projection=projection,
            format_version=format_version,
            guid=guid,
        )

    def builtin(self, key, *, database_uid, value):
        try:
            template = BUILTIN_QUERIES[key]
        except KeyError as error:
            raise ValueError(f"Unknown built-in query: {key}") from error
        return self.create(
            template.name,
            database_uid=database_uid,
            entity_type=template.entity_type,
            field=template.field,
            operator=template.operator,
            value=value,
            sort_field=template.sort_field,
        )

    def name_search(self, entity_type, *, database_uid, value):
        return self.create(
            f"{entity_type.title()} Name Search",
            database_uid=database_uid,
            entity_type=entity_type,
            field="name",
            operator="contains",
            value=value,
        )

    @staticmethod
    def execute(store, query_block, limit=100):
        data = query_block.block_data
        if data.database_uid != store.block.guid:
            raise ValueError("Saved query belongs to another entity database")
        return store.query(
            data.entity_type,
            field=data.field,
            operator=data.operator,
            value=data.value,
            sort_field=data.sort_field,
            sort_order=data.sort_order,
            limit=limit,
        )