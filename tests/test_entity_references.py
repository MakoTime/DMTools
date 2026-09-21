from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore
from PySide6.QtWidgets import QApplication, QDialog

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


def entity_references(entity):
    return [
        reference
        for reference in entity.source_metadata.get("entity_references", ())
        if reference["entity_type"] != "rule"
    ]


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

    assert len(entity_references(normalized[1])) == 1
    assert [reference["entity_type"] for reference in entity_references(normalized[2])] == [
        "class", "spell",
    ]


def test_textual_spell_mentions_are_normalized_to_uids():
    spell = record("spell", "spell-fireball", "Fireball", {"name": "Fireball"})
    monster = record(
        "monster",
        "monster-wizard",
        "Wizard",
        {"name": "Wizard", "features": [{"name": "Spellcasting", "description": "The wizard casts Fireball."}]},
    )

    normalized = normalize_entity_references((spell, monster))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.features[0].description:text",
        "target_uid": "spell-fireball",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Fireball",
    }]


def test_item_spell_feature_registers_lowercase_spell_names():
    spell = record("spell", "spell-call-lightning", "Call Lightning", {"name": "Call Lightning"})
    item = record(
        "item",
        "item-sword-of-kas",
        "Sword of Kas",
        {
            "name": "Sword of Kas",
            "features": [{
                "name": "Spells",
                "description": (
                    "While the sword is on your person, you can use an action to "
                    "cast one of the following spells: call lightning, divine word, "
                    "or finger of death."
                ),
            }],
        },
    )

    normalized = normalize_entity_references((spell, item))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.features[0].description:text",
        "target_uid": "spell-call-lightning",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Call Lightning",
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

    assert entity_references(normalized) == [{
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


def test_schema_backed_class_feat_and_equipment_references_are_normalized():
    parent_class = record("class", "class-fighter", "Fighter", {"name": "Fighter"})
    subclass = record("subclass", "subclass-champion", "Champion", {
        "name": "Champion", "class": "Fighter",
    })
    feat = record("feat", "feat-alert", "Alert", {"name": "Alert"})
    race = record("race", "race-human", "Human", {
        "name": "Human", "feats": ["Alert"],
    })
    item = record("item", "item-crossbow", "Light Crossbow", {
        "name": "Light Crossbow",
    })
    background = record("background", "background-soldier", "Soldier", {
        "name": "Soldier",
        "equipment": [{"item": {"name": "Light Crossbow"}}],
    })

    normalized = normalize_entity_references(
        (parent_class, subclass, feat, race, item, background)
    )

    assert normalized[1].source_metadata["entity_references"] == [{
        "path": "class",
        "target_uid": "class-fighter",
        "entity_type": "class",
        "source_namespace": "compendium",
        "display_fallback": "Fighter",
    }]
    assert entity_references(normalized[3]) == [{
        "path": "feats[0]",
        "target_uid": "feat-alert",
        "entity_type": "feat",
        "source_namespace": "compendium",
        "display_fallback": "Alert",
    }]
    assert entity_references(normalized[5]) == [{
        "path": "equipment[0].item",
        "target_uid": "item-crossbow",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Light Crossbow",
    }]


def test_all_major_structured_rule_sections_create_rule_references():
    spell = record(
        "spell",
        "spell-fireball",
        "Fireball",
        {
            "name": "Fireball",
            "school": "evocation",
            "components": ["verbal"],
        },
    )
    monster = record(
        "monster",
        "monster-dragon",
        "Dragon",
        {
            "name": "Dragon",
            "size": "huge",
            "creature_type": "dragon",
            "alignment": "unaligned",
            "languages": ["common"],
            "condition_immunities": ["frightened"],
            "damage_resistances": ["fire"],
        },
    )
    item = record(
        "item",
        "item-sword",
        "Sword",
        {
            "name": "Sword",
            "weapon": {
                "type": "longsword",
                "properties": ["versatile"],
            },
            "cost": {"currency": "gp", "amount": 15},
            "magic_item": {"rarity": "rare"},
        },
    )
    weapon = record(
        "weapon",
        "weapon-sword",
        "Longsword",
        {
            "name": "Longsword",
            "category": "martial",
            "weapon_type": "longsword",
            "damage": {"type": "slashing"},
            "properties": ["versatile"],
        },
    )

    normalized = normalize_entity_references((spell, monster, item, weapon))
    references = [
        reference
        for entity in normalized
        for reference in entity.source_metadata.get("entity_references", ())
        if reference["entity_type"] == "rule"
    ]

    assert {
        (reference["category"], reference["value"])
        for reference in references
    } >= {
        ("spell_school", "evocation"),
        ("spell_component", "verbal"),
        ("size", "huge"),
        ("creature_type", "dragon"),
        ("alignment", "unaligned"),
        ("proficiencies-languages", "common"),
        ("conditions", "frightened"),
        ("damage_type", "fire"),
        ("weapons-groups", "martial"),
        ("weapons-types", "longsword"),
        ("weapons-tags", "versatile"),
        ("currency", "gp"),
        ("rarity", "rare"),
    }


def test_rule_values_in_feature_descriptions_create_rule_references():
    monster = record(
        "monster",
        "monster-warder",
        "Warder",
        {
            "name": "Warder",
            "features": [{
                "name": "Ward",
                "description": (
                    "The warder is poisoned, has fire damage resistance, "
                    "and has darkvision."
                ),
            }],
        },
    )

    normalized = normalize_entity_references((monster,))[0]
    references = normalized.source_metadata["entity_references"]

    assert {
        (reference["category"], reference["value"])
        for reference in references
        if reference["entity_type"] == "rule"
    } >= {
        ("conditions", "poisoned"),
        ("damage_type", "fire"),
        ("sense", "darkvision"),
    }


def test_equipment_section_links_items_but_not_light_spell():
    spell = record("spell", "spell-light", "Light", {"name": "Light"})
    item = record("item", "item-crossbow", "Light Crossbow", {
        "name": "Light Crossbow",
    })
    class_record = record("class", "class-fighter", "Fighter", {
        "name": "Fighter",
        "features": [{
            "name": "Equipment",
            "description": "You start with light armour and a Light Crossbow.",
        }],
    })

    normalized = normalize_entity_references((spell, item, class_record))[-1]

    assert entity_references(normalized) == [{
        "path": "features[0].description:text",
        "target_uid": "item-crossbow",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Light Crossbow",
    }]


def test_light_spell_does_not_match_inside_light_crossbow_in_spellcasting_text():
    spell = record("spell", "spell-light", "Light", {"name": "Light"})
    item = record("item", "item-crossbow", "Light Crossbow", {
        "name": "Light Crossbow",
    })
    class_record = record("class", "class-bard", "Bard", {
        "name": "bard",
        "description": (
            "Spellcasting ability: Charisma.\n\n"
            "Equipment: a Light Crossbow."
        ),
    })

    normalized = normalize_entity_references((spell, item, class_record))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.description:text",
        "target_uid": "item-crossbow",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Light Crossbow",
    }]


def test_domain_choice_named_light_is_not_linked_as_spell():
    spell = record("spell", "spell-light", "Light", {"name": "Light"})
    cleric = record("class", "class-cleric", "Cleric", {
        "name": "Cleric",
        "features": [{
            "name": "Divine Domain",
            "description": (
                "Choose one domain related to your deity: Arcana, Death, "
                "Forge, Grave, Knowledge, Life, Light, Nature, Order, Peace, "
                "Tempest, Trickery, Twilight, or War."
            ),
        }],
    })

    normalized = normalize_entity_references((spell, cleric))[-1]

    assert "entity_references" not in normalized.source_metadata


def test_sorcerer_starting_sections_keep_light_crossbow_out_of_spell_matching():
    light_spell = record("spell", "spell-light", "Light", {"name": "Light"})
    light_crossbow = record("item", "item-light-crossbow", "Light Crossbow", {
        "name": "Light Crossbow",
    })
    sorcerer = record("class", "class-sorcerer", "Sorcerer", {
        "name": "Sorcerer",
        "description": (
            "Starting Sorcerer (1st level)\n\n"
            "You are proficient with the following items.\n\n"
            "• Armor: none\n\n"
            "• Weapons: daggers, darts, slings, quarterstaffs, Light crossbows\n\n"
            "• Tools: none\n\n"
            "You begin play with the following equipment.\n\n"
            "• (a) a Light Crossbow and 20 bolts or (b) any simple weapon\n\n"
            "Alternatively, you may start with 3d4x10 gp."
        ),
    })

    normalized = normalize_entity_references(
        (light_spell, light_crossbow, sorcerer)
    )[-1]

    assert entity_references(normalized) == [{
        "path": "payload.description:text",
        "target_uid": "item-light-crossbow",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Light Crossbow",
    }]


def test_multiclass_proficiency_section_links_concrete_items():
    hand_crossbow = record("item", "item-hand-crossbow", "Hand Crossbow", {
        "name": "Hand Crossbow",
    })
    class_record = record("class", "class-bard", "Bard", {
        "name": "Bard",
        "features": [{
            "name": "Multiclass Bard",
            "description": (
                "You gain the following proficiencies:\n\n"
                "• light armor, hand crossbows, and one musical instrument."
            ),
        }],
    })

    normalized = normalize_entity_references((hand_crossbow, class_record))[-1]

    assert entity_references(normalized) == [{
        "path": "features[0].description:text",
        "target_uid": "item-hand-crossbow",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Hand Crossbow",
    }]


def test_bard_descriptions_resolve_lowercase_plural_items_and_spells():
    spell = record("spell", "spell-cure-wounds", "Cure Wounds", {
        "name": "Cure Wounds",
    })
    hand_crossbow = record("item", "item-hand-crossbow", "Hand Crossbow", {
        "name": "Hand Crossbow",
    })
    longsword = record("item", "item-longsword", "Longsword", {
        "name": "Longsword",
    })
    bard = record("class", "class-bard", "Bard", {
        "name": "bard",
        "description": (
            "Weapons: simple weapons, hand crossbows, longswords."
        ),
        "features": [{
            "name": "Spellcasting",
            "description": "You can cast cure wounds using a spell slot.",
        }],
    })

    normalized = normalize_entity_references(
        (spell, hand_crossbow, longsword, bard)
    )[-1]

    references = normalized.source_metadata["entity_references"]
    assert {reference["target_uid"] for reference in references} == {
        "spell-cure-wounds",
        "item-hand-crossbow",
        "item-longsword",
    }


def test_tool_proficiency_links_matching_item_name():
    tool = record("item", "item-disguise-kit", "Disguise Kit", {
        "name": "Disguise Kit",
    })
    background = record("background", "background-charlatan", "Charlatan", {
        "name": "Charlatan", "tool_proficiencies": ["disguise_kit"],
    })

    normalized = normalize_entity_references((tool, background))[-1]

    assert entity_references(normalized) == [{
        "path": "tool_proficiencies[0]",
        "target_uid": "item-disguise-kit",
        "entity_type": "item",
        "source_namespace": "compendium",
        "display_fallback": "Disguise Kit",
    }]


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


def test_project_controller_rebuilds_references_without_reimporting(tmp_path):
    QApplication.instance() or QApplication([])
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    spell = record("spell", "spell-fireball", "Fireball", {"name": "Fireball"})
    item = record(
        "item",
        "item-wand",
        "Wand",
        {
            "name": "Wand",
            "description": "The wand casts Fireball.",
            "magic_item": {"spells": [{"spell": "Fireball"}]},
        },
    )
    controller.commit_imported_entities((spell,), namespace="compendium")
    controller.commit_imported_entities((item,), namespace="homebrew")

    progress = []

    class ImmediateProgressDialog:
        def __init__(self, work):
            self.work = work
            self.model = type("Model", (), {"result": None})()

        def exec(self):
            self.model.result = self.work(
                lambda current, total: progress.append((current, total)),
                lambda: False,
            )
            return QDialog.DialogCode.Accepted

    controller.normalize_entity_references(
        progress_factory=lambda task_runner, work, source_name, **kwargs: (
            ImmediateProgressDialog(work)
        )
    )

    assert progress == [(1, 2), (2, 2)]
    stored = controller.resolve_entity(item.uid)
    assert stored.source_metadata["entity_references"]
    assert stored.source_metadata["entity_references"][0]["target_uid"] == spell.uid


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