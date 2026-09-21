import pytest
from projectfoundry import ArtifactStore, Project

from application.imports import EntityImportService
from application.project_controller import ProjectController
from application.homebrew import HomebrewDraft
from components.tree.model import TreeNode
from components.tree.roots.entity_roots import (
    ENTITY_CATEGORIES,
    canonical_entity_type,
    compendium_root,
    homebrew_root,
)


EXPECTED_CATEGORIES = [label for _entity_type, label in ENTITY_CATEGORIES]

ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""

CLASS_WITH_SUBCLASS_XML = """
<compendium>
    <class>
        <name>Bard</name><hd>8</hd>
        <autolevel level="3">
            <feature optional="YES">
                <name>Bard College: College of Lore</name>
                <text>College description.</text>
            </feature>
            <feature optional="YES">
                <name>Cutting Words (College of Lore)</name>
                <text>Feature description.</text>
            </feature>
        </autolevel>
    </class>
</compendium>
"""


def test_project_owns_ordered_compendium_and_homebrew_hierarchies():
    controller = ProjectController()

    assert [node.name for node in controller.tree_manager.root_nodes] == [
        "Databases",
        "Compendium",
        "Homebrew",
        "Collections",
    ]
    for root, namespace in (
        (compendium_root, "compendium"),
        (homebrew_root, "homebrew"),
    ):
        categories = root.children[: len(ENTITY_CATEGORIES)]
        assert [node.name for node in categories] == EXPECTED_CATEGORIES
        assert [node.entity_type for node in categories] == [
            entity_type for entity_type, _label in ENTITY_CATEGORIES
        ]
        assert all(node.namespace == namespace for node in categories)
        assert controller.project.nodes.get(root.uid).node_type == "entity_root"

    assert compendium_root.rules.name == "Rules"
    assert [node.name for node in compendium_root.rules.children] == [
        "Proficiencies",
        "Weapons",
        "Ability Scores",
        "Ability Kinds",
        "Alignments",
        "Action Types",
        "Attack Types",
        "Bonus Types",
        "Casting Time Units",
        "Class Names",
        "Conditions",
        "Distance Units",
        "Duration Units",
        "Movement Types",
        "Recharge Times",
        "Sizes",
        "Senses",
        "Spell Components",
        "Spell Schools",
        "Currencies",
        "Rarities",
        "Creature Types",
        "Damage Types",
        "Spellcasting Progressions",
        "Item Categories",
        "Target Types",
        "Target Zones",
        "Targeting Modes",
    ]
    assert [node.category_type for node in compendium_root.rules.children] == [
        "proficiencies",
        "weapons",
        "ability_score",
        "ability_kind",
        "alignment",
        "action_type",
        "attack_type",
        "bonus_type",
        "casting_time",
        "class_name",
        "conditions",
        "distance_type",
        "duration",
        "movement_type",
        "recharge",
        "size",
        "sense",
        "spell_component",
        "spell_school",
        "currency",
        "rarity",
        "creature_type",
        "damage_type",
        "spellcasting_progression",
        "item_category",
        "target_type",
        "target_zone",
        "targeting",
    ]
    assert [node.name for node in compendium_root.rules.category("proficiencies").children] == [
        "Languages",
        "Skills",
        "Tools",
        "Armor",
        "Instruments",
        "Gaming Sets",
        "Vehicles",
    ]
    assert [node.name for node in compendium_root.rules.category("size").children] == [
        "Tiny",
        "Small",
        "Medium",
        "Large",
        "Huge",
        "Gargantuan",
    ]
    assert "Common" in [
        node.name
        for node in compendium_root.rules.category("proficiencies").children[0].children
    ]
    weapon_groups = compendium_root.rules.category("weapons").children[0]
    weapon_types = compendium_root.rules.category("weapons").children[1]
    weapon_tags = compendium_root.rules.category("weapons").children[2]
    assert {"simple", "martial"}.issubset(
        node.value for node in weapon_groups.children
    )
    assert weapon_types.children
    assert {"light", "versatile", "ammunition"}.issubset(
        node.value for node in weapon_tags.children
    )
    assert homebrew_root.rules.name == "Rules"
    assert homebrew_root.rules.category("proficiencies").children[0].children == []


def test_homebrew_custom_values_are_projected_into_homebrew_rules():
    homebrew_root.rules.set_custom_values(
        (("language", "astral"), ("weapon_property", "cleaving"))
    )

    languages = homebrew_root.rules.category("proficiencies").children[0]
    weapons = homebrew_root.rules.category("weapons").children[2]
    assert [node.value for node in languages.children] == ["astral"]
    assert [node.value for node in weapons.children] == ["cleaving"]


def test_persisted_homebrew_custom_value_is_projected_into_rules(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    draft = HomebrewDraft.blank("background")
    draft.payload["languages"] = ["astral"]

    controller.commit_imported_entities(
        (draft.apply(),),
        namespace="homebrew",
    )

    languages = homebrew_root.rules.category("proficiencies").children[0]
    assert [node.value for node in languages.children] == ["astral"]


def test_entity_hierarchy_uids_survive_project_replacement():
    controller = ProjectController()
    original_uids = {
        node.name: node.uid
        for root in (compendium_root, homebrew_root)
        for node in (root, *root.children)
    }

    controller.new_project()

    assert original_uids == {
        node.name: node.uid
        for root in (compendium_root, homebrew_root)
        for node in (root, *root.children)
    }
    def tree_size(node):
        return 1 + sum(tree_size(child) for child in node.children)

    assert len(controller.project.nodes) == sum(
        tree_size(root) for root in controller.tree_manager.root_nodes
    )


def test_entity_category_validates_canonical_type_and_prevents_deletion():
    spells = compendium_root.category("Spells")
    entity_node = TreeNode("Magic Missile")

    assert canonical_entity_type("Spells") == "spell"
    assert spells.add_entity_node(entity_node, "spell") is entity_node
    with pytest.raises(ValueError, match="Cannot add item to Spells"):
        spells.add_entity_node(TreeNode("Wand"), "item")
    assert compendium_root.remove_child(spells) is False

    controller = ProjectController()
    projected_spells = controller.project.nodes.get(spells.uid)
    assert projected_spells.can_delete() is False
    assert projected_spells.delete() is False


def test_empty_entity_hierarchies_round_trip_through_legacy_project(tmp_path):
    controller = ProjectController()
    project_file = controller.project_serializer.save(
        tmp_path / "project.json", controller.tree_manager
    )

    controller.project_serializer.load(
        project_file,
        controller.tree_manager,
        controller.tree_model,
    )

    assert [node.name for node in compendium_root.children[: len(ENTITY_CATEGORIES)]] == EXPECTED_CATEGORIES
    assert compendium_root.children[-1].name == "Rules"
    assert [node.name for node in homebrew_root.children] == [
        *EXPECTED_CATEGORIES,
        "Rules",
    ]
    assert compendium_root.category("spell").entity_type == "spell"


def test_framework_document_round_trips_category_metadata():
    controller = ProjectController()
    document = controller.framework_project_document()
    spell_record = next(
        record
        for record in document["tree"]
        if record["node_uid"] == compendium_root.category("spell").uid
    )

    assert spell_record["node_type"] == "entity_category"
    assert spell_record["namespace"] == "compendium"
    assert spell_record["entity_type"] == "spell"
    assert spell_record["protected"] is True

    restored = Project()
    controller.framework_serializer.load_document(document, restored)
    restored_spell = restored.nodes.get(spell_record["node_uid"])
    assert restored_spell.namespace == "compendium"
    assert restored_spell.entity_type == "spell"
    assert restored_spell.protected is True


def test_project_tree_refresh_preserves_canonical_and_entity_node_identity(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    record = EntityImportService().preview_xml(ITEM_XML).records[0]
    controller.commit_imported_entities((record,))
    root_node = controller.project.nodes.get(compendium_root.uid)
    entity_uid = f"dmtools-compendium-entity-{record.uid}"
    entity_node = controller.project.nodes.get(entity_uid)

    controller.create_collection("Gear")
    controller.refresh_project_tree()

    assert controller.project.nodes.get(compendium_root.uid) is root_node
    assert controller.project.nodes.get(entity_uid) is entity_node
    assert entity_node.parent_uid == compendium_root.category("item").uid


def test_subclass_import_is_stored_and_projected_under_subclasses(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    preview = EntityImportService().preview_xml(
        CLASS_WITH_SUBCLASS_XML,
        source_name="classes.xml",
    )

    assert preview.can_commit is True
    assert [record.entity_type for record in preview.records] == ["class", "subclass"]

    controller.commit_imported_entities(preview.records)

    store = controller.entity_database_store("compendium")
    subclasses = store.query("subclass", operator="all")
    assert [row.name for row in subclasses] == ["College of Lore"]
    assert subclasses[0].payload["class"] == "bard"
    class_record, subclass_record = preview.records
    class_node = controller.project.nodes.get(
        f"dmtools-compendium-entity-{class_record.uid}"
    )
    subclass_node = controller.project.nodes.get(
        f"dmtools-compendium-entity-{subclass_record.uid}"
    )
    assert class_node.parent_uid == compendium_root.category("class").uid
    assert subclass_node.parent_uid == compendium_root.category("subclass").uid


def test_refresh_moves_legacy_subclass_node_to_subclasses_category():
    controller = ProjectController()
    node = TreeNode("College of Lore", uid="legacy-subclass-node")
    node.node_type = "entity"
    node.namespace = "compendium"
    node.entity_type = "subclass"
    node.entity_uid = "subclass-uid"
    controller.project.add_node(
        node,
        parent_uid=compendium_root.category("class").uid,
    )

    controller.refresh_project_tree()

    migrated = controller.project.nodes.get(node.uid)
    assert migrated is node
    assert migrated.parent_uid == compendium_root.category("subclass").uid