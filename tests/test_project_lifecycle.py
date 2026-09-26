import json

import pytest
from projectfoundry import ArtifactStore

from application.entity_queries import EntityQueryFactory
from application.imports import EntityImportService
from application.project_controller import ProjectController
from application.project_tree import ProjectTreeMutationService
from application.project_serializer import ProjectSerializer
from objects.json_object import JSONBlock


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def test_lifecycle_service_preserves_legacy_and_framework_documents(tmp_path):
    controller = ProjectController()

    project_file = controller.create_project(tmp_path / "campaign")
    document = json.loads(project_file.read_text(encoding="utf-8"))

    assert "roots" in document
    assert "framework" in document
    assert controller.project_context.package_path == project_file
    controller.close()


def test_lifecycle_service_loads_framework_candidate_before_replacing_project(tmp_path):
    source = ProjectController()
    project_file = source.create_project(tmp_path / "campaign")
    source_project = source.project

    target = ProjectController()
    target.load_project(project_file)

    assert target.project is not source_project
    assert target.project_context.project is target.project
    source.close()
    target.close()


def test_legacy_project_requires_explicit_import(tmp_path):
    source = ProjectController()
    project_file = ProjectSerializer().save(tmp_path / "legacy", source.tree_manager)
    target = ProjectController()

    with pytest.raises(ValueError, match="import_legacy"):
        target.load_project(project_file)

    loaded = target.import_legacy_project(project_file)
    assert loaded
    assert target.project_context.package_path == project_file

    source.close()
    target.close()


def test_projectfoundry_tree_hierarchy_round_trips_by_uid(tmp_path):
    source = ProjectController()
    project_file = source.create_project(tmp_path / "campaign")
    record = EntityImportService().preview_xml(ITEM_XML).records[0]
    source.commit_imported_entities((record,))
    source.save_project()

    target = ProjectController()
    target.load_project(project_file)

    entity_node = target.project.nodes.get(
        f"dmtools-compendium-entity-{record.uid}"
    )
    assert entity_node.entity_uid == record.uid
    assert target.project.nodes.get(entity_node.parent_uid).name == "Item"
    assert target.entity_database_store("compendium").get(record.uid).name == "Backpack"

    source.close()
    target.close()


def test_conversion_fixture_round_trips_roots_database_objects_and_editor_metadata(
    tmp_path,
):
    source = ProjectController(artifact_store=ArtifactStore(tmp_path))
    project_file = source.create_project(tmp_path / "campaign")
    record = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    source.commit_imported_entities((record,))

    database = source.entity_database_store("compendium").block
    query = EntityQueryFactory().create(
        "Item Name Search",
        database_uid=database.guid,
        entity_type="item",
        field="name",
        operator="contains",
        value="pack",
        projection=["name", "weight"],
    )
    source.register_entity_query(query)
    source.save_project()

    document = json.loads(project_file.read_text(encoding="utf-8"))
    assert {root["name"] for root in document["roots"]} >= {
        "Compendium",
        "Homebrew",
        "Collections",
    }
    assert (project_file.parent / "data" / "compendium.sqlite").exists()
    query_record = next(
        block
        for block in document["framework"]["blocks"]
        if block["block_uid"] == query.guid
    )
    assert query_record["data"]["database_uid"] == database.guid
    assert query_record["data"]["projection"] == ["name", "weight"]

    target = ProjectController()
    target.load_project(project_file)

    assert target.entity_database_store("compendium").get(record.uid).name == "Backpack"
    restored_query = target.project.blocks.get(query.guid)
    assert restored_query.block_data.database_uid == database.guid
    assert restored_query.block_data.projection == ["name", "weight"]
    assert target.execute_entity_query(query.guid)[0].uid == record.uid

    source.close()
    target.close()


def test_uid_integrity_survives_project_tree_block_collection_and_sqlite_round_trip(
    tmp_path,
):
    source = ProjectController(artifact_store=ArtifactStore(tmp_path))
    project_file = source.create_project(tmp_path / "campaign")
    record = EntityImportService().preview_xml(ITEM_XML).records[0]
    source.commit_imported_entities((record,))
    database = source.entity_database_store("compendium").block
    query = EntityQueryFactory().name_search(
        "item", database_uid=database.guid, value="pack"
    )
    source.register_entity_query(query)
    collection = source.create_collection(
        "Travel Gear",
        entity_uids=[record.uid],
        dynamic_query_uid=query.guid,
    )
    source.save_project()

    target = ProjectController()
    target.load_project(project_file)
    entity_node = target.project.nodes.get(
        f"dmtools-compendium-entity-{record.uid}"
    )
    restored_query = target.project.blocks.get(query.guid)
    restored_collection = target.project.blocks.get(collection.guid)

    assert target.entity_database_store("compendium").get(record.uid).uid == record.uid
    assert entity_node.entity_uid == record.uid
    assert entity_node.object_uid is None
    assert restored_query.block_data.database_uid == database.guid
    assert restored_collection.block_data.entity_uids == [record.uid]
    assert restored_collection.block_data.dynamic_query_uid == query.guid
    assert [row.uid for row in target.resolve_collection_members(collection.guid)] == [
        record.uid
    ]
    assert target.execute_entity_query(query.guid)[0].uid == record.uid

    source.close()
    target.close()


def test_project_tree_mutation_service_validates_and_rolls_back_block_changes():
    controller = ProjectController()
    service = ProjectTreeMutationService(controller.project)
    block = JSONBlock("Draft", guid="draft-block")

    node = service.create_block(
        block,
        parent_uid="dmtools-collections-root",
        node_uid="draft-node",
    )
    assert node.object_uid == block.guid
    assert controller.project.blocks.get(block.guid) is block

    service.rename_block(block.guid, "Renamed Draft")
    assert controller.project.blocks.get(block.guid).name == "Renamed Draft"

    with pytest.raises(ValueError, match="Parent node UID is missing"):
        service.create_block(
            JSONBlock("Orphan", guid="orphan-block"),
            parent_uid="missing-parent",
        )
    assert not controller.project.blocks.contains("orphan-block")

    assert service.delete_block(block.guid) is block
    assert not controller.project.blocks.contains(block.guid)
    assert not controller.project.nodes.contains(node.guid)
    controller.close()
