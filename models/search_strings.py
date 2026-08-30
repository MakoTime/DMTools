import re

# ---------------------------------------------------------------------------
# Action structure
# ---------------------------------------------------------------------------

NUMBERED_ENTRY = re.compile(
    r"(?m)^\s*(?P<number>\d+)\.\s*"
    r"(?P<name>[^.]+)\.\s*"
    r"(?P<description>.*?)(?=^\s*\d+\.\s|"
    r"^\s*[A-Z][^:\n]{1,50}:\s*$|\Z)",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Attack
# ---------------------------------------------------------------------------

MELEE_WEAPON_ATTACK = re.compile(
    r"Melee Weapon Attack:\s*"
    r"(?P<bonus>[+-]?\d+)\s+to hit,\s*"
    r"reach\s+(?P<reach>\d+)\s*ft\.,\s*"
    r"(?P<target>[^.]+)\.\s*"
    r"Hit:\s*"
    r"(?P<hit>.*)",
    re.IGNORECASE | re.DOTALL,
)

RANGED_WEAPON_ATTACK = re.compile(
    r"Ranged Weapon Attack:\s*"
    r"(?P<bonus>[+-]?\d+)\s+to hit,\s*"
    r"range\s+(?P<range>\d+)(?:/\s*(?P<long_range>\d+))?\s*ft\.,\s*"
    r"(?P<target>[^.]+)\.\s*"
    r"Hit:\s*"
    r"(?P<hit>.*)",
    re.IGNORECASE | re.DOTALL,
)

MELEE_OR_RANGED_ATTACK = re.compile(
    r"(?P<attack_type>Melee|Ranged)\s+"
    r"(?P<weapon_type>Weapon|Spell)\s+Attack:\s*"
    r"(?P<bonus>[+-]?\d+)\s+to hit,\s*"
    r"(?P<range_type>reach|range)\s+"
    r"(?P<range>\d+)"
    r"(?:/\s*(?P<long_range>\d+))?\s*ft\.,\s*"
    r"(?P<target>[^.]+)\.\s*"
    r"Hit:\s*"
    r"(?P<hit>.*)",
    re.IGNORECASE | re.DOTALL,
)

MELEE_SPELL_ATTACK = re.compile(
    r"^Melee Spell Attack:\s*"
    r"(?P<bonus>[+-]\d+)\s+to hit,\s*"
    r"reach\s+(?P<reach>\d+)\s*ft\.,\s*"
    r"(?P<target>.+?)\.\s*"
    r"Hit:\s*(?P<hit>.+)$",
    re.IGNORECASE | re.DOTALL,
)


RANGED_SPELL_ATTACK = re.compile(
    r"^Ranged Spell Attack:\s*"
    r"(?P<bonus>[+-]\d+)\s+to hit,\s*"
    r"range\s+(?P<range>\d+)"
    r"(?:/(?P<long_range>\d+))?\s*ft\.,\s*"
    r"(?P<target>.+?)\.\s*"
    r"Hit:\s*(?P<hit>.+)$",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# Saving throws
# ---------------------------------------------------------------------------

SAVING_THROW = re.compile(
    r"(?:must|needs to)\s+"
    r"(?:succeed on|make)\s+a\s+"
    r"DC\s+(?P<dc>\d+)\s+"
    r"(?P<ability>Strength|Dexterity|Constitution|"
    r"Intelligence|Wisdom|Charisma)\s+"
    r"saving throw",
    re.IGNORECASE,
)

SAVING_THROW_ANY_DC = re.compile(
    r"DC\s+(?P<dc>\d+)\s+"
    r"(?P<ability>Strength|Dexterity|Constitution|"
    r"Intelligence|Wisdom|Charisma)\s+"
    r"saving throw",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Damage
# ---------------------------------------------------------------------------

DAMAGE = re.compile(
    r"(?P<average>\d+)\s*"
    r"\((?P<count>\d+)?d(?P<dice>\d+)"
    r"(?P<modifier>[+-]\d+)?\)\s*"
    r"(?P<type>acid|bludgeoning|cold|fire|force|lightning|"
    r"necrotic|piercing|poison|psychic|radiant|slashing|thunder)"
    r"\s+damage",
    re.IGNORECASE,
)

DAMAGE_ROLL = re.compile(
    r"(?P<count>\d+)?d(?P<dice>\d+)"
    r"(?P<modifier>[+-]\d+)?\s*"
    r"(?P<type>acid|bludgeoning|cold|fire|force|lightning|"
    r"necrotic|piercing|poison|psychic|radiant|slashing|thunder)"
    r"\s+damage",
    re.IGNORECASE,
)

EFFECT_TABLE = re.compile(
    r"(?ms)"
    r"^\s*(?P<number>\d+)\.\s*"
    r"(?P<name>[^.]+)\.\s*"
    r"(?P<description>.*?)(?="
    r"^\s*\d+\.\s*"
    r"|\Z)"
)

# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------

CONDITION = re.compile(
    r"\b(?P<condition>"
    r"blinded|charmed|deafened|exhaustion|frightened|grappled|"
    r"incapacitated|invisible|paralyzed|petrified|poisoned|prone|"
    r"restrained|stunned|unconscious"
    r")\b",
    re.IGNORECASE,
)

BECOMES_CONDITION = re.compile(
    r"\b(?:becomes?|is|be|fall|falls)\s+"
    r"(?P<condition>"
    r"blinded|charmed|deafened|exhausted|frightened|grappled|"
    r"incapacitated|invisible|paralyzed|petrified|poisoned|prone|"
    r"restrained|stunned|unconscious"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Healing / Hit Points
# ---------------------------------------------------------------------------

HEALING = re.compile(
    r"(?:regains?|recovers?|restores?)\s+"
    r"(?P<amount>.+?)\s+hit points",
    re.IGNORECASE,
)

HIT_POINT_LOSS = re.compile(
    r"(?:loses?|reduces?)\s+"
    r"(?P<amount>.+?)\s+hit points",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------

DURATION = re.compile(
    r"\bfor\s+"
    r"(?P<amount>\d+)\s+"
    r"(?P<unit>round|rounds|minute|minutes|hour|hours|"
    r"day|days|turn|turns)\b",
    re.IGNORECASE,
)

UNTIL = re.compile(
    r"\buntil\s+"
    r"(?P<condition>[^.]+)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Range / Reach
# ---------------------------------------------------------------------------

REACH = re.compile(
    r"\breach\s+(?P<distance>\d+)\s*ft\.",
    re.IGNORECASE,
)

RANGE = re.compile(
    r"\bwithin\s+(?P<distance>\d+)\s*ft\.",
    re.IGNORECASE,
)

RANGE_WITH_UNIT = re.compile(
    r"\b(?P<distance>\d+)\s+"
    r"(?P<unit>ft\.|feet|mile|miles)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

ONE_TARGET = re.compile(
    r"\bone target\b",
    re.IGNORECASE,
)

TARGET_COUNT = re.compile(
    r"\b(?P<minimum>\d+)\s+"
    r"(?:to\s+(?P<maximum>\d+)\s+)?"
    r"targets?\b",
    re.IGNORECASE,
)

TARGET_CREATURE = re.compile(
    r"\b(?:the\s+)?target(?:ed)?\s+creature\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Attack result
# ---------------------------------------------------------------------------

HIT_RESULT = re.compile(
    r"\bHit:\s*(?P<effect>.*)",
    re.IGNORECASE | re.DOTALL,
)

FAILED_SAVE = re.compile(
    r"\b(?:on\s+a\s+)?failed\s+save(?:,|\s+)?\s*"
    r"(?P<effect>.*)",
    re.IGNORECASE | re.DOTALL,
)

SUCCESSFUL_SAVE = re.compile(
    r"\b(?:on\s+a\s+)?successful\s+save(?:,|\s+)?\s*"
    r"(?P<effect>.*)",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

MOVES_DISTANCE = re.compile(
    r"\bmoves?\s+(?:it\s+)?(?:up\s+to\s+)?"
    r"(?P<distance>\d+)\s*ft\.",
    re.IGNORECASE,
)

SPEED_ZERO = re.compile(
    r"\bspeed\s+(?:becomes?|is)\s+0\b",
    re.IGNORECASE,
)

SPEED_HALVED = re.compile(
    r"\bspeed\s+is\s+halved\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Special attack effects
# ---------------------------------------------------------------------------

CRITICAL_AT_ZERO = re.compile(
    r"\b(?:dies?|die)\s+if\s+.*?reduces?.*?to\s+0\s+hit points",
    re.IGNORECASE,
)

DIES_AT_ZERO = re.compile(
    r"\bdies?\s+if\s+.*?reduces?.*?to\s+0\s+hit points",
    re.IGNORECASE,
)

REPEAT_SAVE = re.compile(
    r"\b(?:can|must)\s+repeat\s+the\s+saving\s+throw\b"
    r"(?:\s+at\s+the\s+end\s+of\s+(?P<timing>[^.]+))?",
    re.IGNORECASE,
)

HALF_DAMAGE_SUCCESS = re.compile(
    r"\bhalf\s+as\s+much\s+damage\s+on\s+a\s+successful\s+save\b",
    re.IGNORECASE,
)

NO_SAVE = re.compile(
    r"\bwithout\s+a\s+saving\s+throw\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

WHITESPACE = re.compile(r"\s+")

LEADING_NUMBER = re.compile(
    r"^\s*\d+\.\s*"
)

LEADING_BULLET = re.compile(
    r"^\s*[•*-]\s*"
)


TARGET_COUNT = re.compile(
    r"\b(?P<minimum>one|two|three|four|five|six|seven|eight|nine|ten|\d+)"
    r"(?:\s+to\s+(?P<maximum>one|two|three|four|five|six|seven|eight|nine|ten|\d+))?"
    r"\s+targets?\b",
    re.IGNORECASE,
)

DAMAGE_ROLL = re.compile(
    r"\b(\d+)\s*\((\d+d\d+)\)\s+"
    r"(acid|bludgeoning|cold|fire|force|lightning|necrotic|piercing|"
    r"poison|psychic|radiant|slashing|thunder)\s+damage\b",
    re.IGNORECASE,
)

SAVING_THROW = re.compile(
    r"\bDC\s+(\d+)\s+"
    r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)"
    r"\s+saving throw\b",
    re.IGNORECASE,
)

CONDITION = re.compile(
    r"\b("
    r"blinded|charmed|deafened|exhaustion|frightened|grappled|"
    r"incapacitated|invisible|paralyzed|petrified|poisoned|prone|"
    r"restrained|stunned|unconscious"
    r")\b",
    re.IGNORECASE,
)

DICE = re.compile(
    r"\b(\d+)d(\d+)\b",
    re.IGNORECASE,
)


NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def parse_number(value: str) -> int:
    value = value.lower()

    if value in NUMBER_WORDS:
        return NUMBER_WORDS[value]

    return int(value)