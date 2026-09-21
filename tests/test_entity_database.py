import sqlite3
from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore

from application.entity_database import EntityDatabaseStore
from application.imports import EntityImportService
from application.project_controller import ProjectController


ITEM_XML = """
<compendium>
    <item>
        <name>Backpack</name><type>G</type><weight>5</weight><value>2</value>
        <text>A leather pack.</text>
    </item>
</compendium>
"""


def item_record():
    return EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]


def test_entity_store_creates_json1_schema_and_indexes(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()

    with sqlite3.connect(store.database_path) as connection:
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }

    assert "idx_entities_type_name" in indexes
    assert "idx_entities_item_weight" in indexes
    assert "idx_entities_spell_level" in indexes
    assert "idx_entities_monster_cr" in indexes
    assert store.block.block_data.artifact.format == "sqlite"
    assert store.block.block_data.artifact.valid is True


def test_entity_store_requires_json1_before_schema_creation(tmp_path, monkeypatch):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite")
    monkeypatch.setattr(
        store,
        "require_json1",
        lambda connection: (_ for _ in ()).throw(RuntimeError("JSON1 required")),
    )

    with pytest.raises(RuntimeError, match="JSON1 required"):
        store.initialize()

    with sqlite3.connect(store.database_path) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'entities'"
        ).fetchone() is None


def test_entity_store_commits_atomically_and_retains_uid_results(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()
    record = item_record()
    conflicting = replace(record, source_identity="rules:item:other")

    with pytest.raises(sqlite3.IntegrityError):
        store.commit_records((record, conflicting))

    assert store.count() == 0
    store.commit_records((record,))
    result = store.query("item", field="weight", operator="eq", value=5)
    assert len(result) == 1
    assert result[0].uid == record.uid
    assert result[0].payload == record.payload


def test_entity_store_duplicate_policies_and_reopen(tmp_path):
    path = tmp_path / "compendium.sqlite"
    store = EntityDatabaseStore(path).initialize()
    original = item_record()
    replacement = replace(
        original,
        display_name="Adventurer's Backpack",
        payload={**original.payload, "name": "Adventurer's Backpack"},
    )
    store.commit_records((original,))

    assert store.commit_records((replacement,), duplicate_policy="skip") == 1
    assert store.query("item", value="Backpack")[0].name == "Backpack"
    store.commit_records((replacement,), duplicate_policy="replace")
    assert store.query("item", value="Adventurer's Backpack")[0].uid == original.uid

    reopened = EntityDatabaseStore(path).initialize()
    assert reopened.count() == 1
    assert original.source_identity in reopened.source_identities()


def test_entity_store_rejects_unsafe_fields_and_operators(tmp_path):
    store = EntityDatabaseStore(tmp_path / "compendium.sqlite").initialize()

    with pytest.raises(ValueError, match="Unsupported field"):
        store.query("item", field="$.weight; DROP TABLE entities", value=5)
    with pytest.raises(ValueError, match="Unsupported query operator"):
        store.query("item", operator="matches_sql", value="pack")


def test_project_controller_owns_entity_database_block_without_redundant_node(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))

    store = controller.entity_database_store("compendium")
    block = store.block

    assert controller.project.blocks.get(block.guid) is block
    assert not controller.project.nodes.contains(f"{block.guid}-node")
    record = next(
        item
        for item in controller.framework_project_document()["blocks"]
        if item["block_uid"] == block.guid
    )
    assert record["type"] == "entity_database"
    assert record["data"]["artifact"]["path"] == "data/compendium.sqlite"

    controller.refresh_project_tree()
    assert not controller.project.nodes.contains(f"{block.guid}-node")