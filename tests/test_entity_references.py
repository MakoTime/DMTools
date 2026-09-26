from dataclasses import replace

import pytest
from projectfoundry import ArtifactStore
from PySide6.QtWidgets import QApplication, QDialog

from application.entity_references import (
    EntityNavigationController,
    EntityReference,
    _link_display_name,
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
        "display_fallback": "Fireball",
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


def test_spellcasting_progression_links_for_classes_and_subclasses():
    class_record = record(
        "class",
        "class-wizard",
        "Wizard",
        {
            "name": "Wizard",
            "hit_dice": "d6",
            "spellcasting": {"ability": "intelligence", "progression": "full"},
        },
    )
    subclass = record(
        "subclass",
        "subclass-eldritch-knight",
        "Eldritch Knight",
        {
            "name": "Eldritch Knight",
            "class": "Fighter",
            "features": [{
                "name": "Spellcasting",
                "description": "This subclass uses third spellcasting progression.",
            }],
        },
    )

    normalized = normalize_entity_references((class_record, subclass))

    assert {
        (reference["category"], reference["value"])
        for entity in normalized
        for reference in entity.source_metadata.get("entity_references", ())
        if reference["entity_type"] == "rule"
    } >= {
        ("spellcasting_progression", "full"),
        ("spellcasting_progression", "third"),
    }


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


def test_spell_lists_continue_across_blank_lines_in_monster_features():
    spell_names = [
        "Disguise Self",
        "Fog Cloud",
        "Identify",
        "Ray of Sickness",
        "Hold Person",
        "Locate Object",
    ]
    spells = [
        record("spell", f"spell-{index}", name, {"name": name})
        for index, name in enumerate(spell_names)
    ]
    monster = record(
        "monster",
        "monster-annis-hag",
        "Annis Hag",
        {
            "name": "Annis Hag",
            "features": [
                {
                    "name": "Innate Spellcasting",
                    "description": (
                        "She can innately cast the following spells:\n\n"
                        "3/day each: disguise self, fog cloud"
                    ),
                },
                {
                    "name": "Shared Spellcasting",
                    "description": (
                        "They can each cast the following spells from the wizard's spell list:\n\n"
                        "• 1st level (4 slots): identify, ray of sickness\n\n"
                        "• 2nd level (3 slots): hold person, locate object\n\n"
                        "For casting these spells, each hag is a 12th-level spellcaster."
                    ),
                },
            ],
        },
    )

    normalized = normalize_entity_references((*spells, monster))[-1]

    assert {
        reference["display_fallback"]
        for reference in entity_references(normalized)
        if reference["entity_type"] == "spell"
    } == set(spell_names)


def test_textual_spell_names_match_qualified_compendium_spell_names():
    spells = [
        record("spell", "spell-identify", "Identify*", {"name": "Identify*"}),
        record(
            "spell",
            "spell-disguise-self",
            "Disguise Self (Ritual Only)",
            {"name": "Disguise Self (Ritual Only)"},
        ),
    ]
    monster = record(
        "monster",
        "monster-caster",
        "Caster",
        {
            "name": "Caster",
            "features": [{
                "name": "Spellcasting",
                "description": "The creature can cast identify and disguise self.",
            }],
        },
    )

    normalized = normalize_entity_references((*spells, monster))[-1]

    assert {
        reference["display_fallback"]
        for reference in entity_references(normalized)
        if reference["entity_type"] == "spell"
    } == {"Identify", "Disguise Self (Ritual Only)"}


def test_textual_spell_name_resolves_unqualified_alias_of_qualified_record():
    spell = record(
        "spell",
        "spell-beast-sense",
        "Beast Sense (Ritual Only)",
        {"name": "Beast Sense (Ritual Only)"},
    )
    subclass = record(
        "subclass",
        "subclass-ranger",
        "Ranger",
        {
            "name": "Ranger",
            "features": [{
                "name": "Primal Awareness",
                "description": "At 5th level, the ranger can cast beast sense.",
            }],
        },
    )

    normalized = normalize_entity_references((spell, subclass))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.features[0].description:text",
        "target_uid": "spell-beast-sense",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Beast Sense (Ritual Only)",
    }]


def test_unqualified_spell_record_wins_over_editorial_qualified_duplicate():
    spells = [
        record("spell", "spell-identify", "Identify", {"name": "Identify"}),
        record("spell", "spell-identify-marked", "Identify*", {"name": "Identify*"}),
    ]
    monster = record(
        "monster",
        "monster-caster",
        "Caster",
        {
            "name": "Caster",
            "features": [{
                "name": "Spellcasting",
                "description": "The creature can cast identify.",
            }],
        },
    )

    normalized = normalize_entity_references((*spells, monster))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.features[0].description:text",
        "target_uid": "spell-identify",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Identify",
    }]


def test_structured_monster_spell_lists_strip_editorial_annotations():
    spells = [
        record("spell", "spell-mage-armor", "Mage Armor", {"name": "Mage Armor"}),
        record("spell", "spell-mind-blank", "Mind Blank", {"name": "Mind Blank"}),
        record("spell", "spell-time-stop", "Time Stop", {"name": "Time Stop"}),
    ]
    monster = record(
        "monster",
        "monster-archmage",
        "Archmage",
        {
            "name": "Archmage",
            "spell_casting": {
                "spells_known": {
                    "level_1": {"spells": ["mage armor*"]},
                    "level_8": {"spells": ["mind blank*"]},
                    "level_9": {
                        "spells": [
                            "time stop * The archmage casts these spells on itself before combat."
                        ]
                    },
                }
            },
        },
    )

    normalized = normalize_entity_references((*spells, monster))[-1]

    assert {
        reference["display_fallback"]
        for reference in entity_references(normalized)
        if reference["entity_type"] == "spell"
    } == {"Mage Armor", "Mind Blank", "Time Stop"}
    assert "reference_diagnostics" not in normalized.source_metadata


def test_structured_monster_spell_lists_strip_parenthetical_editorial_annotations():
    spell = record("spell", "spell-fire-shield", "Fire Shield", {"name": "Fire Shield"})
    monster = record(
        "monster",
        "monster-flamewrath",
        "Flamewrath",
        {
            "name": "Flamewrath",
            "spell_casting": {
                "spells_known": {
                    "level_4": {"spells": ["fire shield (see Wreathed in Flame)"]},
                }
            },
        },
    )

    normalized = normalize_entity_references((spell, monster))[-1]

    assert entity_references(normalized) == [{
        "path": "spell_casting.spells_known.level_4.spells[0]",
        "target_uid": "spell-fire-shield",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Fire Shield",
    }]
    assert "reference_diagnostics" not in normalized.source_metadata


def test_avarice_curly_apostrophe_spell_resolves_to_canonical_spell():
    spells = [
        record("spell", "spell-rary", "Rary's Telepathic Bond", {"name": "Rary's Telepathic Bond"}),
        record(
            "spell",
            "spell-rary-ritual",
            "Rary's Telepathic Bond (Ritual Only)",
            {"name": "Rary's Telepathic Bond (Ritual Only)"},
        ),
    ]
    avarice = record(
        "monster",
        "monster-avarice",
        "Avarice",
        {
            "name": "Avarice",
            "spell_casting": {
                "spells_known": {
                    "level_5": {"spells": ["Rary’s telepathic bond"]}
                }
            },
        },
    )

    normalized = normalize_entity_references((*spells, avarice))[-1]

    assert normalized.source_metadata["entity_references"] == [{
        "path": "spell_casting.spells_known.level_5.spells[0]",
        "target_uid": "spell-rary",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Rary's Telepathic Bond",
    }]
    assert "reference_diagnostics" not in normalized.source_metadata


def test_subclass_spell_lists_support_levels_above_ninth():
    spell_names = (
        "Blight",
        "Confusion",
        "Contagion",
        "Dominate Person",
    )
    spells = [
        record("spell", f"spell-{index}", name, {"name": name})
        for index, name in enumerate(spell_names)
    ]
    subclass = record(
        "subclass",
        "subclass-oathbreaker",
        "Oathbreaker",
        {
            "name": "Oathbreaker",
            "features": [{
                "name": "Sacred Oath: Oathbreaker",
                "description": (
                    "An Oathbreaker gains the following Oathbreaker spells at the paladin levels listed.\n\n"
                    "13th — blight, confusion\n\n"
                    "17th — contagion, dominate person"
                ),
            }],
        },
    )

    normalized = normalize_entity_references((*spells, subclass))[-1]

    assert {
        reference["display_fallback"]
        for reference in entity_references(normalized)
        if reference["entity_type"] == "spell"
    } == set(spell_names)


def test_damage_composites_create_rule_references():
    monster = record(
        "monster",
        "monster-damage",
        "Damage Test",
        {
            "name": "Damage Test",
            "damage_resistances": ["cold; bludgeoning"],
            "damage_immunities": ["piercing and slashing from nonmagical attacks"],
            "damage_vulnerabilities": ["fire"],
        },
    )

    normalized = normalize_entity_references((monster,))[0]

    assert {
        (reference["category"], reference["value"])
        for reference in normalized.source_metadata["entity_references"]
        if reference["entity_type"] == "rule"
    } >= {
        ("damage_type", "cold"),
        ("damage_type", "bludgeoning"),
        ("damage_type", "piercing"),
        ("damage_type", "slashing"),
        ("damage_type", "fire"),
    }


def test_link_display_names_use_pascal_case_with_lowercase_connectors():
    assert _link_display_name("hold person") == "Hold Person"
    assert _link_display_name("sword_of_kas") == "Sword of Kas"
    assert _link_display_name("damage and healing") == "Damage and Healing"


def test_textual_spell_mentions_in_entries_fields_are_normalized_to_uids():
    spell = record("spell", "spell-shield", "Shield", {"name": "Shield"})
    ability = record(
        "ability",
        "ability-ward",
        "Arcane Ward",
        {
            "name": "Arcane Ward",
            "entries": ["You can cast sHiElD when a creature attacks you."],
        },
    )

    normalized = normalize_entity_references((spell, ability))[-1]

    assert entity_references(normalized) == [{
        "path": "payload.entries[0]:text",
        "target_uid": "spell-shield",
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "Shield",
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
        "display_fallback": "Hold Person",
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


def test_refined_rule_contexts_require_explicit_effect_language():
    monster = record(
        "monster",
        "monster-refined-contexts",
        "Refined Contexts",
        {
            "name": "Refined Contexts",
            "features": [{
                "name": "Rules",
                "description": (
                    "It can fly, gains darkvision, deals fire damage, affects dragons, "
                    "and uses a reaction."
                ),
            }],
        },
    )
    item = record(
        "item",
        "item-unrelated-contexts",
        "Unrelated Contexts",
        {
            "name": "Unrelated Contexts",
            "description": "Its type and speed are listed for reference only.",
        },
    )

    normalized = normalize_entity_references((monster, item))
    monster_rules = {
        (reference["category"], reference["value"])
        for reference in normalized[0].source_metadata["entity_references"]
        if reference["entity_type"] == "rule"
    }
    item_rules = {
        (reference["category"], reference["value"])
        for reference in normalized[1].source_metadata.get("entity_references", ())
        if reference["entity_type"] == "rule"
    }

    assert monster_rules >= {
        ("movement_type", "fly"),
        ("sense", "darkvision"),
        ("damage_type", "fire"),
        ("creature_type", "dragon"),
        ("action_type", "reaction"),
    }
    assert item_rules == set()


def test_rule_references_bridge_across_all_entity_types():
    records = (
        record("spell", "spell-ward", "Ward", {
            "name": "Ward",
            "school": "abjuration",
            "components": ["verbal"],
            "description": "The spell deals fire damage to a fiend.",
        }),
        record("item", "item-ward", "Ward Item", {
            "name": "Ward Item",
            "category": "weapon",
            "cost": {"currency": "gp", "amount": 10},
            "magic_item": {"rarity": "rare"},
            "description": "This item grants resistance to fire damage.",
        }),
        record("race", "race-elf", "Elf", {
            "name": "Elf",
            "size": "medium",
            "movement": [{"movement_type": "walk", "speed": 30}],
            "skill_proficiencies": ["perception"],
            "languages": ["common"],
        }),
        record("class", "class-wizard", "Wizard", {
            "name": "Wizard",
            "hit_dice": "d6",
            "spellcasting": {"ability": "intelligence", "progression": "full"},
            "features": [{
                "name": "Spellcasting",
                "description": "You can take a bonus action to cast a spell.",
            }],
        }),
        record("subclass", "subclass-warder", "Warder", {
            "name": "Warder",
            "class": "Wizard",
            "features": [{
                "name": "Spellcasting",
                "description": "This uses half spellcasting progression.",
            }],
        }),
        record("monster", "monster-fiend", "Fiend", {
            "name": "Fiend",
            "challenge_rating": 1,
            "size": "medium",
            "creature_type": "fiend",
            "alignment": "evil",
            "movement": [{"movement_type": "fly", "speed": 60}],
            "senses": [{"type": "darkvision", "distance": 60, "distance_type": "feet"}],
            "damage_resistances": ["fire"],
            "condition_immunities": ["frightened"],
            "languages": ["common"],
        }),
        record("feat", "feat-ward", "Ward Master", {
            "name": "Ward Master",
            "prerequisite": "You must be resistant to fire damage.",
            "skill_proficiencies": ["arcana"],
        }),
        record("background", "background-guard", "Guard", {
            "name": "Guard",
            "skill_proficiencies": ["athletics"],
            "tool_proficiencies": ["smith_tools"],
            "languages": ["common"],
        }),
        record("ability", "ability-ward", "Ward Ability", {
            "name": "Ward Ability",
            "category": "passive",
            "effects": [{"description": "You gain darkvision and can target fiends."}],
        }),
    )

    normalized = normalize_entity_references(records)
    references_by_type = {
        entity.entity_type: {
            (reference["category"], reference["value"])
            for reference in entity.source_metadata.get("entity_references", ())
            if reference["entity_type"] == "rule"
        }
        for entity in normalized
    }

    assert references_by_type["spell"] >= {
        ("spell_school", "abjuration"),
        ("spell_component", "verbal"),
        ("damage_type", "fire"),
        ("creature_type", "fiend"),
    }
    assert references_by_type["item"] >= {
        ("item_category", "weapon"),
        ("currency", "gp"),
        ("rarity", "rare"),
        ("damage_type", "fire"),
    }
    assert references_by_type["race"] >= {
        ("size", "medium"),
        ("movement_type", "walk"),
        ("proficiencies-skills", "perception"),
        ("proficiencies-languages", "common"),
    }
    assert references_by_type["class"] >= {
        ("spellcasting_progression", "full"),
        ("action_type", "bonus_action"),
    }
    assert references_by_type["subclass"] >= {
        ("spellcasting_progression", "half"),
    }
    assert references_by_type["monster"] >= {
        ("creature_type", "fiend"),
        ("alignment", "evil"),
        ("movement_type", "fly"),
        ("sense", "darkvision"),
        ("damage_type", "fire"),
        ("conditions", "frightened"),
    }
    assert references_by_type["feat"] >= {
        ("proficiencies-skills", "arcana"),
        ("damage_type", "fire"),
    }
    assert references_by_type["background"] >= {
        ("proficiencies-skills", "athletics"),
        ("proficiencies-tools", "smith_tools"),
        ("proficiencies-languages", "common"),
    }
    assert references_by_type["ability"] >= {
        ("sense", "darkvision"),
        ("creature_type", "fiend"),
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


def test_single_word_armor_proficiency_links_shield_item():
    shield = record("item", "item-shield", "Shield", {
        "name": "Shield",
        "armor": {"category": "shield"},
    })
    fighter = record("class", "class-fighter", "Fighter", {
        "name": "Fighter",
        "armor_proficiencies": ["shields"],
    })

    normalized = normalize_entity_references((shield, fighter))[-1]

    assert {
        (reference["entity_type"], reference.get("target_uid"), reference.get("category"), reference.get("value"))
        for reference in normalized.source_metadata["entity_references"]
    } == {
        ("item", "item-shield", None, None),
        ("rule", "dmtools-compendium-rules-proficiencies-armor-shield", "proficiencies-armor", "shield"),
    }


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


def test_project_controller_resolves_all_matching_unresolved_references(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    target = record(
        "subclass",
        "subclass-clockwork-soul",
        "Clockwork Soul",
        {"name": "Clockwork Soul"},
    )
    diagnostic = {
        "path": "classes[4]",
        "entity_type": "class",
        "display_fallback": "sorcerer (clockwork)",
        "status": "missing",
        "candidate_uids": (),
    }
    first = record(
        "item", "item-one", "One", {"name": "One"}
    )
    first = replace(first, source_metadata={"reference_diagnostics": [diagnostic]})
    second = record(
        "item", "item-two", "Two", {"name": "Two"}
    )
    second = replace(second, source_metadata={"reference_diagnostics": [diagnostic]})
    controller.commit_imported_entities((target,))
    controller.persist_imported_entities((first,))
    controller.persist_imported_entities((second,), namespace="homebrew")

    updated = controller.resolve_unresolved_reference(
        "class", "sorcerer (clockwork)", target.uid
    )

    assert set(updated) == {first.uid, second.uid}
    for uid in (first.uid, second.uid):
        stored = controller.resolve_entity(uid)
        assert stored.source_metadata["entity_references"] == [{
            "path": "classes[4]",
            "target_uid": target.uid,
            "entity_type": "subclass",
            "source_namespace": "compendium",
            "display_fallback": "Sorcerer (Clockwork)",
        }]
        assert stored.source_metadata["manual_entity_references"] == [{
            "path": "classes[4]",
            "target_uid": target.uid,
            "entity_type": "subclass",
            "source_namespace": "compendium",
            "display_fallback": "Sorcerer (Clockwork)",
        }]
        assert "reference_diagnostics" not in stored.source_metadata


def test_project_controller_marks_one_unresolved_reference_as_intended(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    controller.commit_imported_entities((record("spell", "spell-sacred-flame", "Sacred Flame", {"name": "Sacred Flame"}),))
    source = record("monster", "monster-thurstwell", "Thurstwell", {"name": "Thurstwell"})
    diagnostic = {
        "path": "spell_casting.spells_known.cantrips[1]",
        "entity_type": "spell",
        "display_fallback": 'Sacred Flame (See "Actions" Below)',
        "status": "missing",
    }
    source = replace(source, source_metadata={"reference_diagnostics": [diagnostic]})
    controller.persist_imported_entities((source,))

    assert controller.mark_reference_intended(
        source.uid, diagnostic["path"]
    ) is True

    stored = controller.resolve_entity(source.uid)
    assert "reference_diagnostics" not in stored.source_metadata
    assert stored.source_metadata["ignored_reference_diagnostics"] == [diagnostic]
    assert "entity_references" not in stored.source_metadata


def test_project_controller_resolves_one_reference_to_multiple_targets(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    first_target = record("spell", "spell-sacred-flame", "Sacred Flame", {"name": "Sacred Flame"})
    second_target = record("spell", "spell-thaumaturgy", "Thaumaturgy", {"name": "Thaumaturgy"})
    source = record("monster", "monster-thurstwell", "Thurstwell", {"name": "Thurstwell"})
    diagnostic = {
        "path": "spell_casting.spells_known.cantrips[1]",
        "entity_type": "spell",
        "display_fallback": "Sacred Flame",
        "status": "missing",
    }
    source = replace(source, source_metadata={"reference_diagnostics": [diagnostic]})
    controller.commit_imported_entities((first_target, second_target))
    controller.persist_imported_entities((source,))

    controller.resolve_unresolved_reference(
        "spell", "Sacred Flame", (first_target.uid, second_target.uid)
    )

    stored = controller.resolve_entity(source.uid)
    assert [reference["target_uid"] for reference in stored.source_metadata["entity_references"]] == [
        first_target.uid,
        second_target.uid,
    ]


def test_project_controller_replaces_existing_resolved_reference(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    first_target = record("spell", "spell-first", "First Spell", {"name": "First Spell"})
    second_target = record("spell", "spell-second", "Second Spell", {"name": "Second Spell"})
    source = record("monster", "monster-source", "Source", {"name": "Source"})
    source = replace(source, source_metadata={"entity_references": [{
        "path": "spellcasting.cantrips[0]",
        "target_uid": first_target.uid,
        "entity_type": "spell",
        "source_namespace": "compendium",
        "display_fallback": "First Spell",
    }]})
    controller.commit_imported_entities((first_target, second_target))
    controller.persist_imported_entities((source,))

    controller.replace_resolved_reference(
        source.uid,
        "spellcasting.cantrips[0]",
        "spell",
        "First Spell",
        second_target.uid,
    )

    stored = controller.resolve_entity(source.uid)
    assert stored.source_metadata["entity_references"][0]["target_uid"] == second_target.uid
    assert stored.source_metadata["manual_entity_references"][0]["target_uid"] == second_target.uid


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