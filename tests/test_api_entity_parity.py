from api.adaptor import SRDAdaptor
from application.imports import EntityImportService


def import_api_payload(collection, source):
    record = SRDAdaptor().record(collection, source)
    preview = EntityImportService().preview_api([record])
    assert preview.can_commit is True
    return preview.records[0].payload


def test_api_shield_maps_top_level_armor_fields():
    payload = import_api_payload(
        "equipment",
        {
            "index": "shield",
            "name": "Shield",
            "armor_category": "Shield",
            "armor_class": {"base": 2, "dex_bonus": False},
            "cost": {"quantity": 10, "unit": "gp"},
            "desc": [],
            "stealth_disadvantage": False,
            "str_minimum": 0,
            "url": "/api/2014/equipment/shield",
            "weight": 6,
        },
    )

    assert payload == {
        "name": "Shield",
        "category": "armor",
        "armor": {
            "category": "shield",
            "type": "shield",
            "armor_class": 2,
            "stealth_disadvantage": False,
        },
        "weight": 6.0,
        "cost": {"amount": 10, "currency": "gp"},
        "source": {"href": "/api/2014/equipment/shield"},
    }


def test_api_armor_maps_dexterity_and_strength_constraints():
    payload = import_api_payload(
        "equipment",
        {
            "name": "Chain Mail",
            "armor_category": "Heavy",
            "armor_class": {"base": 16, "dex_bonus": False},
            "cost": {"quantity": 75, "unit": "gp"},
            "str_minimum": 13,
            "stealth_disadvantage": True,
            "url": "/api/2014/equipment/chain-mail",
            "weight": 55,
        },
    )

    assert payload["armor"] == {
        "category": "heavy",
        "type": "chain_mail",
        "armor_class": 16,
        "stealth_disadvantage": True,
        "strength_requirement": 13,
    }


def test_api_spell_classes_and_race_size_are_canonical_case():
    spell = import_api_payload(
        "spells",
        {
            "name": "Acid Arrow",
            "desc": ["A spell."],
            "higher_level": [],
            "level": 2,
            "school": {"name": "Evocation"},
            "classes": [{"name": "Wizard"}],
            "casting_time": "1 action",
            "range": "90 feet",
            "components": ["V", "S"],
            "duration": "Instantaneous",
            "ritual": False,
            "concentration": False,
            "url": "/api/2014/spells/acid-arrow",
        },
    )
    race = import_api_payload(
        "races",
        {
            "name": "Dragonborn",
            "size": "Medium",
            "speed": 30,
            "languages": [{"name": "Common"}],
            "ability_bonuses": [],
            "starting_proficiencies": [],
            "traits": [],
            "age": "They mature quickly.",
            "alignment": "They tend to extremes.",
            "url": "/api/2014/races/dragonborn",
        },
    )

    assert spell["classes"] == ["wizard"]
    assert race["size"] == "medium"


def test_api_class_choices_and_ability_score_levels_match_xml_semantics():
    source = {
        "name": "Wizard",
        "hit_die": 6,
        "proficiencies": [
            {"name": "Daggers"},
            {"name": "Saving Throw: INT"},
        ],
        "saving_throws": [{"name": "INT"}, {"name": "WIS"}],
        "proficiency_choices": [{
            "choose": 2,
            "from": {"options": [
                {"option_type": "string", "string": "Arcana"},
                {"option_type": "string", "string": "History"},
            ]},
        }],
        "class_levels": [
            {"level": 1, "ability_score_bonuses": 0},
            {"level": 4, "ability_score_bonuses": 1},
            {"level": 8, "ability_score_bonuses": 2},
        ],
    }

    payload = import_api_payload("classes", source)

    assert payload["skill_choices"]["from"] == ["arcana", "history"]
    assert payload["ability_score_increase"] == [4, 8]
