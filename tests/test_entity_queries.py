from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore
from PySide6.QtWidgets import QApplication

from application.entity_database import EntityDatabaseStore
from application.entity_queries import BUILTIN_QUERIES, EntityQueryFactory
from application.imports import EntityImportService
from application.project_controller import ProjectController
from dialog.entity_query_results import create_entity_query_results


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def item_records():
    first = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    second = replace(
        first,
        uid="second-item",
        source_identity="rules:item:heavy-pack",
        display_name="Heavy Pack",
        payload={**first.payload, "name": "Heavy Pack", "weight": 10},
    )
    return first, second


def qt_app():
    return QApplication.instance() or QApplication([])


def test_builtin_query_metadata_and_category_fields_are_validated():
    factory = EntityQueryFactory()

    query = factory.builtin(
        "item_weight",
        database_uid="database",
        value=5,
    )

    assert set(BUILTIN_QUERIES) == {
        "item_weight",
        "spell_level",
        "monster_challenge_rating",
    }
    assert query.block_data.format_version == 1
    assert query.block_data.field == "weight"
    assert query.block_data.sort_field == "weight"
    with pytest.raises(ValueError, match="Unsupported field for spell"):
        factory.create(
            "Invalid",
            database_uid="database",
            entity_type="spell",
            field="weight",
        )


def test_name_search_and_sorting_return_stable_entity_uids(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()
    first, second = item_records()
    store.commit_records((first, second))
    factory = EntityQueryFactory()
    search = factory.name_search(
        "item",
        database_uid=store.block.guid,
        value="pack",
    )
    sorted_query = factory.create(
        "Heavy first",
        database_uid=store.block.guid,
        entity_type="item",
        field="name",
        operator="all",
        sort_field="weight",
        sort_order="desc",
    )

    results = factory.execute(store, search)
    sorted_results = factory.execute(store, sorted_query)

    assert [row.uid for row in results] == [first.uid, second.uid]
    assert [row.uid for row in sorted_results] == [second.uid, first.uid]


def test_entity_store_combines_validated_query_criteria(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()
    first, second = item_records()
    store.commit_records((first, second))

    results = store.query(
        "item",
        criteria=(("name", "contains", "pack"), ("weight", "lte", 5)),
    )

    assert [row.uid for row in results] == [first.uid]
    with pytest.raises(ValueError, match="Unsupported field for item: level"):
        store.query("item", criteria=(("level", "eq", 1),))


def test_item_query_supports_nested_schema_parameters(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()
    first, second = item_records()
    flame_tongue = replace(
        first,
        payload={
            **first.payload,
            "weapon": {
                "type": "longsword",
                "properties": ["versatile"],
                "effects": [{"damage": {"type": "fire"}}],
            },
            "magic_item": {
                "rarity": "rare",
                "attunement": True,
                "spells": [{"spell": "fire shield", "charges": 1}],
            },
        },
    )
    store.commit_records((flame_tongue, second))

    results = store.query(
        "item",
        criteria=(
            ("is_weapon", "eq", 1),
            ("weapon_damage_type", "has", "fire"),
            ("grants_spells", "eq", 1),
            ("rarity", "eq", "rare"),
        ),
    )

    assert [row.uid for row in results] == [first.uid]
    assert store.query(
        "item", criteria=(("granted_spell", "has", "fire shield"),)
    )[0].uid == first.uid
    assert [row.uid for row in store.query(
        "item", criteria=(("rarity", "any_of", ("rare", "legendary")),)
    )] == [first.uid]
    assert [row.uid for row in store.query(
        "item",
        criteria=(("weapon_damage_type", "any_of", ("cold", "fire")),),
    )] == [first.uid]


def test_project_controller_routes_saved_query_lifecycle(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    database = controller.entity_database_store("compendium").block
    query = EntityQueryFactory().name_search(
        "item",
        database_uid=database.guid,
        value="pack",
    )

    controller.register_entity_query(query)

    assert controller.project.block_child_uids(database.guid) == (query.guid,)
    assert controller.project.nodes.get(f"{query.guid}-node").parent_uid == (
        "dmtools-compendium-item-category"
    )
    record = next(
        item
        for item in controller.framework_project_document()["blocks"]
        if item["block_uid"] == query.guid
    )
    assert record["type"] == "entity_saved_query"
    assert record["data"]["format_version"] == 1

    controller.update_entity_query(query.guid, name="Packs", value="back")
    duplicate = controller.duplicate_entity_query(query.guid)
    assert query.name == "Packs"
    assert query.block_data.value == "back"
    assert duplicate.guid != query.guid
    assert duplicate.block_data.value == "back"

    controller.unregister_entity_query(query.guid)
    assert not controller.project.blocks.contains(query.guid)
    assert controller.project.blocks.contains(duplicate.guid)


def test_saved_query_rejects_database_from_another_project(tmp_path):
    first = ProjectController(artifact_store=ArtifactStore(tmp_path / "first"))
    second = ProjectController(artifact_store=ArtifactStore(tmp_path / "second"))
    foreign_database = first.entity_database_store("compendium").block
    query = EntityQueryFactory().name_search(
        "item",
        database_uid=foreign_database.guid,
        value="pack",
    )

    with pytest.raises(ValueError, match="not in the active project"):
        second.register_entity_query(query)


def test_saved_query_and_collection_restore_before_dependent_view(tmp_path):
    qt_app()
    project_directory = tmp_path / "campaign"
    controller = ProjectController()
    controller.create_project(project_directory)
    records = item_records()
    controller.commit_imported_entities(records)
    database = controller.entity_database_store("compendium").block
    query = EntityQueryFactory().name_search(
        "item", database_uid=database.guid, value="pack"
    )
    controller.register_entity_query(query)
    collection = controller.create_collection(
        "Packs", dynamic_query_uid=query.guid
    )
    project_file = controller.save_project()

    restored = ProjectController()
    restored.load_project(project_file)
    rows = restored.execute_entity_query(query.guid)
    view = create_entity_query_results(rows, project_controller=restored)

    assert [row.uid for row in rows] == [record.uid for record in records]
    assert restored.project.block_child_uids(database.guid) == (query.guid,)
    assert [row.uid for row in restored.resolve_collection_members(collection.guid)] == [
        record.uid for record in records
    ]
    assert view.model.rowCount() == 2


def test_saved_query_handles_missing_entity_and_stale_database(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    record = item_records()[0]
    controller.commit_imported_entities((record,))
    database = controller.entity_database_store().block
    query = EntityQueryFactory().name_search(
        "item", database_uid=database.guid, value="pack"
    )
    controller.register_entity_query(query)

    controller.entity_database_store().delete(record.uid)
    assert controller.execute_entity_query(query.guid) == ()

    query.block_data.database_uid = "missing-database"
    with pytest.raises(ValueError, match="database UID is missing"):
        controller.execute_entity_query(query.guid)