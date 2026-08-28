import unittest
import json
import os
from schemas.validator import validate_entity

class TestDndEntities(unittest.TestCase):

    def test_spell_fireball(self):
        # Fireball spell example
        fireball = {
            "name": "Fireball",
            "description": "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame.",
            "level": 3,
            "casting_time": {"casting_time": "1 action"},
            "components": ["verbal", "somatic", "material"],
            "material": {"description": "a tiny ball of bat guano and sulfur"},
            "duration": {"duration": "instantaneous"},
            "source": {"text": "PHB p241"}
        }
        errors = validate_entity(fireball, "entities/Spell.schema.json")
        self.assertEqual(len(errors), 0, f"Fireball validation failed: {errors}")

    def test_item_longsword(self):
        longsword = {
            "name": "Longsword",
            "weight": 3,
            "cost": 15,
            "magic": False,
            "source": {"text": "PHB p149"}
        }
        errors = validate_entity(longsword, "entities/Item.schema.json")
        self.assertEqual(len(errors), 0, f"Longsword validation failed: {errors}")

if __name__ == '__main__':
    unittest.main()
