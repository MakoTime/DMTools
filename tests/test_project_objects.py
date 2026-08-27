import json
import sqlite3

from application import ProjectController
from application.project_serializer import ProjectSerializer
from objects.database_object import DatabaseObject
from objects.query_object import QueryObject
from objects.shopkeeper_object import ShopkeeperObject
from dialog.database.model import FilterCondition, MultiTableLookup


def test_database_and_shopkeeper_references_round_trip(tmp_path):
    database_path = tmp_path / "source.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    controller = ProjectController()
    database = DatabaseObject("Items", database_path)
    database.add_query("All items", "SELECT * FROM items")
    database.add_to_tree(controller.tree_manager, controller.tree_manager.root_nodes[0])

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
    loaded = ProjectSerializer().load(project_file, loaded_controller.tree_manager)
    loaded_types = {
        type(node.node_object).__name__
        for root in loaded_controller.tree_manager.get_root_nodes()
        for node in walk(root)
        if node.node_object is not None
    }
    assert "DatabaseObject" in loaded_types
    assert "ShopkeeperObject" in loaded_types


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
