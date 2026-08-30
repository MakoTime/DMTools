from enum import Enum


class Size(str, Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"


class CreatureType(str, Enum):
    ABERRATION = "aberration"
    BEAST = "beast"
    CELESTIAL = "celestial"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    FEY = "fey"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"
    UNDEAD = "undead"


class AbilityScore(str, Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"


class Dice(int, Enum):
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D20 = 20
    D100 = 100


class MovementType(str, Enum):
    WALK = "walk"
    FLY = "fly"
    SWIM = "swim"
    CLIMB = "climb"
    BURROW = "burrow"


class DistanceType(str, Enum):
    FEET = "feet"
    MILES = "miles"


class SenseType(str, Enum):
    BLINDSIGHT = "blindsight"
    DARKVISION = "darkvision"
    DEVIL_SIGHT = "devil_sight"
    TREMORSENSE = "tremorsense"
    TRUESIGHT = "truesight"


class Condition(str, Enum):
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    EXHAUSTION = "exhaustion"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


class DamageType(str, Enum):
    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"


class Skill(str, Enum):
    ACROBATICS = "acrobatics"
    ANIMAL_HANDLING = "animal_handling"
    ARCANA = "arcana"
    ATHLETICS = "athletics"
    DECEPTION = "deception"
    HISTORY = "history"
    INSIGHT = "insight"
    INTIMIDATION = "intimidation"
    INVESTIGATION = "investigation"
    MEDICINE = "medicine"
    NATURE = "nature"
    PERCEPTION = "perception"
    PERFORMANCE = "performance"
    PERSUASION = "persuasion"
    RELIGION = "religion"
    SLEIGHT_OF_HAND = "sleight_of_hand"
    STEALTH = "stealth"
    SURVIVAL = "survival"


class ActionType(str, Enum):
    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    FREE_ACTION = "free_action"
    LEGENDARY_ACTION = "legendary_action"
    LAIR_ACTION = "lair_action"
    MYTHIC_ACTION = "mythic_action"


class AttackType(str, Enum):
    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MELEE_SPELL = "melee_spell"
    RANGED_SPELL = "ranged_spell"


class TargetType(str, Enum):
    CREATURE = "creature"
    ALLY = "ally"
    ENEMY = "enemy"
    OBJECT = "object"
    SELF = "self"


class TargetZoneType(str, Enum):
    SINGLE = "single"
    LINE = "line"
    CONE = "cone"
    CUBE = "cube"
    CYLINDER = "cylinder"
    SPHERE = "sphere"