from pathlib import Path
import unittest

from schema_importer import SchemaImporter
from schemas.validator import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_ROOT = PROJECT_ROOT / "schemas"
DATA_ROOT = PROJECT_ROOT / "tests" / "data" / "schemas"


class TestSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_importer = SchemaImporter(
            SCHEMA_ROOT,
            DATA_ROOT,
        )

    def test_schemas(self):
        for schema_path, data_path in self.schema_importer.iter_tests():
            with self.subTest(
                schema=schema_path.name,
                data=data_path.name,
            ):
                self.assertTrue(
                    validate(schema_path, data_path, SCHEMA_ROOT)
                )


# class TestSchemas(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         cls.schema_root = SCHEMA_ROOT

#     def validate(self, schema, data):
#         return validate(self.schema_root / schema, data, self.schema_root)

#     def test_fireball(self):
#         fireball = {
#             "name": "Fireball",
#             "description": (
#                 "A bright streak flashes from your pointing finger to a point you "
#                 "choose within range and then blossoms with a low roar into an "
#                 "explosion of flame."
#             ),
#             "higher_level": (
#                 "When you cast this spell using a spell slot of 4th level or higher, "
#                 "the damage increases by 1d6 for each slot level above 3rd."
#             ),
#             "level": 3,
#             "casting_time": {
#                 "amount": 1,
#                 "unit": "round"
#             },
#             "target": {
#                 "target": "range",
#                 "range": {
#                     "amount": 150,
#                     "unit": "feet"
#                 },
#                 "zone": {
#                     "type": "sphere",
#                     "size": 20
#                 }
#             },
#             "components": [
#                 "verbal",
#                 "somatic",
#                 "material"
#             ],
#             "material": {
#                 "description": "A tiny ball of bat guano and sulfur",
#                 "consumed": False,
#                 "focus": False
#             },
#             "duration": "instantaneous",
#             "school": "evocation",
#             "saving_throw": "dexterity",
#             "damage_type": "Fire",
#             "tags": [
#                 "Wizard",
#                 "Sorcerer"
#             ],
#             "source": {
#                 "text": "PHB p241"
#             }
#         }

#         assert self.validate("entities/Spell.schema.json", fireball)

#     def test_mage_hand(self):
#         mage_hand = {
#             "name": "Mage Hand",
#             "description": (
#                 "A spectral, floating hand appears at a point you choose within "
#                 "range. The hand lasts for the duration or until you dismiss it "
#                 "as an action."
#             ),
#             "level": 0,
#             "casting_time": {
#                 "amount": 1,
#                 "unit": "round"
#             },
#             "target": {
#                 "target": "range",
#                 "range": {
#                     "amount": 30,
#                     "unit": "feet"
#                 }
#             },
#             "components": [
#                 "verbal",
#                 "somatic"
#             ],
#             "duration": "minute",
#             "school": "conjuration",
#             "tags": [
#                 "Bard",
#                 "Sorcerer",
#                 "Warlock",
#                 "Wizard"
#             ],
#             "source": {
#                 "text": "PHB p256"
#             }
#         }

#         assert self.validate("entities/Spell.schema.json", mage_hand)

#     def test_cure_wounds(self):
#         cure_wounds = {
#             "name": "Cure Wounds",
#             "description": (
#                 "A creature you touch regains a number of hit points equal to "
#                 "1d8 + your spellcasting ability modifier."
#             ),
#             "higher_level": (
#                 "When you cast this spell using a spell slot of 2nd level or higher, "
#                 "the healing increases by 1d8 for each slot level above 1st."
#             ),
#             "level": 1,
#             "casting_time": {
#                 "amount": 1,
#                 "unit": "round"
#             },
#             "target": {
#                 "target": "touch"
#             },
#             "components": [
#                 "verbal",
#                 "somatic"
#             ],
#             "duration": "instantaneous",
#             "school": "evocation",
#             "tags": [
#                 "Bard",
#                 "Cleric",
#                 "Druid",
#                 "Paladin",
#                 "Ranger"
#             ],
#             "source": {
#                 "text": "PHB p230"
#             }
#         }

#         assert self.validate("entities/Spell.schema.json", cure_wounds)

#     def test_longsword(self):
#         longsword = {
#             "name": "Longsword",
#             "description": "A martial melee weapon.",
#             "source": {
#                 "text": "PHB p149"
#             }
#         }

#         assert self.validate("entities/Item.schema.json", longsword)

#     def test_dagger(self):
#         dagger = {
#             "name": "Dagger",
#             "description": (
#                 "A simple melee weapon that can be used with finesse or thrown."
#             ),
#             "source": {
#                 "text": "PHB p149"
#             }
#         }

#         assert self.validate("entities/Item.schema.json", dagger)

#     def test_goblin(self):
#         goblin = {
#             "name": "Goblin",
#             "alignment": {
#                 "law_chaos": "neutral",
#                 "good_evil": "evil"
#             },
#             "speed": {
#                 "walk": 30
#             },
#             "hit_points": {
#                 "maximum": 7,
#                 "current": 7,
#                 "temporary": 0
#             },
#             "armor_class": {
#                 "value": 15,
#                 "description": "Leather armor and shield"
#             },
#             "ability_scores": {
#                 "strength": 8,
#                 "dexterity": 14,
#                 "constitution": 10,
#                 "intelligence": 10,
#                 "wisdom": 8,
#                 "charisma": 8
#             },
#             "languages": [
#                 "Common",
#                 "Goblin"
#             ],
#             "source": {
#                 "text": "MM p166"
#             }
#         }

#         assert self.validate("entities/Creature.schema.json", goblin)

#     def test_wolf(self):
#         wolf = {
#             "name": "Wolf",
#             "alignment": {
#                 "unaligned": "unaligned"
#             },
#             "speed": {
#                 "walk": 40
#             },
#             "hit_points": {
#                 "maximum": 11,
#                 "current": 11,
#                 "temporary": 0
#             },
#             "armor_class": {
#                 "value": 13,
#                 "description": "Natural armor"
#             },
#             "ability_scores": {
#                 "strength": 12,
#                 "dexterity": 15,
#                 "constitution": 12,
#                 "intelligence": 3,
#                 "wisdom": 12,
#                 "charisma": 6
#             },
#             "source": {
#                 "text": "MM p341"
#             }
#         }

#         assert self.validate("entities/Creature.schema.json", wolf)

#     def test_ability_scores(self):
#         ability_scores = {
#             "strength": 15,
#             "dexterity": 14,
#             "constitution": 13,
#             "intelligence": 12,
#             "wisdom": 10,
#             "charisma": 8
#         }

#         assert self.validate("components/ability_scores.schema.json", ability_scores)

#     def test_hit_points(self):
#         hit_points = {
#             "maximum": 24,
#             "current": 18,
#             "temporary": 5
#         }

#         assert self.validate("components/hit_points.schema.json", hit_points)

#     def test_material_component(self):
#         material_component = {
#             "description": "A diamond worth at least 300 gp",
#             "cost": 300,
#             "consumed": True,
#             "focus": False
#         }

#         assert self.validate("components/material_component.schema.json", material_component)

#     def test_source(self):
#         source = {
#             "text": "PHB p241",
#             "note": "Classic 5e spell.",
#             "href": "https://www.dndbeyond.com"
#         }

#         assert self.validate("values/source.schema.json", source)
        
#     def test_adult_blue_dracolich(self):
#         dracolich = {
#             "name": "Adult Blue Dracolich",
#             "size": "huge",
#             "creature_type": "undead",
#             "alignment": {
#                 "order": "lawful",
#                 "morality": "evil"
#             },
#             "ability_scores": {
#                 "strength": 25,
#                 "dexterity": 10,
#                 "constitution": 23,
#                 "intelligence": 16,
#                 "wisdom": 15,
#                 "charisma": 19
#             },
#             "hit_points": {
#                 "maximum": 225,
#                 "current": 225,
#                 "temporary": 0
#             },
#             "hit_dice": {
#                 "count": 18,
#                 "dice": "d12"
#             },
#             "armor_class": {
#                 "value": 19,
#                 "description": "Natural armor"
#             },
#             "movement": [
#                 {
#                     "movement_type": "walk",
#                     "speed": {
#                         "amount": 40,
#                         "distance_type": "feet"
#                     }
#                 },
#                 {
#                     "movement_type": "burrow",
#                     "speed": {
#                         "amount": 30,
#                         "distance_type": "feet"
#                     }
#                 },
#                 {
#                     "movement_type": "fly",
#                     "speed": {
#                         "amount": 80,
#                         "distance_type": "feet"
#                     }
#                 }
#             ],
#             "saving_throws": {
#                 "dexterity": 5,
#                 "constitution": 11,
#                 "wisdom": 7,
#                 "charisma": 9
#             },
#             "skills": {
#                 "perception": 12,
#                 "stealth": 5
#             },
#             "senses": [
#                 {
#                     "type": "blindsight",
#                     "distance": 60
#                 },
#                 {
#                     "type": "darkvision",
#                     "distance": 120
#                 }
#             ],
#             "passive_perception": 22,
#             "languages": [
#                 "Common",
#                 "Draconic"
#             ],
#             "condition_immunities": [
#                 "charmed",
#                 "exhaustion",
#                 "frightened",
#                 "paralyzed",
#                 "poisoned"
#             ],
#             "damage_immunities": [
#                 "lightning",
#                 "poison"
#             ],
#             "damage_resistances": [
#                 "necrotic"
#             ],
#             "damage_vulnerabilities": [],
#             "features": [
#                 {
#                     "name": "Legendary Resistance (3/Day)",
#                     "description": "If the dracolich fails a saving throw, it can choose to succeed instead."
#                 },
#                 {
#                     "name": "Magic Resistance",
#                     "description": "The dracolich has advantage on saving throws against spells and other magical effects."
#                 }
#             ],
#             "actions": [
#                 {
#                     "name": "Multiattack",
#                     "description": "The dracolich can use its Frightful Presence. It then makes three attacks: one with its bite and two with its claws."
#                 },
#                 {
#                     "name": "Bite",
#                     "description": "Melee Weapon Attack: +12 to hit, reach 10 ft., one target. Hit: 18 (2d10+7) piercing damage plus 5 (1d10) lightning damage.",
#                     "effects": [
#                         {
#                             "attack_hit": {
#                                 "type": "melee",
#                                 "bonus": 12,
#                                 "effects": [
#                                     {
#                                         "damage": {
#                                             "type": "piercing",
#                                             "roll": "2d10",
#                                             "modifier": 7
#                                         }
#                                     },
#                                     {
#                                         "damage": {
#                                             "type": "lightning",
#                                             "roll": "1d10",
#                                             "modifier": 0
#                                         }
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "name": "Claw",
#                     "description": "Melee Weapon Attack: +12 to hit, reach 5 ft., one target. Hit: 14 (2d6+7) slashing damage.",
#                     "effects": [
#                         {
#                             "attack_hit": {
#                                 "type": "melee",
#                                 "bonus": 12,
#                                 "effects": [
#                                     {
#                                         "damage": {
#                                             "type": "slashing",
#                                             "roll": "2d6",
#                                             "modifier": 7
#                                         }
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "name": "Tail",
#                     "description": "Melee Weapon Attack: +12 to hit, reach 15 ft., one target. Hit: 16 (2d8+7) bludgeoning damage.",
#                     "effects": [
#                         {
#                             "attack_hit": {
#                                 "type": "melee",
#                                 "bonus": 12,
#                                 "effects": [
#                                     {
#                                         "damage": {
#                                             "type": "bludgeoning",
#                                             "roll": "2d8",
#                                             "modifier": 7
#                                         }
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "name": "Frightful Presence",
#                     "description": "Each creature of the dracolich's choice that is within 120 feet of the dracolich and aware of it must succeed on a DC 18 Wisdom saving throw or become frightened for 1 minute. A creature can repeat the saving throw at the end of each of its turns, ending the effect on itself on a success. If a creature's saving throw is successful or the effect ends for it, the creature is immune to the dracolich's Frightful Presence for the next 24 hours.",
#                     "effects": [
#                         {
#                             "attack_save": {
#                                 "ability": "wisdom",
#                                 "dc": 18,
#                                 "failure": [
#                                     {
#                                         "condition": "frightened"
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 },
#                 {
#                     "name": "Lightning Breath (Recharge 5-6)",
#                     "description": "The dracolich exhales lightning in a 90-foot line that is 5 feet wide. Each creature in that line must make a DC 20 Dexterity saving throw, taking 66 (12d10) lightning damage on a failed save, or half as much damage on a successful one.",
#                     "effects": [
#                         {
#                             "attack_save": {
#                                 "ability": "dexterity",
#                                 "dc": 20,
#                                 "success": [
#                                     {
#                                         "damage": {
#                                             "type": "lightning",
#                                             "roll": "12d10"
#                                         }
#                                     }
#                                 ],
#                                 "failure": [
#                                     {
#                                         "damage": {
#                                             "type": "lightning",
#                                             "roll": "12d10"
#                                         }
#                                     }
#                                 ]
#                             }
#                         }
#                     ]
#                 }
#             ],
#             "legendary_actions": [
#                 {
#                     "name": "Legendary Actions (3/Turn)",
#                     "description": "The dracolich can take 3 legendary actions, choosing from the options below. Only one legendary action option can be used at a time, and only at the end of another creature's turn. The dracolich regains spent legendary actions at the start of its turn."
#                 },
#                 {
#                     "name": "Detect",
#                     "description": "The dracolich makes a Wisdom (Perception) check."
#                 },
#                 {
#                     "name": "Tail Attack",
#                     "description": "The dracolich makes a tail attack."
#                 },
#                 {
#                     "name": "Wing Attack (Costs 2 Actions)",
#                     "description": "The dracolich beats its tattered wings. Each creature within 10 ft. of the dracolich must succeed on a DC 21 Dexterity saving throw or take 14 (2d6+7) bludgeoning damage and be knocked prone. After beating its wings this way, the dracolich can fly up to half its flying speed."
#                 }
#             ],
#             "challenge_rating": 17,
#             "environments": [
#                 "desert"
#             ],
#             "source": {
#                 "text": "Monster Manual p. 84"
#             }
#         }

#         self.assertTrue(
#             self.validate("entities/Creature.schema.json", dracolich)
#         )


if __name__ == "__main__":
    unittest.main()
