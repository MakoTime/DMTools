from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore

from application.entity_references import (
    EntityNavigationController,
    EntityReference,
    normalize_entity_references,
)
from application.imports import EntityImportService, ImportedEntityRecord
from application.project_controller import ProjectController


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def record(entity_type, uid, name, payload):
    return ImportedEntityRecord(
        entity_type=entity_type,
        uid=uid,
        source_identity=f"source:{entity_type}:{uid}",
        display_name=name,
        payload=payload,
    )


def test_structured_references_normalize_to_uids_without_changing_payload():
    spell = record("spell", "spell-fireball", "Fireball", {"name": "Fireball"})
    item = record(
        "item",
        "item-wand",
        "Wand",
        {"name": "Wand", "magic_item": {"spells": [{"spell": "fireball"}]}},
    )

    normalized_spell, normalized_item = normalize_entity_references((spell, item))

    reference = normalized_item.source_metadata["entity_references"][0]
    assert reference == {
        "path": "magic_item.spells[0].spell",
        "target_uid": spell.uid,
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "fireball",
    }
    assert normalized_item.payload == item.payload
    assert normalized_spell.source_metadata == {}


def test_missing_and_ambiguous_references_keep_diagnostics():
    first = record("spell", "spell-1", "Alarm", {"name": "Alarm"})
    second = replace(first, uid="spell-2", source_identity="source:spell:2")
    feat = record(
        "feat",
        "feat-1",
        "Magic",
        {"name": "Magic", "spell_grants": [{"spells": ["Alarm", "Shield"]}]},
    )

    normalized = normalize_entity_references((first, second, feat))[-1]
    diagnostics = normalized.source_metadata["reference_diagnostics"]

    assert [item["status"] for item in diagnostics] == ["ambiguous", "missing"]
    assert diagnostics[0]["candidate_uids"] == ("spell-1", "spell-2")


def test_class_and_subclass_spell_grants_are_normalized():
    spell = record("spell", "spell-shield", "Shield", {"name": "Shield"})
    class_record = record(
        "class", "class-wizard", "Wizard",
        {"name": "Wizard", "hit_dice": "d6", "spellcasting": {
            "ability": "intelligence", "progression": "full",
            "spells": {"spells": ["Shield"]},
        }},
    )
    subclass = record(
        "subclass", "subclass-abjurer", "Abjurer",
        {"name": "Abjurer", "class": "wizard", "spells": [{"spells": ["Shield"]}]},
    )

    normalized = normalize_entity_references((spell, class_record, subclass))

    assert len(normalized[1].source_metadata["entity_references"]) == 1
    assert len(normalized[2].source_metadata["entity_references"]) == 1


def test_textual_spell_mentions_are_normalized_to_uids():
    spell = record("spell", "spell-fireball", "Fireball", {"name": "Fireball"})
    monster = record(
        "monster",
        "monster-wizard",
        "Wizard",
        {"name": "Wizard", "features": [{"name": "Spellcasting", "description": "The wizard casts Fireball."}]},
    )

    normalized = normalize_entity_references((spell, monster))[-1]

    assert normalized.source_metadata["entity_references"] == [{
        "path": "payload.features[0].description:text",
        "target_uid": "spell-fireball",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Fireball",
    }]


def test_option_prefixed_spell_reference_resolves_to_canonical_spell():
    spell = record("spell", "spell-hold-person", "Hold Person", {"name": "Hold Person"})
    item = record(
        "item",
        "item-wand",
        "Wand of Binding",
        {
            "name": "Wand of Binding",
            "description": "Cast hold monster or hold person.",
            "magic_item": {"spells": [{"spell": "or hold person"}]},
        },
    )

    normalized = normalize_entity_references((spell, item))[-1]

    assert normalized.source_metadata["entity_references"] == [{
        "path": "magic_item.spells[0].spell",
        "target_uid": "spell-hold-person",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "hold person",
    }]
    assert "reference_diagnostics" not in normalized.source_metadata


def test_spell_class_lists_resolve_qualified_entries_to_subclasses():
    subclasses = (
        record("subclass", "subclass-eldritch-knight", "Eldritch Knight", {"name": "Eldritch Knight"}),
        record("subclass", "subclass-arcane-trickster", "Arcane Trickster", {"name": "Arcane Trickster"}),
        record("subclass", "subclass-swarmkeeper", "Swarmkeeper", {"name": "Swarmkeeper"}),
    )
    spell = record(
        "spell",
        "spell-acid-splash",
        "Acid Splash",
        {
            "name": "Acid Splash",
            "classes": [
                "fighter (eldritch knight)",
                "rogue (arcane trickster)",
                "ranger (swarmkeeper)",
            ],
        },
    )

    normalized = normalize_entity_references((*subclasses, spell))[-1]

    assert [reference["entity_type"] for reference in normalized.source_metadata["entity_references"]] == [
        "subclass", "subclass", "subclass",
    ]
    assert "reference_diagnostics" not in normalized.source_metadata


def test_reference_resolution_validates_namespace_and_type(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    imported = EntityImportService().preview_xml(ITEM_XML).records[0]
    controller.commit_imported_entities((imported,))
    reference = EntityReference(
        imported.uid, "item", "compendium", imported.display_name
    )

    assert controller.resolve_entity_reference(reference).uid == imported.uid
    with pytest.raises(ValueError, match="namespace"):
        controller.resolve_entity_reference(replace(reference, source_namespace="homebrew"))
    with pytest.raises(ValueError, match="type"):
        controller.resolve_entity_reference(replace(reference, entity_type="spell"))


def test_later_homebrew_commit_resolves_existing_compendium_reference(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    spell = record("spell", "spell-fireball", "Fireball", {"name": "Fireball"})
    item = record(
        "item",
        "item-wand",
        "Wand",
        {"name": "Wand", "magic_item": {"spells": [{"spell": "fireball"}]}},
    )

    controller.commit_imported_entities((spell,))
    controller.commit_imported_entities((item,), namespace="homebrew")

    stored = controller.resolve_entity(item.uid)
    reference = stored.source_metadata["entity_references"][0]
    assert reference["target_uid"] == spell.uid
    assert reference["source_namespace"] == "compendium"


def test_navigation_reuses_entities_preserves_back_context_and_rejects_cycle():
    first = type("Entity", (), {"uid": "first"})()
    second = type("Entity", (), {"uid": "second"})()

    class Controller:
        def __init__(self):
            self.calls = []

        def resolve_entity_reference(self, reference):
            self.calls.append(reference.target_uid)
            return {"first": first, "second": second}[reference.target_uid]

        def resolve_entity(self, entity_uid):
            self.calls.append(entity_uid)
            return {"first": first, "second": second}[entity_uid]

    controller = Controller()
    navigation = EntityNavigationController(controller)
    second_reference = EntityReference("second", "item", "compendium")

    assert navigation.open(second_reference, origin_uid="first") is second
    assert navigation.open(second_reference) is second
    assert controller.calls == ["second"]
    assert navigation.back() is first

    navigation.open(second_reference, origin_uid="first")
    with pytest.raises(ValueError, match="Circular"):
        navigation.open(
            EntityReference("first", "item", "compendium"), origin_uid="second"
        )