from pathlib import Path

import pytest

from api.adaptor import SRDAdaptor
from application.imports import ENTITY_REGISTRY
from parsers.spell_adaptor import SpellAdaptor
from parsers.spell_parser import parse_spell
from parsers.xml_parser import parse_xml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


API_SAMPLES = {
    "monster": {
        "name": "Goblin",
        "challenge_rating": 0.25,
        "size": "Small",
        "type": "humanoid",
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
        "hit_points": 7,
        "hit_dice": "2d6",
        "armor_class": [{"value": 15, "desc": "natural armor"}],
        "speed": {"walk": "30 ft."},
        "proficiencies": [
            {"value": 4, "proficiency": {"name": "Skill: Perception"}},
            {"value": 2, "proficiency": {"name": "Saving Throw: DEX"}},
        ],
        "senses": {"darkvision": "60 ft.", "passive_perception": 14},
        "languages": "Common, Goblin",
        "damage_resistances": ["fire"],
        "special_abilities": [{"name": "Keen Sight", "desc": "The goblin sees well."}],
        "actions": [{"name": "Scimitar", "desc": "The goblin attacks with its scimitar."}],
        "legendary_actions": [{"name": "Quick Step", "desc": "The goblin moves."}],
        "proficiency_bonus": 2,
        "image": "https://example.test/goblin.png",
    },
    "class": {"name": "Wizard", "hit_die": 6},
    "spell": {
        "name": "Fireball",
        "level": 3,
        "school": {"name": "Evocation"},
        "casting_time": "1 action",
        "range": "150 feet",
        "components": ["V", "S", "M"],
        "material": "A small pinch of bat guano and sulfur.",
        "duration": "Instantaneous",
        "desc": ["A bright streak flashes toward a point."],
        "classes": [{"name": "Wizard"}],
        "ritual": False,
        "concentration": False,
    },
    "race": {"name": "Elf", "size": "Medium", "languages": [{"name": "Common"}]},
    "background": {"name": "Acolyte", "desc": ["You have spent your life in service."]},
    "feat": {"name": "Alert", "desc": ["Always on the lookout for danger."]},
    "item": {
        "name": "Dagger",
        "equipment_category": {"name": "Weapon"},
        "weight": 1,
        "desc": ["A small blade."],
    },
    "subclass": {
        "name": "School of Evocation",
        "class": {"name": "Wizard"},
        "desc": ["You focus on evocation magic."],
    },
}

COLLECTIONS = {
    "monster": "monsters",
    "class": "classes",
    "spell": "spells",
    "race": "races",
    "background": "backgrounds",
    "feat": "feats",
    "item": "equipment",
    "subclass": "subclasses",
}


@pytest.mark.parametrize("entity_type", API_SAMPLES)
def test_srd_adaptor_payload_matches_project_schema(entity_type):
    collection = COLLECTIONS[entity_type]
    payload = SRDAdaptor().adapt(collection, API_SAMPLES[entity_type])
    normalized = ENTITY_REGISTRY[entity_type].validate_payload(payload)
    assert normalized["name"] == API_SAMPLES[entity_type]["name"]


def test_srd_class_preserves_schema_supported_spellcasting_details():
    source = {
        "name": "Wizard",
        "hit_die": 6,
        "spellcasting": {
            "level": 1,
            "spellcasting_ability": {"name": "INT"},
        },
        "class_levels": [
            {"level": 1, "features": [{"name": "Spellcasting", "desc": [
                "You can cast a spell as a ritual if it has the ritual tag."
            ]}], "spellcasting": {}},
        ],
    }

    payload = SRDAdaptor().adapt("classes", source)
    normalized = ENTITY_REGISTRY["class"].validate_payload(payload)
    assert normalized["spellcasting"] == {
        "ability": "intelligence",
        "progression": "full",
        "ritual": True,
        "prepared": False,
    }


def test_srd_class_excludes_api_subclass_placeholders_and_normalizes_spellcasting_name():
    payload = SRDAdaptor().adapt("classes", {
        "name": "Wizard",
        "hit_die": 6,
        "class_levels": [{
            "level": 1,
            "features": [{
                "name": "Spellcasting: Wizard",
                "desc": ["You cast spells."],
            }],
        }, {
            "level": 6,
            "features": [{
                "name": "Arcane Tradition feature",
                "desc": ["Subclass feature placeholder."],
            }],
        }],
    })

    assert payload["features"] == [{
        "name": "Spellcasting",
        "description": "You cast spells.",
        "level": 1,
    }]


def test_srd_class_spell_endpoint_is_not_treated_as_spell_names():
    source = {
        "name": "Bard",
        "hit_die": 8,
        "spellcasting": {"level": 1, "spellcasting_ability": {"name": "CHA"}},
        "spells": "/api/2014/classes/bard/spells",
    }

    payload = SRDAdaptor().adapt("classes", source)
    normalized = ENTITY_REGISTRY["class"].validate_payload(payload)

    assert "spells" not in normalized["spellcasting"]


def test_srd_race_preserves_reader_facing_details():
    source = {
        "name": "Elf",
        "size": "Medium",
        "speed": {"walk": "30 ft.", "hover": False},
        "ability_bonuses": [{"ability_score": {"name": "DEX"}, "bonus": 2}],
        "languages": [{"name": "Common"}, {"name": "Elvish"}],
        "age": "Elves mature at the same rate as humans.",
        "alignment": "Elves tend toward chaotic good.",
        "traits": [{"name": "Keen Senses", "desc": ["You have proficiency in Perception."]}],
        "starting_proficiencies": [],
    }

    normalized = ENTITY_REGISTRY["race"].validate_payload(
        SRDAdaptor().adapt("races", source)
    )

    assert normalized["movement"] == [{
        "movement_type": "walk",
        "speed": {"distance": 30, "unit": "feet"},
        "hover": False,
    }]
    assert {feature["name"] for feature in normalized["features"]} == {
        "Keen Senses", "Age", "Alignment",
    }


def test_srd_race_normalizes_scalar_speed_and_api_trait_senses():
    payload = SRDAdaptor().adapt("races", {
        "name": "Elf",
        "size": "Medium",
        "speed": 30,
        "traits": [{
            "name": "Darkvision",
            "desc": ["Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light."],
        }],
    })

    assert payload["movement"] == [{
        "movement_type": "walk",
        "speed": {"distance": 30, "unit": "feet"},
    }]
    assert payload["senses"] == [{
        "type": "darkvision",
        "distance": 60,
        "distance_type": "feet",
    }]


def test_srd_spell_matches_xml_spell_normalization():
    xml_path = PROJECT_ROOT / "tests" / "data" / "xml_files" / "spells" / "prismatic_spray.xml"
    xml_payload = SpellAdaptor().adapt(parse_spell(parse_xml(xml_path)))
    api_payload = SRDAdaptor().adapt("spells", API_SAMPLES["spell"])

    assert api_payload["casting_time"] == {"amount": 1, "unit": "action"}
    assert api_payload["components"] == ["verbal", "somatic", "material"]
    assert api_payload["material"] == {"description": "A small pinch of bat guano and sulfur."}
    assert api_payload["duration"] == {"duration": "instantaneous"}
    assert api_payload["school"] == "evocation"
    assert set(api_payload) >= {"name", "level", "description", "casting_time", "components", "duration"}
    assert set(xml_payload) >= {"name", "level", "description", "casting_time", "components", "duration"}


def test_srd_spell_preserves_material_cost_and_consumption():
    source = dict(API_SAMPLES["spell"])
    source["components"] = ["V", "S", "M"]
    source["material"] = "A pearl worth at least 100gp, which is consumed."

    payload = SRDAdaptor().adapt("spells", source)

    assert payload["material"] == {
        "description": "A pearl worth at least 100gp, which is consumed.",
        "cost": 100.0,
        "consumed": True,
    }


def test_srd_monster_preserves_combat_and_sensory_data():
    payload = SRDAdaptor().adapt("monsters", API_SAMPLES["monster"])

    assert payload["ability_scores"] == {
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
    }
    assert payload["armor_class"] == {"value": 15, "description": "natural armor"}
    assert payload["movement"] == [
        {"movement_type": "walk", "speed": {"distance": 30, "unit": "feet"}}
    ]
    assert payload["senses"] == [
        {"type": "darkvision", "distance": 60, "distance_type": "feet"}
    ]
    assert payload["saving_throws"] == {"dexterity": 2}
    assert payload["skills"] == {"perception": 4}
    assert len(payload["features"]) == 1
    assert len(payload["actions"]) == 1
    assert len(payload["legendary_actions"]) == 1
    assert payload["proficiency_bonus"] == 2
    assert payload["image"] == {
        "uri": "https://example.test/goblin.png",
        "alt": "Goblin",
    }


def test_srd_monster_deduplicates_condition_immunities():
    source = dict(API_SAMPLES["monster"])
    source["condition_immunities"] = [
        {"name": "Blinded"},
        {"name": "Charmed"},
        {"name": "blinded"},
    ]

    payload = SRDAdaptor().adapt("monsters", source)

    assert payload["condition_immunities"] == ["blinded", "charmed"]


def test_srd_adaptors_preserve_non_monster_detail_fields():
    class_payload = SRDAdaptor().adapt("classes", {
        "name": "Wizard",
        "hit_die": 6,
        "saving_throws": [{"name": "INT"}, {"name": "WIS"}],
        "proficiencies": [
            {"name": "Daggers"},
            {"name": "Arcana"},
        ],
        "spellcasting": {"level": 1, "spellcasting_ability": {"name": "INT"}},
        "multi_classing": {
            "prerequisites": [{
                "ability_score": {"name": "INT"},
                "minimum_score": 13,
            }],
        },
        "class_levels": [
            {
                "level": 1,
                "ability_score_bonuses": 0,
                "features": [{
                    "name": "Arcane Recovery",
                    "level": 1,
                    "desc": ["Recover spell slots after a short rest."],
                }],
            },
            {"level": 4, "ability_score_bonuses": 1, "features": []},
        ],
    })
    assert class_payload["saving_throws"] == ["intelligence", "wisdom"]
    assert class_payload["spellcasting"] == {"ability": "intelligence", "progression": "full"}
    assert class_payload["features"] == [{
        "name": "Arcane Recovery",
        "description": "Recover spell slots after a short rest.",
        "level": 1,
    }]
    assert class_payload["required_stats"] == ["intelligence"]
    assert class_payload["ability_score_increase"] == [4]

    race_payload = SRDAdaptor().adapt("races", {
        "name": "Elf",
        "size": "Medium",
        "ability_bonuses": [{"ability_score": {"name": "DEX"}, "bonus": 2}],
        "languages": [{"name": "Common"}],
    })
    assert race_payload["ability_score_increases"] == [{"ability": "dexterity", "amount": 2}]

    item_payload = SRDAdaptor().adapt("equipment", {
        "name": "Dagger",
        "equipment_category": {"name": "Weapon"},
        "weapon_category": "Simple",
        "weapon_range": "Melee",
        "damage": {"damage_dice": "1d4", "damage_type": {"name": "Piercing"}},
        "range": {"normal": 5},
        "cost": {"quantity": 2, "unit": "gp"},
        "weight": 1,
    })
    assert item_payload["cost"] == {"amount": 2, "currency": "gp"}
    assert item_payload["weapon"]["effects"][0]["damage"]["type"] == "piercing"

    subclass_payload = SRDAdaptor().adapt("subclasses", {
        "name": "Evocation",
        "class": {"name": "Wizard"},
        "desc": ["A school of elemental magic."],
        "subclass_levels": [{
            "level": 2,
            "features": [{
                "name": "Sculpt Spells",
                "level": 2,
                "desc": ["Protect allies from your evocations."],
            }],
        }],
    })
    assert subclass_payload["features"] == [{
        "name": "Sculpt Spells",
        "description": "Protect allies from your evocations.",
        "level": 2,
    }]


def test_srd_record_preserves_complete_api_source_metadata():
    source = {
        "index": "wizard",
        "name": "Wizard",
        "hit_die": 6,
        "starting_equipment": [{"equipment": {"name": "Spellbook"}, "quantity": 1}],
        "class_levels": [{"level": 1, "features": [{"name": "Spellcasting"}]}],
        "url": "/api/2014/classes/wizard",
    }

    record = SRDAdaptor().record("classes", source)

    assert record["source_metadata"]["api_url"] == source["url"]
    assert record["source_metadata"]["api_source"] == source
