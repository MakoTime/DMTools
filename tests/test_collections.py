from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore, Project

from application.entity_queries import EntityQueryFactory
from application.imports import EntityImportService
from application.project_controller import ProjectController


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def records():
    first = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    second = replace(
        first,
        uid="heavy-pack-uid",
        source_identity="rules:item:heavy-pack",
        display_name="Heavy Pack",
        payload={**first.payload, "name": "Heavy Pack", "weight": 10},
    )
    return first, second


def controller_with_entities(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    controller.commit_imported_entities(records())
    return controller


def test_collection_manual_membership_preserves_order_and_prevents_duplicates(tmp_path):
    controller = controller_with_entities(tmp_path)
    first, second = records()
    collection = controller.create_collection(
        "Travel Gear",
        description="Useful packs",
        entity_uids=(second.uid, first.uid),
    )

    assert collection.block_data.entity_uids == [second.uid, first.uid]
    assert [row.uid for row in controller.resolve_collection_members(collection.guid)] == [
        second.uid,
        first.uid,
    ]
    assert controller.project.nodes.get(f"{collection.guid}-node").parent_uid == (
        "dmtools-collections-root"
    )
    with pytest.raises(ValueError, match="already in the collection"):
        controller.add_collection_entity(collection.guid, first.uid)

    assert controller.remove_collection_entity(collection.guid, second.uid) is True
    assert controller.remove_collection_entity(collection.guid, second.uid) is False


def test_collection_search_filters_members_and_keeps_source_namespace(tmp_path):
    controller = controller_with_entities(tmp_path)
    first, second = records()
    collection = controller.create_collection(
        "Travel Gear", entity_uids=(first.uid, second.uid)
    )

    results = controller.search_collection(collection.guid, "heavy")

    assert [row.uid for row in results] == [second.uid]
    assert results[0].source_namespace == "compendium"


def test_collection_rejects_unknown_and_cross_project_entity_uids(tmp_path):
    first = controller_with_entities(tmp_path / "first")
    second = ProjectController(artifact_store=ArtifactStore(tmp_path / "second"))
    foreign_uid = records()[0].uid

    with pytest.raises(ValueError, match="Unknown active-project entity UID"):
        second.create_collection("Foreign", entity_uids=(foreign_uid,))
    assert not any(
        block.type_name == "collection" for block in second.project.blocks.values()
    )
    assert first.resolve_entity(foreign_uid).uid == foreign_uid


def test_collection_query_capture_and_dynamic_refresh_are_distinct(tmp_path):
    controller = controller_with_entities(tmp_path)
    database = controller.entity_database_store("compendium").block
    query = EntityQueryFactory().create(
        "All Items",
        database_uid=database.guid,
        entity_type="item",
        operator="all",
    )
    controller.register_entity_query(query)
    captured = controller.create_collection("Captured")
    dynamic = controller.create_collection("Dynamic", dynamic_query_uid=query.guid)

    controller.capture_query_results(captured.guid, query.guid)

    assert len(captured.block_data.entity_uids) == 2
    assert dynamic.block_data.entity_uids == []
    assert len(controller.resolve_collection_members(dynamic.guid)) == 2
    assert controller.resolve_collection_members(dynamic.guid, include_dynamic=False) == ()


def test_collection_crud_stale_references_and_serialization(tmp_path):
    controller = controller_with_entities(tmp_path)
    first, _second = records()
    collection = controller.create_collection("Gear", entity_uids=(first.uid,))

    controller.update_collection(collection.guid, name="Travel Gear", description="Ready")
    duplicate = controller.duplicate_collection(collection.guid)
    assert duplicate.guid != collection.guid
    assert duplicate.block_data.entity_uids == [first.uid]

    store = controller.entity_database_store("compendium")
    with store.connect() as connection:
        connection.execute("DELETE FROM entities WHERE uid = ?", (first.uid,))
        connection.commit()
    missing = controller.resolve_collection_members(collection.guid)[0]
    assert missing.uid == first.uid
    assert missing.missing is True

    document = controller.framework_project_document()
    record = next(
        item
        for item in document["blocks"]
        if item["block_uid"] == collection.guid
    )
    assert record["type"] == "collection"
    assert record["data"]["entity_uids"] == [first.uid]
    restored = Project(artifact_store=ArtifactStore(tmp_path))
    controller.framework_serializer.load_document(document, restored)
    assert restored.blocks.get(collection.guid).block_data.entity_uids == [first.uid]

    controller.remove_collection(collection.guid)
    assert not controller.project.blocks.contains(collection.guid)