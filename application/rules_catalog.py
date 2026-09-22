from __future__ import annotations


_RULE_DESCRIPTIONS = {
    "ability_score": {
        "handbook_reference": "Player's Handbook, Chapter 7, Using Ability Scores (pp. 173-179)",
        "description": "One of the six abilities used to describe a creature's capabilities.",
        "strength": "Strength measures bodily power and supports forceful attacks, lifting, and athletic effort.",
        "dexterity": "Dexterity measures agility, reflexes, balance, and precision, and commonly affects Armor Class and initiative.",
        "constitution": "Constitution measures stamina and resilience, and contributes to hit points and concentration checks.",
        "intelligence": "Intelligence measures memory, reasoning, and learned knowledge.",
        "wisdom": "Wisdom measures awareness, intuition, and sensitivity to the world and other creatures.",
        "charisma": "Charisma measures force of personality, confidence, and social influence.",
    },
    "ability_kind": {"description": "A category describing the kind of custom ability."},
    "alignment": {
        "description": "A broad description of a creature's moral and ethical outlook.",
        "lawful": "The lawful alignment axis describes a preference for order, structure, rules, or dependable codes.",
        "chaotic": "The chaotic alignment axis describes a preference for freedom, spontaneity, or personal choice over imposed order.",
        "good": "The good alignment axis describes concern for the welfare and dignity of others.",
        "evil": "The evil alignment axis describes a willingness to harm or exploit others for personal ends.",
        "neutral": "Neutral can describe balance between alignment extremes or an absence of strong commitment to one axis.",
        "unaligned": "Unaligned describes a creature that does not meaningfully participate in the moral or ethical alignment axes.",
        "any": "Any alignment allows the rule to apply regardless of the creature's alignment.",
    },
    "action_type": {
        "handbook_reference": "Player's Handbook, Chapter 9, Combat, Actions in Combat (pp. 192-193)",
        "description": "The action economy category used by an action or feature.",
        "action": "A creature can take one action on its turn, choosing from the actions available to it.",
        "bonus_action": "A creature can take a bonus action only when a feature, spell, or other rule grants one, and can take no more than one per turn.",
        "reaction": "A reaction is an immediate response to a trigger and is unavailable again until the start of the creature's next turn.",
        "free_action": "The Player's Handbook does not define a general free-action turn option; this project value is an extension for content that uses one.",
        "legendary_action": "Legendary actions are not a standard Player's Handbook character action; this value represents a monster rule defined by a creature's stat block.",
        "lair_action": "Lair actions are not a standard Player's Handbook character action; this value represents an environmental monster effect defined by a creature's stat block.",
        "mythic_action": "Mythic actions are not defined as a standard Player's Handbook rule; this value represents a setting or monster-system extension.",
    },
    "attack_type": {
        "handbook_reference": "Player's Handbook, Chapter 9, Combat (pp. 194-196)",
        "description": "The kind of attack roll used by an effect or attack.",
        "melee_weapon": "A melee weapon attack uses a melee weapon against a target within the weapon's reach.",
        "ranged_weapon": "A ranged weapon attack uses the weapon's normal or long range; beyond normal range it has disadvantage, and beyond long range it cannot be made.",
        "melee_spell": "A melee spell attack targets a creature within the spell's reach using the caster's spell attack modifier.",
        "ranged_spell": "A ranged spell attack targets a creature within the spell's range using the caster's spell attack modifier.",
    },
    "bonus_type": {"description": "The kind of statistic that a magic item bonus modifies."},
    "casting_time": {"handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 202-203)", "description": "A unit used to describe how long it takes to cast a spell."},
    "distance_type": {
        "handbook_reference": "Player's Handbook, Chapter 8, Adventuring (pp. 181-183)",
        "description": "A unit used when describing ranges, speeds, and other distances.",
        "feet": "Feet are the standard tactical distance unit for ranges, movement, and areas of effect.",
        "miles": "Miles measure long travel distances rather than the short distances used on a battle map.",
    },
    "duration": {
        "handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 203-204)",
        "description": "A unit or condition used to describe how long an effect lasts.",
        "round": "A round is the time in which every participant in an encounter gets a turn.",
        "minute": "A minute is ten rounds and is used for longer actions, spells, and durations.",
        "hour": "An hour is a longer interval used for travel, rituals, and extended effects.",
        "day": "A day is the ordinary cycle used for rests, travel, and effects lasting until the next day.",
        "week": "A week is a period used for downtime, long projects, and extended effects.",
        "month": "A month is a calendar-scale period used for long-term activity and duration.",
        "year": "A year is a full calendar cycle used for very long durations and aging effects.",
        "instantaneous": "Instantaneous means the effect happens immediately and does not continue as an ongoing duration.",
        "until_dispelled": "Until dispelled means the effect remains until a rule or successful dispelling ends it.",
        "until_saved": "Until saved means the effect continues until the affected creature succeeds on the required saving throw.",
        "next_round": "Next round means the effect lasts until the indicated point in the following round.",
    },
    "movement_type": {
        "handbook_reference": "Player's Handbook, Chapter 8, Adventuring (pp. 181-183)",
        "description": "A mode of movement used when describing a creature's speed.",
        "walk": "Walking is a creature's ordinary ground movement speed.",
        "fly": "Flying allows movement through the air, subject to the creature's speed and any rule requiring it to land.",
        "swim": "Swimming is movement through water and normally uses a creature's swim speed when it has one.",
        "climb": "Climbing is movement up or across a surface and can be affected by the surface and available handholds.",
        "burrow": "Burrowing is movement through earth or another material when the creature's rules allow it.",
    },
    "recharge": {"description": "A timing condition that restores a feature, spell, or item use.", "short_rest": "A short-rest recharge restores an ability after a brief period of rest when the creature's rules permit it.", "long_rest": "A long-rest recharge restores an ability after the required extended rest.", "dawn": "Dawn is the daily time at which an ability or effect refreshes when its rule specifies dawn.", "dusk": "Dusk is the daily time at which an ability or effect refreshes when its rule specifies dusk."},
    "spell_component": {
        "handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 203-204)",
        "description": "A component required to cast a spell.",
        "verbal": "A verbal component is a spoken magical utterance; a caster who cannot speak cannot provide it.",
        "somatic": "A somatic component is a deliberate gesture. The caster must have at least one free hand unless another rule supplies an exception.",
        "material": "A material component is the physical substance listed by the spell. A spellcasting focus can replace it when the spell permits.",
    },
    "target_type": {
        "handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 204-205)",
        "description": "The kind of creature or object an effect can target.",
        "creature": "Creature identifies a living or active creature as the target of an effect.",
        "ally": "Ally identifies a friendly creature as the target of an effect.",
        "enemy": "Enemy identifies a hostile creature as the target of an effect.",
        "object": "Object identifies a non-creature item or thing as the target of an effect.",
        "special": "Special means the effect defines its own targeting rule rather than using the ordinary target categories.",
    },
    "target_zone": {
        "handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 204-205)", "description": "The shape or scope of an effect's area.",
        "single": "A single-target effect selects one creature, object, or point as specified by its rule.", "line": "A line area extends from its point of origin in a straight path to the length specified by the effect.",
        "cone": "A cone area extends from its point of origin in the chosen direction and widens across its length.", "cube": "A cube area originates from a point on one face and fills the cube's stated dimensions.",
        "cylinder": "A cylinder area extends from its point of origin with the stated radius and height.", "sphere": "A sphere area extends outward from its point of origin to the stated radius.",
    },
    "targeting": {
        "handbook_reference": "Player's Handbook, Chapter 10, Spellcasting (pp. 204-205)", "description": "The targeting mode used by an action or spell.",
        "self": "A range of Self makes the caster or user the point of origin or target, as the effect specifies.", "touch": "A range of Touch requires the caster or user to reach the target.",
        "range": "A ranged effect targets a creature, object, or point within the listed distance and requires a clear path unless its rule says otherwise.", "sight": "A sight-based target must be visible to the user and satisfy the effect's other targeting requirements.", "unlimited": "An unlimited range has no stated distance limit, but the effect can still impose visibility or target restrictions.",
    },
    "proficiencies-languages": {
        "handbook_reference": "Player's Handbook, Chapter 4, Personality and Background (p. 123)", "description": "Languages a character or creature can communicate in or understand.",
        "common": "Common is a widely used language for trade and communication.", "dwarvish": "Dwarvish is the language associated with dwarven peoples.", "elvish": "Elvish is the language associated with elven peoples.", "giant": "Giant is the language associated with giants and giant-descended peoples.", "gnomish": "Gnomish is the language associated with gnomes.", "halfling": "Halfling is the language associated with halflings.", "orc": "Orc is the language associated with orcs.", "abyssal": "Abyssal is associated with demons and the Abyss.", "celestial": "Celestial is associated with angels and other creatures of the Upper Planes.", "draconic": "Draconic is the ancient language associated with dragons.", "deep_speech": "Deep Speech is associated with aberrations and other alien creatures.", "infernal": "Infernal is associated with devils and the ordered Lower Planes.", "primordial": "Primordial is the language of elemental creatures, with dialects used by different elements.", "sylvan": "Sylvan is associated with fey creatures and the Feywild.", "undercommon": "Undercommon is a trade language used by many peoples of the Underdark.",
    },
    "proficiencies-skills": {
        "handbook_reference": "Player's Handbook, Chapter 7, Using Ability Scores (pp. 175-179)", "description": "Focused areas of ability checks associated with the six ability scores.",
        "acrobatics": "Dexterity-based checks for balance, tumbling, and keeping footing.", "animal_handling": "Wisdom-based checks for calming, controlling, or understanding animals.", "arcana": "Intelligence-based checks about spells, magic items, magical traditions, and the planes.", "athletics": "Strength-based checks for climbing, jumping, swimming, and feats of physical force.", "deception": "Charisma-based checks for concealing the truth or convincing someone of a falsehood.", "history": "Intelligence-based checks for recalling historical events, peoples, and places.", "insight": "Wisdom-based checks for reading a creature's intentions, mood, or honesty.", "intimidation": "Charisma-based checks for influencing someone through threats, pressure, or hostile force.", "investigation": "Intelligence-based checks for deductions, searching, and finding clues through reasoning.", "medicine": "Wisdom-based checks for diagnosing injuries, illness, and a creature's physical condition.", "nature": "Intelligence-based checks about terrain, plants, animals, weather, and natural cycles.", "perception": "Wisdom-based checks for noticing details through sight, hearing, smell, or other senses.", "performance": "Charisma-based checks for entertaining an audience through music, acting, or similar expression.", "persuasion": "Charisma-based checks for influencing others through tact, argument, etiquette, or good faith.", "religion": "Intelligence-based checks about deities, rites, symbols, religious traditions, and the planes.", "sleight_of_hand": "Dexterity-based checks for legerdemain, concealed actions, and manipulating small objects.", "stealth": "Dexterity-based checks for hiding, moving quietly, and avoiding notice.", "survival": "Wisdom-based checks for tracking, navigation, foraging, and enduring the wilderness.",
    },
    "proficiencies-tools": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (pp. 154-155)", "description": "Tools and kits that grant specialized capabilities or proficiency-based checks."},
    "proficiencies-armor": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (pp. 144-146)", "description": "Armor groups and armor types that determine protection and training requirements.", "light": "Light armor allows the wearer to add the full Dexterity modifier to Armor Class.", "medium": "Medium armor limits the Dexterity modifier that can be added to Armor Class.", "heavy": "Heavy armor provides strong protection and does not add the wearer's Dexterity modifier to Armor Class.", "shield": "A shield increases Armor Class while wielded, but requires one hand and shield proficiency."},
    "proficiencies-instruments": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (p. 154)", "description": "Musical instruments that can be used with the appropriate proficiency."},
    "proficiencies-gaming_sets": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (p. 154)", "description": "Gaming sets used for games of chance or skill."},
    "proficiencies-vehicles": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (p. 155)", "description": "Vehicle groups that describe training with land, water, or air vehicles."},
    "weapons-groups": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (pp. 146-149)", "description": "Simple and martial weapon groups used to describe weapon training.", "simple": "Simple weapons are easy to use and are commonly included in basic weapon training.", "martial": "Martial weapons require more specialized combat training."},
    "weapons-tags": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (pp. 146-149)", "description": "Weapon properties that change how a weapon is wielded, attacked with, or reloaded.", "versatile": "A versatile weapon can be used in one or two hands and has a separate two-handed damage die.", "light": "A light weapon is small and easy to handle; two-weapon fighting normally uses light melee weapons.", "heavy": "A heavy weapon is large and unwieldy; Small creatures have disadvantage attacking with one.", "finesse": "A finesse weapon lets the attacker choose Strength or Dexterity for attack and damage rolls.", "reach": "A reach weapon extends the wielder's reach by 5 feet for its attacks and opportunity attacks.", "thrown": "A thrown weapon can make a ranged attack using its listed range and retains its melee properties.", "loading": "A loading weapon permits only one piece of ammunition to be fired when an action would otherwise allow multiple attacks.", "ammunition": "An ammunition weapon requires ammunition for each attack; ammunition can be recovered after a battle when the field is searched.", "special": "A special weapon uses an unusual rule printed with its weapon entry.", "two_handed": "A two-handed weapon requires two hands when making an attack with it.", "monk": "Monk is a project vocabulary tag; the Player's Handbook instead defines monk-weapon eligibility through the monk class rules."},
    "weapons-types": {"handbook_reference": "Player's Handbook, Chapter 5, Equipment (pp. 146-149)", "description": "Specific weapon forms, each with its own damage, properties, and range in equipment data.", "club": "a simple melee weapon used to deal bludgeoning damage", "dagger": "a finesse and light simple melee weapon that can also be thrown", "greatclub": "a heavy two-handed simple melee weapon that deals bludgeoning damage", "handaxe": "a light simple melee weapon that can also be thrown", "javelin": "a simple melee weapon designed to be thrown", "light_hammer": "a light simple melee weapon that can also be thrown", "mace": "a simple melee weapon that deals bludgeoning damage", "quarterstaff": "a versatile simple melee weapon", "sickle": "a light simple melee weapon", "spear": "a versatile simple melee weapon that can also be thrown", "crossbow_light": "a loading simple ranged weapon that uses ammunition", "dart": "a finesse simple ranged weapon that can be thrown", "shortbow": "a two-handed simple ranged weapon that uses ammunition", "sling": "a simple ranged weapon that uses ammunition", "battleaxe": "a versatile martial melee weapon", "flail": "a martial melee weapon that deals bludgeoning damage", "glaive": "a heavy, reach, two-handed martial melee weapon", "greataxe": "a heavy two-handed martial melee weapon", "greatsword": "a heavy two-handed martial melee weapon", "halberd": "a heavy, reach, two-handed martial melee weapon", "lance": "a reach martial melee weapon with special mounted-use considerations", "longsword": "a versatile martial melee weapon", "maul": "a heavy two-handed martial melee weapon that deals bludgeoning damage", "morningstar": "a martial melee weapon that deals piercing damage", "pike": "a heavy, reach, two-handed martial melee weapon", "rapier": "a finesse martial melee weapon", "scimitar": "a finesse and light martial melee weapon", "shortsword": "a finesse and light martial melee weapon", "trident": "a versatile martial melee weapon that can also be thrown", "war_pick": "a martial melee weapon that deals piercing damage", "warhammer": "a versatile martial melee weapon", "whip": "a finesse and reach martial melee weapon", "blowgun": "a loading martial ranged weapon that uses ammunition", "crossbow_hand": "a light martial ranged weapon that uses ammunition", "crossbow_heavy": "a heavy and loading martial ranged weapon that uses ammunition", "longbow": "a heavy two-handed martial ranged weapon that uses ammunition", "net": "a special martial ranged weapon used to restrain a target rather than deal damage", "any_sword": "a grouping for effects or proficiencies that apply to any qualifying sword"},
    "conditions": {"handbook_reference": "Player's Handbook, Appendix A, Conditions (pp. 290-292)", "description": "A condition applies a defined set of effects to a creature until its duration or removal rule ends.", "blinded": "A blinded creature cannot see, automatically fails sight-based ability checks, grants advantage to attackers, and has disadvantage on its attacks.", "charmed": "A charmed creature cannot attack or harm the charmer through targeted abilities or magic, and the charmer has advantage on social checks against it.", "deafened": "A deafened creature cannot hear and automatically fails checks that require hearing.", "frightened": "A frightened creature has disadvantage on checks and attacks while it can see the source of fear and cannot willingly move closer to it.", "grappled": "A grappled creature has speed 0 and cannot benefit from speed bonuses; the condition ends when the grapple is broken or removed.", "incapacitated": "An incapacitated creature cannot take actions or reactions.", "invisible": "An invisible creature cannot be seen without special senses or magic; attacks against it have disadvantage and its attacks have advantage.", "paralyzed": "A paralyzed creature is incapacitated, cannot move or speak, automatically fails Strength and Dexterity saves, and attacks from within 5 feet that hit are critical hits.", "petrified": "A petrified creature becomes an inanimate solid substance, is incapacitated and unaware, cannot move or speak, automatically fails Strength and Dexterity saves, and gains broad resistances and immunities.", "poisoned": "A poisoned creature has disadvantage on attack rolls and ability checks.", "prone": "A prone creature crawls or spends half its speed to stand; its attacks have disadvantage, nearby attacks have advantage, and other attacks have disadvantage.", "restrained": "A restrained creature has speed 0, grants advantage to attackers, has disadvantage on attacks and Dexterity saves, and cannot benefit from speed bonuses.", "stunned": "A stunned creature is incapacitated, cannot move, speaks only falteringly, automatically fails Strength and Dexterity saves, and grants advantage to attackers.", "unconscious": "An unconscious creature is incapacitated, unaware, prone, unable to move or speak, automatically fails Strength and Dexterity saves, and is especially vulnerable to nearby attacks."},
    "size": {"description": "A creature size category affects the space it occupies, the area it controls, and some interaction rules.", "tiny": "A Tiny creature occupies a very small space, typically less than a four-foot square.", "small": "A Small creature occupies a compact space and can share some spaces under the normal movement rules.", "medium": "A Medium creature is the standard humanoid-sized category and normally occupies a five-foot space.", "large": "A Large creature occupies a four-square space, normally ten feet by ten feet.", "huge": "A Huge creature occupies a nine-square space, normally fifteen feet by fifteen feet.", "gargantuan": "A Gargantuan creature occupies at least a sixteen-square space, normally twenty feet by twenty feet or larger."},
    "sense": {"description": "A special sense grants awareness beyond ordinary sight or hearing, usually within a stated range.", "blindsight": "Blindsight lets a creature perceive its surroundings without relying on sight, within the stated range.", "darkvision": "Darkvision lets a creature see in darkness as though it were dim light, but does not normally reveal color there.", "tremorsense": "Tremorsense detects the origin of vibrations within the stated range when the creature and source share a surface or the creature is in the source's medium.", "truesight": "Truesight lets a creature see normally in darkness, notice invisible creatures and objects, see through illusions, perceive the original form of transformations, and see into the Ethereal Plane within range."},
    "damage_type": {"description": "A damage type classifies the harm dealt and interacts with resistance, immunity, and vulnerability.", "acid": "Acid damage represents corrosive substances or effects.", "bludgeoning": "Bludgeoning damage comes from blunt impact, crushing force, constriction, or falling.", "cold": "Cold damage comes from intense chill or freezing effects.", "fire": "Fire damage comes from flame, heat, or combustion.", "force": "Force damage is concentrated magical energy.", "lightning": "Lightning damage comes from electrical energy or discharge.", "necrotic": "Necrotic damage withers matter and life force.", "piercing": "Piercing damage comes from puncturing attacks such as arrows, spears, or claws.", "poison": "Poison damage comes from toxic substances or venom.", "psychic": "Psychic damage assaults the mind.", "radiant": "Radiant damage comes from holy power, brilliant energy, or similar forces.", "slashing": "Slashing damage comes from cutting attacks such as blades or claws.", "thunder": "Thunder damage is concussive energy produced by intense sound."},
    "spell_school": {"handbook_reference": "Player's Handbook, Chapter 10, Spellcasting and Chapter 11, Spells", "description": "A school groups spells by the kind of magical effect they produce.", "abjuration": "Abjuration is the school of protective and warding magic, including barriers, negation, banishment, and magical defenses.", "conjuration": "Conjuration concerns transporting or summoning creatures and objects, and creating some objects or effects.", "divination": "Divination reveals information, including hidden things, forgotten secrets, future possibilities, or distant places.", "enchantment": "Enchantment affects minds by influencing or controlling behavior and emotions.", "evocation": "Evocation channels magical energy to create direct effects, including elemental forces and damaging effects.", "illusion": "Illusion deceives the senses or creates false images, sounds, or other perceptions.", "necromancy": "Necromancy manipulates life force, death, and the energies associated with living or dead creatures.", "transmutation": "Transmutation changes a creature, object, or environment by altering its properties or form."},
    "spellcasting_progression": {
        "handbook_reference": "Player's Handbook, Chapter 3, Classes",
        "description": "The rate at which a class or subclass gains spell slots.",
        "full": "Full spellcasting progression grants spell slots at the fastest class progression rate.",
        "half": "Half spellcasting progression grants spell slots at half the full-caster rate.",
        "third": "Third spellcasting progression grants spell slots at one-third the full-caster rate.",
        "pact": "Pact spellcasting uses pact magic slots that recover on a short or long rest.",
    },
    "currency": {"description": "A currency denomination expresses the common exchange value used for equipment and services.", "cp": "Copper pieces are the smallest common coin denomination. Ten copper pieces equal one silver piece.", "sp": "Silver pieces are a common everyday denomination. Ten silver pieces equal one gold piece.", "ep": "Electrum pieces are worth five silver pieces, or half a gold piece.", "gp": "Gold pieces are the standard measure of adventuring wealth. Ten gold pieces equal one platinum piece.", "pp": "Platinum pieces are worth ten gold pieces each."},
    "rarity": {"description": "An item rarity expresses how frequently a magic item is encountered and how exceptional it is.", "common": "Common magic items are the least difficult magical items to find.", "uncommon": "Uncommon magic items are more unusual and valuable than common items.", "rare": "Rare magic items are powerful and difficult to find.", "very_rare": "Very rare magic items are exceptional and seldom encountered.", "legendary": "Legendary magic items are extraordinarily powerful and scarce.", "artifact": "An artifact is a unique or nearly unique magic item with exceptional power and history."},
    "creature_type": {"description": "A creature type identifies the broad nature of a creature and can interact with features and spells.", "aberration": "An aberration has an alien nature and often originates outside the ordinary natural order.", "beast": "A beast is a nonhumanoid living creature that is part of the natural world.", "celestial": "A celestial is a creature native to or strongly tied to the Upper Planes.", "construct": "A construct is made rather than born and is often animated by magic.", "dragon": "A dragon is an ancient reptilian creature, typically powerful and intelligent.", "elemental": "An elemental is a creature formed from or strongly connected to elemental forces.", "fey": "A fey is a creature closely tied to the Feywild and its magic.", "fiend": "A fiend is a creature associated with the Lower Planes.", "giant": "A giant is a large humanoid-shaped creature with its own ancient cultures.", "humanoid": "A humanoid is a two-legged, language-using people or similar creature.", "monstrosity": "A monstrosity is an unusual creature that does not fit another natural category.", "ooze": "An ooze is an amorphous creature, commonly fluid-bodied.", "plant": "A plant is an animate plant or plant-like creature.", "undead": "An undead creature is animated after death by necromantic or similar forces."},
    "item_category": {
        "description": "An item category identifies the broad equipment family to which an item belongs.",
        "armor": "Armor protects its wearer and may impose training or movement requirements.",
        "potion": "A potion is a consumable item that produces its listed magical or physical effect.",
        "ring": "A ring is a wearable item whose magic or function is defined by its entry.",
        "rod": "A rod is a magical implement with the properties and charges described by its entry.",
        "scroll": "A scroll records a spell or magical effect for later use.",
        "staff": "A staff is a weapon or magical implement with the properties described by its entry.",
        "wand": "A wand is a magical implement that may hold charges or reproduce a spell effect.",
        "weapon": "A weapon is equipment used to make attacks or deliver other combat effects.",
        "wonderous_item": "A wondrous item is a miscellaneous magical item with its own special properties.",
        "adventuring_gear": "Adventuring gear is equipment used for travel, exploration, or practical tasks.",
        "tool": "A tool is equipment used to perform a specialized task or support a proficiency.",
    },
}


def _display(value: str) -> str:
    return value.replace("_", " ").title()


def rule_description(value: str, category: str) -> str:
    """Return concise guidance for a canonical rules value."""
    category_entry = _RULE_DESCRIPTIONS.get(category, {})
    description = category_entry.get(value)
    if description:
        if category == "weapons-types":
            return f"{_display(value)} is {description}. Its equipment entry supplies its attack range, damage, cost, and weight."
        return description
    category_key = category.rsplit("-", 1)[-1]
    category_description = category_entry.get("description", f"{_display(value)} is a canonical value in the {category} rules vocabulary.")
    if category_key == "tools":
        return f"{_display(value)} proficiency represents training with this tool or kit. It can support relevant ability checks when the character has time and suitable materials."
    if category_key == "instruments":
        return f"{_display(value)} is a musical instrument for which a character may have tool proficiency."
    if category_key == "gaming_sets":
        return f"{_display(value)} is a gaming set used for games of chance or skill and related tool checks."
    if category_key == "vehicles":
        return f"{_display(value)} is a vehicle proficiency category covering {value} vehicles and their operation."
    if category_key == "languages":
        return f"{_display(value)} is a language proficiency that represents the ability to communicate in that language."
    return f"{_display(value)}: {category_description} The schema permits this value and may also permit a non-empty custom value for homebrew content."


def rule_details(value: str, category: str, schema_names: tuple[str, ...]) -> dict[str, str]:
    schema_paths = []
    for schema_name in schema_names:
        if "/" not in schema_name:
            schema_name = f"values/{schema_name}"
        schema_paths.append(f"{schema_name}.schema.json")
    handbook_reference = _RULE_DESCRIPTIONS.get(category, {}).get("handbook_reference", "Player's Handbook reference varies by the rule that uses this value.")
    return {
        "Description": rule_description(value, category),
        "Canonical value": value,
        "Category": category,
        "Validated by": ", ".join(schema_paths),
        "Handbook reference": handbook_reference,
        "Guidance": f"Canonical value: {value}\nCategory: {category}\nSchema reference: {', '.join(schema_paths)}\nHandbook reference: {handbook_reference}",
    }
