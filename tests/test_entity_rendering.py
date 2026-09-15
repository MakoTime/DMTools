from types import SimpleNamespace

import pytest

from application.entity_rendering import (
    presentation_contract,
    render_entity_html,
    render_entity_markdown,
)


def entity(entity_type="item", payload=None, metadata=None):
    return SimpleNamespace(
        uid="entity-1",
        name="<Unsafe> Pack",
        entity_type=entity_type,
        source_namespace="homebrew",
        payload=payload or {"weight": 5, "features": ["Useful"]},
        source_metadata=metadata or {},
    )


def test_renderer_supports_all_canonical_entity_types():
    for entity_type in (
        "item", "spell", "race", "class", "subclass", "monster",
        "feat", "background", "ability",
    ):
        markdown = render_entity_markdown(entity(entity_type))
        assert "# <Unsafe> Pack" in markdown
        assert "dmtools-entity-uid: entity-1" in markdown


def test_markdown_supports_empty_entities_and_homebrewery_style_tables():
    for entity_type in (
        "item", "spell", "race", "class", "subclass", "monster",
        "feat", "background", "ability",
    ):
        rendered = render_entity_markdown(entity(entity_type, payload={}))
        assert "# <Unsafe> Pack" in rendered
        assert "None" not in rendered

    rendered = render_entity_markdown(
        entity(
            payload={
                "name": "Pack",
                "table": [
                    {"property": "Weight", "value": "5 lb"},
                    {"property": "Value", "value": "2 gp"},
                ],
                "callout": {"title": "At a Glance", "text": "Useful gear."},
            }
        )
    )
    assert "### Table" in rendered
    assert "| property | value |" in rendered
    assert "| Weight | 5 lb |" in rendered
    assert "> **At a Glance:** Useful gear." in rendered


def test_presentation_contract_defines_stable_type_specific_field_order():
    entity_types = (
        "item", "spell", "race", "class", "subclass", "monster",
        "feat", "background", "ability",
    )

    for entity_type in entity_types:
        fields = presentation_contract(entity_type)
        assert fields[0] == "name"
        assert len(fields) == len(set(fields))

    with pytest.raises(ValueError, match="Unsupported entity type"):
        presentation_contract("unknown")


def test_html_escapes_untrusted_text_and_emits_uid_reference_links():
    html = render_entity_html(
        entity(
            payload={"name": "Pack", "description": "Contains Fireball."},
            metadata={
                "entity_references": [{
                    "target_uid": "spell-1",
                    "entity_type": "spell",
                    "source_namespace": "compendium",
                    "display_fallback": "Fireball",
                }],
                "reference_diagnostics": [{
                    "display_fallback": "Missing Spell",
                    "status": "missing",
                    "path": "classes[0]",
                }],
            }
        )
    )

    assert "&lt;Unsafe&gt; Pack" in html
    assert 'data-template-version="1"' in html
    assert 'data-css-version="1"' in html
    assert "dmtools://entity/spell-1" in html
    assert "Missing Spell" in html
    assert "<script>" not in html


def test_monster_spell_references_render_as_selectable_spell_links():
    rendered = render_entity_html(
        entity(
            entity_type="monster",
            payload={
                "name": "Caster",
                "features": [{"name": "Spellcasting", "description": "Casts Fireball."}],
            },
            metadata={
                "entity_references": [
                    {
                        "target_uid": "spell-fireball",
                        "entity_type": "spell",
                        "source_namespace": "compendium",
                        "display_fallback": "Fireball",
                    }
                ]
            },
        )
    )

    assert 'href="dmtools://entity/spell-fireball"' in rendered
    assert "Fireball" in rendered
    assert "<h2>Spells</h2>" not in rendered


def test_monster_html_preserves_stat_block_formatting():
    rendered = render_entity_html(
        entity(
            entity_type="monster",
            payload={
                "name": "Owlbear",
                "size": "large",
                "creature_type": "monstrosity",
                "alignment": {"order": "neutral", "morality": "good"},
                "ability_scores": {},
                "features": [{"name": "Keen Sight", "description": "It sees well."}],
            },
        )
    )

    assert "<em>Large, Monstrosity, Neutral Good</em>" in rendered
    assert "<hr>" in rendered
    assert "<h3>Traits</h3>" in rendered
    assert "<strong><em>Keen Sight.</em></strong> It sees well." in rendered
    assert "<li>--</li>" not in rendered


def test_any_spell_bearing_entity_renders_spell_links_section():
    rendered = render_entity_markdown(
        entity(
            entity_type="item",
            payload={"name": "Wand", "description": "Casts Shield."},
            metadata={
                "entity_references": [{
                    "target_uid": "spell-shield",
                    "entity_type": "spell",
                    "source_namespace": "compendium",
                    "display_fallback": "Shield",
                }]
            },
        )
    )

    assert "[Shield](dmtools://entity/spell-shield)" in rendered
    assert "## Spells" not in rendered


def test_renderers_follow_type_specific_field_order():
    item = entity(
        payload={"description": "Details", "weight": 5, "name": "Pack"}
    )

    markdown = render_entity_markdown(item)
    assert markdown.index("**Weight:**") < markdown.index("**Description:**")


def test_renderers_follow_stat_block_and_spell_block_order():
    monster = entity(
        entity_type="monster",
        payload={
            "description": "Lore",
            "actions": [],
            "challenge_rating": 2,
            "armor_class": {"value": 13},
            "name": "Wolf",
        },
    )
    spell = entity(
        entity_type="spell",
        payload={
            "description": "Effect",
            "duration": {"amount": 1},
            "components": ["verbal"],
            "level": 1,
            "name": "Shield",
        },
    )

    monster_markdown = render_entity_markdown(monster)
    spell_markdown = render_entity_markdown(spell)
    assert monster_markdown.index("### Armor Class") < monster_markdown.index(
        "### Actions"
    )
    assert monster_markdown.index("**Challenge Rating:**") < monster_markdown.index(
        "**Description:**"
    )
    assert spell_markdown.index("- **Level:**") < spell_markdown.index(
        "### Components"
    )
    assert spell_markdown.index("- **Duration:**") < spell_markdown.index(
        "**Description:**"
    )

def test_monster_renderer_formats_structured_alignment():
    rendered = render_entity_markdown(
        entity(
            entity_type="monster",
            payload={
                "name": "Owlbear",
                "size": "large",
                "creature_type": "monstrosity",
                "alignment": {"order": "neutral", "morality": "good"},
                "ability_scores": {},
            },
        )
    )

    assert "*Large, Monstrosity, Neutral Good*" in rendered


def test_named_display_objects_use_bold_name_and_description_line():
    markdown = render_entity_markdown(
        entity(
            payload={
                "name": "Pack",
                "features": [{"name": "Useful Gear", "description": "A handy pack."}],
            }
        )
    )
    html = render_entity_html(
        entity(
            payload={
                "name": "Pack",
                "features": [{"name": "Useful Gear", "description": "A handy pack."}],
            }
        )
    )

    assert "- **Useful Gear**  \n  A handy pack." in markdown
    assert "**name:** Useful Gear" not in markdown
    assert "**description:** A handy pack." not in markdown
    assert "<li><strong>Useful Gear</strong><br>A handy pack.</li>" in html


def test_same_entity_feature_source_is_not_repeated():
    rendered = render_entity_markdown(
        entity(
            payload={
                "name": "Pack",
                "features": [{
                    "name": "Useful Gear",
                    "description": "A handy pack.",
                    "source": {"text": "homebrew"},
                }],
            }
        )
    )

    assert "**source:** homebrew" not in rendered


def test_feature_metadata_is_separated_and_source_mappings_are_readable():
    rendered = render_entity_markdown(
        entity(
            payload={
                "name": "Bard",
                "features": [{
                    "name": "Starting Bard",
                    "description": "As a 1st-level Bard.",
                    "level": 1,
                    "source": {"text": "Player's Handbook p. 51"},
                }],
                "tool_proficiencies": ["three_musical_instruments_of_your_choice"],
            }
        )
    )

    assert "- **Starting Bard**  \n  As a 1st-level Bard.\n\n" in rendered
    assert "As a 1st-level Bard.\n\n- **Level:** 1" in rendered
    assert "  **Source:** Player's Handbook p. 51" in rendered
    assert "Player's Handbook p. 51" in rendered
    assert "{'text':" not in rendered
    assert "Three Musical Instruments Of Your Choice" in rendered


def test_class_progression_precedes_feature_details():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Wizard",
                "features": [{"name": "Spellcasting", "level": 1, "description": "Details"}],
                "description": "Class details",
            },
        )
    )

    assert rendered.index("## Level Progression") < rendered.index("### Features")


def test_class_progression_renders_available_levels_without_fabricating_slots():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Wizard",
                "features": [
                    {"name": "Spellcasting", "level": 1, "description": ""},
                    {"name": "Arcane Recovery", "level": 2, "description": ""},
                ],
                "spellcasting": {"ability": "intelligence", "progression": "full"},
            },
        )
    )

    assert "## Level Progression" in rendered
    assert "| Level | Proficiency Bonus | Features | 1st | 2nd |" in rendered
    assert "| 1st | +2 | Spellcasting | 2 | - | - | - | - | - | - | - |" in rendered
    assert "| 2nd | +2 | Arcane Recovery | 3 | - | - | - | - | - | - | - |" in rendered
    assert "| 20th | +6 | - | 4 | 3 | 3 | 3 | 2 | 1 | 1 | 1 | 1 |" in rendered
    assert "Cantrips Known" not in rendered


def test_class_progression_projection_renders_cantrips_and_spell_slots():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Druid",
                "features": [{"name": "Druidic", "level": 1}],
                "presentation_progression": {
                    "cantrips_known": {1: 2, 2: 2, 3: 2},
                    "spell_slots": {
                        "1": {1: 2, 2: 3, 3: 4},
                        "2": {3: 2},
                    },
                },
            },
        )
    )

    assert "| Level | Proficiency Bonus | Features | Cantrips Known | 1st | 2nd |" in rendered
    assert "| 1st | +2 | Druidic | 2 | 2 | - |" in rendered
    assert "| 3rd | +2 | - | 2 | 4 | 2 |" in rendered


def test_class_progression_mentions_one_generic_subclass_feature_per_level():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Bard",
                "features": [{"name": "Bardic Inspiration", "level": 1}],
            },
            metadata={
                "subclass_progression": [
                    {"subclass": "College of Lore", "level": 3, "feature": "Cutting Words"},
                    {"subclass": "College of Valor", "level": 3, "feature": "Combat Inspiration"},
                ],
            },
        )
    )

    assert "| 3rd | +2 | Bard College Feature |" in rendered
    assert "Cutting Words" not in rendered
    assert "Combat Inspiration" not in rendered


def test_html_renders_progression_as_a_table():
    html = render_entity_html(
        entity(
            entity_type="class",
            payload={
                "name": "Wizard",
                "features": [{"name": "Spellcasting", "level": 1}],
                "spellcasting": {"ability": "intelligence", "progression": "full"},
            },
        )
    )

    assert "<table><thead><tr>" in html
    assert "<th>Level</th>" in html
    assert "<td>1st</td>" in html
    assert "<p>| Level |" not in html


def test_subclass_progression_renders_feature_levels():
    rendered = render_entity_markdown(
        entity(
            entity_type="subclass",
            payload={
                "name": "Champion",
                "class": "fighter",
                "features": [
                    {"name": "Improved Critical", "level": 3, "description": ""},
                ],
            },
        )
    )

    assert "## Level Progression" in rendered
    assert "| Level | Features |" in rendered
    assert "| 1 |  |" in rendered
    assert "| 3 | Improved Critical |" in rendered


def test_bard_uses_phb_table_then_class_feature_order():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Bard",
                "hit_dice": 8,
                "features": [
                    {"name": "Hit Points", "description": "Vitality."},
                    {"name": "Proficiencies", "description": "Training."},
                    {"name": "Equipment", "description": "Gear."},
                    {"name": "Spellcasting", "description": "Spells."},
                    {"name": "Bardic Inspiration", "description": "Inspiration."},
                    {"name": "Jack of All Trades", "description": "Versatility."},
                ],
                "spellcasting": {"ability": "charisma", "progression": "full"},
            },
        )
    )

    assert rendered.index("## Level Progression") < rendered.index("## Class Features")
    assert rendered.index("### Hit Points") < rendered.index("### Spellcasting")
    assert rendered.index("### Spellcasting") < rendered.index("### Bardic Inspiration")
    assert rendered.index("### Bardic Inspiration") < rendered.index("### Jack of All Trades")


def test_bard_does_not_repeat_aggregate_description_or_supplementary_features():
    rendered = render_entity_markdown(
        entity(
            entity_type="class",
            payload={
                "name": "Bard",
                "hit_dice": 8,
                "description": (
                    "Starting Bard: Starting equipment and proficiencies.\n\n"
                    "Multiclass Bard: Multiclass prerequisites and proficiencies."
                ),
                "features": [
                    {"name": "Starting Bard", "level": 1, "description": "Starting equipment and proficiencies."},
                    {"name": "Multiclass Bard", "level": 1, "description": "Multiclass prerequisites and proficiencies."},
                    {"name": "Spellcasting", "level": 1, "description": "Spells."},
                    {"name": "Bardic Inspiration", "level": 1, "description": "Inspiration."},
                    {"name": "Additional Bard Spells", "level": 1, "description": "Optional spells."},
                ],
            },
        )
    )

    assert "## Description" not in rendered
    assert rendered.index("## Level Progression") < rendered.index("## Class Features")
    assert rendered.index("### Bardic Inspiration") < rendered.index("### Additional Bard Spells")
    assert rendered.index("### Starting Bard") > rendered.index("### Bardic Inspiration")
    assert "Starting Bard" not in rendered.split("## Level Progression", 1)[1].split("## Class Features", 1)[0]


def test_college_of_lore_uses_overview_and_features_without_derived_table():
    rendered = render_entity_markdown(
        entity(
            entity_type="subclass",
            payload={
                "name": "College of Lore",
                "class": "bard",
                "features": [
                    {"name": "Peerless Skill (College of Lore)", "level": 14, "description": "Skill."},
                    {"name": "Bard College: College of Lore", "level": 3, "description": "Overview."},
                    {"name": "Bonus Proficiencies (College of Lore)", "level": 3, "description": "Proficiencies."},
                    {"name": "Cutting Words (College of Lore)", "level": 3, "description": "Words."},
                    {"name": "Additional Magical Secrets (College of Lore)", "level": 6, "description": "Secrets."},
                ],
            },
        )
    )

    assert "## Level Progression" not in rendered
    assert rendered.index("## Overview") < rendered.index("## Features")
    assert rendered.index("### Bonus Proficiencies") < rendered.index("### Cutting Words")
    assert rendered.index("### Cutting Words") < rendered.index("### Additional Magical Secrets")
    assert rendered.index("### Additional Magical Secrets") < rendered.index("### Peerless Skill")


def test_eldritch_knight_keeps_spellcasting_feature_at_source_position():
    rendered = render_entity_markdown(
        entity(
            entity_type="subclass",
            payload={
                "name": "Eldritch Knight",
                "class": "fighter",
                "features": [
                    {"name": "Martial Archetype: Eldritch Knight", "level": 3, "description": "Overview."},
                    {"name": "Spellcasting (Eldritch Knight)", "level": 3, "description": "The Eldritch Knight Spellcasting table shows spell slots."},
                    {"name": "Weapon Bond (Eldritch Knight)", "level": 3, "description": "Bond."},
                ],
            },
        )
    )

    assert "Eldritch Knight Spellcasting table" in rendered
    assert rendered.index("### Spellcasting (Eldritch Knight)") < rendered.index("### Weapon Bond")


def test_structured_fields_use_reader_facing_units():
    rendered = render_entity_markdown(
        entity(
            entity_type="monster",
            payload={
                "name": "Owl",
                "senses": [{"type": "darkvision", "distance": 60, "distance_type": "feet"}],
                "movement": [{"movement_type": "walk", "speed": {"distance": 30, "unit": "feet"}}],
            },
        )
    )

    assert "- Darkvision: 60 ft" in rendered
    assert "- Walk: 30 ft" in rendered
    assert "distance_type" not in rendered


def test_structured_field_formatting_preserves_zero_and_missing_values():
    rendered = render_entity_markdown(
        entity(
            entity_type="monster",
            payload={
                "name": "Test Creature",
                "senses": [
                    {"type": "blindsight", "distance": 0, "distance_type": "feet"},
                    {"type": "tremorsense", "distance": None},
                ],
            },
        )
    )

    assert "- Blindsight: 0 ft" in rendered
    assert "- Tremorsense: Unavailable" in rendered


def test_structured_fields_normalize_lists_ranges_durations_costs_and_html():
    payload = {
        "name": "Wand",
        "cost": {"amount": 50, "currency": "gold"},
        "range": {"normal": 30, "long": 120},
        "duration": {"duration": "hour", "amount": 1},
        "damage_resistances": ["fire", "unknown_damage"],
        "proficiencies": [{"type": "martial"}],
    }
    entity_record = entity(entity_type="item", payload=payload)
    rendered = render_entity_markdown(entity_record)
    html = render_entity_html(entity_record)

    assert "- **Cost:** 50 gold" in rendered
    assert "- **Range:** 30 ft (long 120 ft)" in rendered
    assert "- **Duration:** 1 hour" in rendered
    assert "- Fire" in rendered
    assert "- Unknown Damage" in rendered
    assert "- Martial" in rendered
    assert "50 gold" in html
    assert "distance_type" not in rendered


def test_spell_metadata_omits_internal_amount_and_unit_labels():
    rendered = render_entity_markdown(
        entity(
            entity_type="spell",
            payload={
                "name": "Cure Wounds",
                "level": 1,
                "school": "evocation",
                "casting_time": {"amount": 1, "unit": "action"},
                "target": {
                    "targeting": "range",
                    "range": {"amount": 60, "unit": "feet"},
                },
                "duration": {"amount": 1, "duration": "hour"},
                "components": ["verbal"],
                "description": "Heal a creature.",
            },
        )
    )

    assert "**Casting Time:** 1 action" in rendered
    assert "**Target:** Range: 60 ft" in rendered
    assert "**Duration:** 1 hour" in rendered
    assert "Amount:" not in rendered
    assert "Unit:" not in rendered


def test_markdown_handles_nested_lists_long_text_and_unresolved_references():
    long_text = "A detailed description. " * 20
    rendered = render_entity_markdown(
        entity(
            payload={
                "name": "Pack",
                "description": long_text,
                "features": [{"name": "Utility", "entries": ["One", "Two"]}],
                "optional": None,
            },
            metadata={
                "reference_diagnostics": [{
                    "display_fallback": "Missing Spell",
                    "status": "missing",
                    "path": "features[0].spell",
                }]
            },
        )
    )

    assert long_text in rendered
    assert "### Features" in rendered
    assert "- One" in rendered
    assert "- Missing Spell (missing; features[0].spell)" in rendered