import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
from projectfoundry import Project
from projectfoundry.core.artifacts import ArtifactStore

from application import ProjectController
from application.project_serializer import ProjectSerializer
from dialog.database.model import FilterCondition, MultiTableLookup
from objects.database_object import DatabaseObject
from objects.json_object import JSONDataObject
from objects.query_object import QueryObject
from objects.shopkeeper_object import ShopkeeperObject
from objects.table_object import TableDataObject
from components.tree.roots.entity_roots import compendium_root, homebrew_root


def test_database_and_shopkeeper_references_round_trip(tmp_path):
    database_path = tmp_path / "source.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    controller = ProjectController()
    database = DatabaseObject("Items", database_path)
    database.add_query("All items", "SELECT * FROM items")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    assert controller.project.blocks.contains(database.guid)
    assert controller.project.resolve_block(database.guid) is database.block_object

    shopkeeper = ShopkeeperObject(
        "General Store",
        database_guid=database.guid,
        query_guids=["all-items-query"],
        stock_count=8,
    )
    shopkeeper.add_to_tree(controller.tree_manager)

    project_file = ProjectSerializer().save(tmp_path / "project", controller.tree_manager)
    raw = json.loads(project_file.read_text(encoding="utf-8"))
    assert raw["roots"][0]["type"] == "folder"
    assert raw["roots"][0]["children"][0]["type"] == "database"

    loaded_controller = ProjectController()
    ProjectSerializer().load(project_file, loaded_controller.tree_manager)
    loaded_types = {
        type(node.node_object).__name__
        for root in loaded_controller.tree_manager.get_root_nodes()
        for node in walk(root)
        if node.node_object is not None
    }
    assert "DatabaseObject" in loaded_types
    assert "ShopkeeperObject" in loaded_types


@pytest.mark.parametrize("namespace_root, namespace", [
    (compendium_root, "compendium"),
    (homebrew_root, "homebrew"),
])
def test_namespace_json_payloads_are_shareable_files(namespace_root, namespace, tmp_path):
    controller = ProjectController()
    payload = JSONDataObject("Shared entity", {"name": "Shared", "description": "Data"})
    payload.add_to_tree(controller.tree_manager, namespace_root)

    project_file = ProjectSerializer().save(tmp_path / "project", controller.tree_manager)
    document = json.loads(project_file.read_text(encoding="utf-8"))

    assert document["data_files"][namespace] == f"data/{namespace}.json"
    assert (tmp_path / "project" / "data" / f"{namespace}.json").exists()
    assert '"description": "Data"' not in project_file.read_text(encoding="utf-8")

    loaded_controller = ProjectController()
    ProjectSerializer().load(project_file, loaded_controller.tree_manager)
    loaded = next(
        node.node_object for root in loaded_controller.tree_manager.root_nodes
        for node in walk(root)
        if node.node_object is not None and node.node_object.name == "Shared entity"
    )
    assert loaded.data == {"name": "Shared", "description": "Data"}


def test_query_object_is_persisted_as_a_database_child(tmp_path):
    controller = ProjectController()
    database_path = tmp_path / "rules.sqlite"
    sqlite3.connect(database_path).close()
    database = DatabaseObject("Rules", database_path)
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    query = QueryObject(
        "Wizard spells",
        sql='SELECT * FROM "dnd5_spells"',
        table_name="dnd5_spells",
        filters=[FilterCondition("spell_level", "Greater than", "2")],
        lookup=MultiTableLookup(enabled=True, output_table="dnd5_spells"),
    )
    database.add_query_object(query)
    controller.refresh_project_tree()
    assert controller.project.block_child_uids(database.guid) == (query.guid,)
    framework_document = controller.framework_project_document()
    framework_blocks = {record["type"] for record in framework_document["blocks"]}
    assert framework_blocks == {"database", "query"}
    database_record = next(
        record for record in framework_document["blocks"] if record["block_uid"] == database.guid
    )
    assert database_record["child_uids"] == [query.guid]
    restored_project = Project()
    controller.framework_serializer.load_document(framework_document, restored_project)
    assert restored_project.block_child_uids(database.guid) == (query.guid,)

    project_file = ProjectSerializer().save(tmp_path / "project", controller.tree_manager)
    raw = json.loads(project_file.read_text(encoding="utf-8"))
    database_data = next(
        item
        for item in raw["roots"][0]["children"]
        if item.get("type") == "database" and item.get("guid") == database.guid
    )
    query_data = next(
        item for item in database_data["children"] if item.get("type") == "query"
    )
    assert query_data["type"] == "query"
    assert query_data["database_guid"] == database.guid
    assert query_data["filters"][0]["column"] == "spell_level"

    loaded_controller = ProjectController()
    ProjectSerializer().load(project_file, loaded_controller.tree_manager)
    loaded_database = next(
        node.node_object
        for node in walk(loaded_controller.tree_manager.root_nodes[0])
        if isinstance(node.node_object, DatabaseObject)
        and node.node_object.guid == database.guid
    )
    assert len(loaded_database.query_objects) == 1
    assert loaded_database.query_objects[0].lookup.enabled is True


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def test_shopkeeper_is_marked_stale_when_database_changes():
    database = DatabaseObject("Items")
    shopkeeper = ShopkeeperObject("General Store")

    shopkeeper.bind_database(database)
    shopkeeper.inventory_stale = False
    database.add_query("All items", "SELECT * FROM items")

    assert shopkeeper.inventory_stale is True
    assert shopkeeper.last_database_revision == database.revision


def test_shopkeeper_block_uses_validated_uid_relationships_and_round_trips():
    controller = ProjectController()
    database = DatabaseObject("Items")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    query = QueryObject("Stock", sql="SELECT 1")
    database.add_query_object(query)
    controller.refresh_project_tree()
    shopkeeper = ShopkeeperObject(
        "General Store",
        database_guid=database.guid,
        query_guids=[query.guid],
        filters={"rarity": "common"},
        stock_count=8,
        random_seed=42,
    )

    controller.register_shopkeeper(shopkeeper)

    block = controller.project.blocks.get(shopkeeper.guid)
    assert block.block_data.database_uid == database.guid
    assert block.block_data.query_uids == [query.guid]
    assert shopkeeper.guid in controller.project.block_child_uids(database.guid)
    document = controller.framework_project_document()
    record = next(
        item for item in document["blocks"] if item["block_uid"] == shopkeeper.guid
    )
    assert record["type"] == "shopkeeper"
    assert record["data"]["query_uids"] == [query.guid]

    restored = Project()
    controller.framework_serializer.load_document(document, restored)
    restored_data = restored.blocks.get(shopkeeper.guid).block_data
    assert restored_data.database_uid == database.guid
    assert restored_data.stock_count == 8


def test_shopkeeper_registration_rejects_missing_uid_without_mutation():
    controller = ProjectController()
    shopkeeper = ShopkeeperObject(
        "Broken Store", database_guid="missing", query_guids=["missing-query"]
    )

    with pytest.raises(ValueError, match="database UID"):
        controller.register_shopkeeper(shopkeeper)

    assert not controller.project.blocks.contains(shopkeeper.guid)


def test_project_controller_owns_a_projectfoundry_project():
    controller = ProjectController()
    original_project = controller.project

    assert controller.project_tree_manager is controller.project.tree
    assert controller.project_tree_model.project is controller.project
    assert controller.project_tree_model.root_data is controller.project.tree.root_nodes
    assert controller.tree_manager is not controller.project_tree_manager
    assert controller.tree_manager.root_nodes[0].uid
    assert controller.project_tree_model.rowCount() == len(
        controller.project_tree_manager.root_nodes
    )
    assert [
        controller.project_tree_model.data(
            controller.project_tree_model.index(row, 0)
        )
        for row in range(controller.project_tree_model.rowCount())
    ] == ["Databases", "Compendium", "Homebrew", "Collections"]
    assert [node.uid for node in controller.project_tree_model.root_data] == [
        node.uid for node in controller.project_tree_manager.root_nodes
    ]

    controller.refresh_project_tree()
    assert [
        controller.project_tree_model.data(
            controller.project_tree_model.index(row, 0)
        )
        for row in range(controller.project_tree_model.rowCount())
    ] == ["Databases", "Compendium", "Homebrew", "Collections"]

    controller.new_project()

    assert controller.project is not original_project
    assert len(controller.project.objects) == 0
    assert len(controller.project.blocks) == 0
    controller.close()


def test_project_context_and_service_follow_create_save_replace_and_load(tmp_path):
    controller = ProjectController()
    project_file = controller.create_project(tmp_path / "campaign")
    context = controller.project_context
    original_project = controller.project

    assert context.project is original_project
    assert context.package_path == project_file
    assert controller.project_service.project is original_project
    assert controller.project_service.task_runner is controller.task_runner
    task_runner = controller.task_runner

    database = DatabaseObject("Rules")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    controller.project.rename_block(database.guid, "Renamed Rules")
    assert context.dirty is True
    controller.save_project()
    assert context.dirty is False

    controller.new_project()
    assert context._closed is True
    assert controller.project is not original_project
    assert controller.project_context is None
    assert controller.project_service.project is controller.project
    assert controller.project_service.task_runner is task_runner
    assert task_runner.runner.project is controller.project

    controller.load_project(project_file)
    assert controller.project_context.project is controller.project
    assert controller.project_service.project is controller.project
    assert controller.project_service.task_runner is task_runner
    assert task_runner.runner.project is controller.project
    assert controller.project.blocks.contains(database.guid)


def test_legacy_database_tree_projects_and_removes_database_block():
    controller = ProjectController()
    database = DatabaseObject("Rules")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])

    controller.refresh_project_tree()
    assert controller.project.resolve_block(database.guid) is database.block_object

    database.remove_from_tree()
    controller.refresh_project_tree()
    assert not controller.project.blocks.contains(database.guid)


def test_tree_model_renames_registered_blocks_through_project(tmp_path):
    controller = ProjectController()
    database = DatabaseObject("Rules", tmp_path / "rules.sqlite")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    index = controller.tree_model.index(
        controller.tree_model.root_data[0].children.index(database.node),
        0,
        controller.tree_model.index(0, 0),
    )

    assert controller.tree_model.setData(index, "Renamed Rules") is True
    assert controller.project.blocks.get(database.guid).name == "Renamed Rules"
    assert database.name == "Renamed Rules"
    controller.close()


def test_project_controller_routes_query_lifecycle():
    controller = ProjectController()
    database = DatabaseObject("Rules")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    query = QueryObject("All rules", sql="SELECT 1")

    database.add_query_object(query)
    controller.refresh_project_tree()
    assert controller.project.block_child_uids(database.guid) == (query.guid,)

    database.query_objects.remove(query)
    query.remove_from_tree()
    database._changed()
    controller.refresh_project_tree()
    assert controller.project.block_child_uids(database.guid) == ()


def test_project_controller_updates_query_block_data():
    controller = ProjectController()
    database = DatabaseObject("Rules")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])
    controller.refresh_project_tree()
    query = QueryObject("All rules", sql="SELECT 1")
    database.add_query_object(query)
    controller.refresh_project_tree()

    controller.update_query(
        database,
        query,
        sql="SELECT 2",
        table_name="rules",
        filters=[],
        lookup=MultiTableLookup(output_table="rules"),
    )

    assert query.block_object.block_data.sql == "SELECT 2"
    assert query.block_object.block_data.table_name == "rules"
    assert query.block_object.block_data.lookup["output_table"] == "rules"


def test_project_controller_registers_json_block():
    controller = ProjectController()
    json_object = JSONDataObject("Settings", {"theme": "dark"})
    json_object.add_to_tree(controller.tree_manager)
    controller.refresh_project_tree()

    assert controller.project.resolve_block(json_object.guid) is json_object.block_object
    record = next(
        record
        for record in controller.framework_project_document()["blocks"]
        if record["block_uid"] == json_object.guid
    )
    assert record["type"] == "json"
    assert record["data"]["data"] == {"theme": "dark"}


def test_table_block_persists_dataframe_as_project_artifact(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    table = TableDataObject(
        "Encounters",
        pd.DataFrame([{"name": "Owlbear", "challenge": 3}]),
    )
    controller.register_table(table, controller.tree_manager.root_nodes[0])

    assert controller.project.resolve_block(table.guid) is table.block_object

    controller.commit_table(table)
    document = controller.framework_project_document()
    record = next(
        item for item in document["blocks"] if item["block_uid"] == table.guid
    )

    assert record["type"] == "table"
    assert "data" not in record["data"]
    assert record["data"]["artifact"]["path"] == f"artifacts/{table.guid}.csv"
    assert record["data"]["artifact"]["format"] == "csv"
    assert record["data"]["artifact"]["checksum"]
    assert table._draft_data is None
    pd.testing.assert_frame_equal(
        table.data,
        pd.DataFrame([{"name": "Owlbear", "challenge": 3}]),
    )

    restored_project = Project()
    controller.framework_serializer.load_document(document, restored_project)
    restored_block = restored_project.resolve_block(table.guid)
    restored_project.artifact_store = controller.project.artifact_store
    restored_table = restored_project.load_block_artifact(
        restored_block.guid, restored_block.load_artifact
    )
    pd.testing.assert_frame_equal(restored_table, table.data)
    table.remove_from_tree()


def test_table_edit_invalidates_artifact_and_failed_commit_preserves_file(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    table = TableDataObject("Encounters", pd.DataFrame([{"name": "Owlbear"}]))
    controller.register_table(table, controller.tree_manager.root_nodes[0])
    original_artifact = controller.commit_table(table)
    artifact_path = tmp_path / original_artifact.path
    original_bytes = artifact_path.read_bytes()

    table.data = pd.DataFrame([{"name": "Displacer Beast"}])
    stale_artifact = table.block_object.block_data.artifact
    assert not stale_artifact.valid
    assert stale_artifact.checksum == original_artifact.checksum

    def fail_persistence(result, path):
        del result
        Path(path).write_text("partial", encoding="utf-8")
        raise RuntimeError("write failed")

    table.block_object.persist_result = fail_persistence
    with pytest.raises(RuntimeError, match="write failed"):
        controller.commit_table(table)

    assert artifact_path.read_bytes() == original_bytes
    assert table.block_object.block_data.artifact == stale_artifact
    table.remove_from_tree()


def test_table_registration_rejects_cross_project_ownership():
    first_controller = ProjectController()
    second_controller = ProjectController()
    table = TableDataObject("Encounters")
    first_controller.register_table(table, first_controller.tree_manager.root_nodes[0])

    with pytest.raises(ValueError, match="another project"):
        second_controller.register_table(table, second_controller.tree_manager.root_nodes[0])

    assert not second_controller.project.blocks.contains(table.guid)
    table.remove_from_tree()


def test_table_legacy_project_round_trip_remains_compatible(tmp_path):
    controller = ProjectController()
    table = TableDataObject(
        "Encounters",
        pd.DataFrame([{"name": "Owlbear", "challenge": 3}]),
    )
    controller.register_table(table, controller.tree_manager.root_nodes[0])

    project_file = ProjectSerializer().save(tmp_path / "project", controller.tree_manager)
    loaded_controller = ProjectController()
    ProjectSerializer().load(project_file, loaded_controller.tree_manager)
    loaded_table = next(
        node.node_object
        for node in walk(loaded_controller.tree_manager.root_nodes[0])
        if isinstance(node.node_object, TableDataObject)
    )

    assert loaded_table.guid == table.guid
    pd.testing.assert_frame_equal(loaded_table.data, table.data)
    table.remove_from_tree()
    loaded_table.remove_from_tree()
