from api.adaptor import SRDAdaptor
from application.imports import EntityImportService
from models.item import Item


def test_api_item_uses_canonical_item_shape():
    source = {
        "name": "Handaxe",
        "equipment_category": {"name": "Weapon"},
        "weight": 2,
        "cost": {"quantity": 5, "unit": "gp"},
        "weapon_category": "Simple",
        "weapon_range": "Melee",
        "damage": {
            "damage_dice": "1d6",
            "damage_type": {"name": "Slashing"},
        },
        "properties": [
            {"name": "Light"},
            {"name": "Thrown"},
        ],
        "range": {"normal": 5},
        "throw_range": {"normal": 20, "long": 60},
        "url": "/api/2014/equipment/handaxe",
    }

    record = SRDAdaptor().record("equipment", source)
    preview = EntityImportService().preview_api([record])
    assert preview.can_commit is True
    payload = preview.records[0].payload

    assert payload == Item.model_validate(payload).model_dump(
        mode="json", exclude_none=True
    )
    assert payload == {
        "name": "Handaxe",
        "category": "weapon",
        "weapon": {
            "type": "handaxe",
            "effects": [{
                "damage": {
                    "type": "slashing",
                    "roll": {"count": 1, "dice": 6},
                    "modifier": 0,
                },
            }],
            "properties": ["light", "thrown"],
            "range": {"normal": 20, "long": 60},
        },
        "weight": 2.0,
        "cost": {"amount": 5, "currency": "gp"},
        "source": {"href": "/api/2014/equipment/handaxe"},
    }
