# XML Coverage Matrix

Verified against `5eFile.xml` and the schemas under `schemas/entities/` on 2026-09-10.
This matrix documents source-to-schema decisions only. It does not implement XML
parsing or normalization.

## Conventions

- Raw XML element names retain their source spelling and order.
- Repeated `text`, trait, action, and progression elements remain ordered lists.
- Useful source descriptions are preserved even when structured extraction is supported.
- An explicit gap means the current schema cannot represent the source structure without a justified schema change.
- Ambiguous mechanics remain in descriptive text; no numeric or enum value is invented.

## Item

Schema: `schemas/entities/Item.schema.json`

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required. |
| `type` | `category` via item-category values | Normalize only after confirming the source code mapping. Preserve the raw code during parsing. |
| `weight` | `weight` | Parse a nonnegative number when present; preserve malformed or nonnumeric values in description/review data. |
| `value` | `cost` via cost component | Normalize according to the source unit and existing cost schema; do not assume a unit from a number alone. |
| `detail` | `description`, `magic_item`, or review data | Preserve attunement and rarity prose. Extract only values supported by the magic-item component. |
| `text` (repeated) | `description` and/or `features` | Preserve every ordered paragraph, including empty source paragraphs where position matters. |
| `ac` | `armor` via armor component | Normalize armor class only when the category confirms armor semantics. |
| `dmg1`, `dmg2`, `dmgType` | `weapon` via weapon and damage components | Map primary, versatile, and damage-type values only when source values are unambiguous. |
| `range` | `weapon.range` | Normalize supported range forms; preserve unusual compound text. |
| `property` (repeated) | `weapon.properties` | Map known weapon properties; retain unsupported property text. |
| `strength` | `armor.strength` | Normalize numeric requirement when present; preserve unusual values. |
| `stealth` | `armor.stealth` | Map the source restriction through the armor component. |
| `modifier` with `category` | `weapon`, `armor`, `magic_item`, or `features` | Route by category and modifier text only after source-specific rules are established. Preserve original text and attributes. |
| `roll` | `features` or supported effect/roll structure | Preserve explicit dice text. Do not infer an effect from a roll alone. |
| `magic` | `magic_item` | Treat presence as a magic-item signal; do not infer rarity, attunement, charges, or spells without source evidence. |
| `range`, `property`, `modifier`, `roll` repeated/empty | Corresponding list or descriptive field | Preserve ordering and empty elements in raw data; omit only during normalization when schema semantics make absence equivalent. |

Representative source values: `Copper (cp)`, `Arrows`, `Shield +2`, `Wand of Orcus`, and `Powered Armor`.
Known gap: no direct schema field represents every raw item code or every arbitrary modifier/roll form.

## Monster

Schema: `schemas/entities/Monster.schema.json` extending `Creature.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required through Creature. |
| `size` | `size` | Map through the size values; preserve unsupported source values as review data. |
| `type` | `creature_type` | Map through creature-type values where supported; preserve compound type text. |
| `alignment` | `alignment` | Parse supported alignment forms; retain values such as `any evil alignment` descriptively when not representable. |
| `ac` | `armor_class` | Split numeric value and source description only when unambiguous. |
| `hp` | `hit_points`, `hit_dice` | Parse the supported hit-point and dice pattern; preserve the complete source value. |
| `speed` | `movement` | Normalize each supported movement mode and distance. |
| `str`, `dex`, `con`, `int`, `wis`, `cha` | `ability_scores` | Map six ability values through the shared ability-score component. |
| `save` | `saving_throws` | Parse supported ability and bonus pairs; retain compound text. |
| `skill` | `skills` | Parse supported skill and bonus pairs; retain unknown skill text. |
| `resist` | `damage_resistances` | Map known damage types; preserve compound or conditional resistance text. |
| `vulnerable` | `damage_vulnerabilities` | Map known damage types; preserve compound or conditional vulnerability text. |
| `immune` | `damage_immunities` | Map known damage types; preserve conditional details in description. |
| `conditionImmune` | `condition_immunities` | Map known conditions; preserve unsupported compound values. |
| `senses` | `senses` | Parse supported sense and distance forms; preserve the original string. |
| `passive` | `passive_perception` | Parse a nonnegative integer when present. |
| `languages` | `languages` | Split only where the source clearly lists languages; preserve prose such as `plus up to five other languages`. |
| `cr` | `challenge_rating` | Parse the supported numeric challenge rating. |
| `trait` with `name`, repeated `text` | `features` | Preserve ordered text blocks and nested child data. |
| `action` with `name`, repeated `text`, `attack` | `actions` | Preserve descriptions and normalize attacks only when the pipe-delimited source is valid. |
| `reaction` with `name`, repeated `text`, `attack` | `reactions` | Same treatment as actions; retain source text. |
| `legendary` with `name`, repeated `text`, `attack` | `legendary_actions` | Preserve action cost text and nested attacks. |
| `spells` | `spell_casting.spells_known` | Normalize lists only when spellcasting context and schema structure support it; preserve prepared-spell prose. |
| `slots` | `spell_casting` | Map level-indexed slots only after confirming the existing component can represent the sequence. |
| `environment` | `environments` | Split clear comma-separated values; preserve empty or unusual source text. |
| `sense` | `senses` or descriptive text | Inspect separately from `senses`; do not merge without source evidence. |
| empty defense, sense, environment, spell, or slot elements | Corresponding optional field | Preserve as empty raw elements; normalize as absent only when schema semantics permit. |

Representative source values: `Giant Fly`, `Lich`, `Aarakocra`, and `Lhammaruntosz`.
Known gaps: the inherited schema does not directly represent every compound defense,
all spell-slot source forms, or arbitrary nested attack text without preserving prose.

## Spell

Schema: `schemas/entities/Spell.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required. |
| `level` | `level` | Parse the integer level. |
| `school` | `school` | Map through the school values. |
| `time` | `casting_time` | Normalize supported casting-time structures; preserve source wording. |
| `range` | `target` and/or range component | Map supported distances and targets; retain unusual range prose. |
| `components` | `components` | Normalize supported verbal, somatic, and material flags. |
| material text in `components` or source text | `material` | Preserve material requirements and costs; do not infer missing costs. |
| `duration` | `duration` and `concentration` | Split concentration only when explicit and retain the full duration text. |
| `ritual` | `ritual` | Map an explicit ritual value. |
| `classes` | `classes` | Split clear class lists; preserve unknown or source-specific names. |
| `text` (repeated) | `description`, `higher_level`, `effects`, `grants`, or `roll_table` | Preserve every paragraph in order; extract supported mechanics in addition to source text. |
| `roll` (repeated) | `roll_table` or effect roll | Use only when the surrounding spell text establishes its meaning. |
| empty `text`, `roll`, or optional field | Corresponding optional field | Preserve raw emptiness; omit from normalized output only when absence is equivalent. |

Representative source values: `Cure Wounds`, `Prismatic Spray`, and `Aid`.
Known gap: paragraph semantics such as higher-level text may require context beyond the raw tag.

## Feat

Schema: `schemas/entities/Feat.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required. |
| `text` (repeated) | `description`, `features`, or supported action/effect fields | Preserve all paragraphs in order. Extract mechanics only where schema support is clear. |
| `prerequisite` | `prerequisite` | Normalize supported prerequisites; preserve compound prose. |
| `proficiency` | proficiency fields | Classify only when the proficiency category is explicit. |
| `modifier` with `category` | `ability_score_increases`, actions, or supported feature fields | Use category plus text; preserve unsupported modifiers. |
| empty `prerequisite` or `text` | Optional field or description | Preserve raw emptiness and do not fabricate a prerequisite or description. |

Representative source values: `Actor`, `Fey Touched`, and `Telepathic (Charisma)`.
Known gap: arbitrary modifier categories and prerequisite prose do not always map to typed fields.

## Race

Schema: `schemas/entities/Race.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required. |
| `size` | `size` | Map supported size values. |
| `speed` | `movement` | Normalize supported movement values. |
| `ability` | `ability_score_increases` | Extract explicit ability increases or choices only when unambiguous. |
| `modifier` with `category` | supported proficiency, ability, or feature fields | Classify using category and preserve modifier text. |
| `proficiency` | proficiency fields | Map only when the proficiency kind is explicit. |
| `spellAbility` | spell-grant or feature data | Preserve the source value; no direct top-level schema field exists. |
| `trait` with `name`, `text`, `special`, `modifier` | `features`, actions, or supported grants | Preserve nested structures and full descriptions. |
| empty `ability`, `proficiency`, or `spellAbility` | Optional field | Preserve raw emptiness; omit only when normalized absence is semantically correct. |

Representative source values: `Elf`, `Dragonborn (Black)`, `Lizardfolk`, and `Custom Lineage`.
Known gap: subtype and spell-ability source conventions may require context not represented by one XML tag.

## Background

Schema: `schemas/entities/Background.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Direct string; required. |
| `proficiency` | `skill_proficiencies`, `tool_proficiencies`, or related fields | Classify only when the source identifies the proficiency type. |
| `trait` with `name`, repeated `text` | `features` and/or `description` | Preserve every nested text node and feature name. |
| equipment prose in trait text | `equipment` or `description` | Create structured equipment only when the source is explicit and the Equipment schema supports it; otherwise preserve prose. |
| empty `proficiency` | Optional proficiency field | Preserve raw emptiness and do not invent a proficiency. |

Representative source values: `Acolyte`, `Charlatan`, `Criminal`, and `Anthropologist`.
Known gap: equipment choices and descriptive feature text cannot always be separated into typed objects.

## Class

Schema: `schemas/entities/Class.schema.json`.

| XML tag or structure | Target field/component | Decision |
| --- | --- | --- |
| `name` | `name` | Map through class-name values; required. |
| `hd` | `hit_dice` | Map through the dice value schema; required. |
| `proficiency` | `saving_throws`, weapon, armor, tool, or skill fields | Classify using source context; preserve ambiguous prose. |
| `armor` | `armor_proficiencies` | Map supported armor proficiency values. |
| `weapons` | `weapon_proficiencies` | Map supported weapon proficiency values. |
| `tools` | `tool_proficiencies` | Map supported tool values. |
| `numSkills` | `skill_choices` | Use as a count only with the corresponding skill-choice source context. |
| `spellAbility` | `spellcasting` | Map supported spellcasting ability information. |
| `wealth` | `description` or source data | Preserve starting-wealth prose; no direct Class schema field currently exists. |
| `armor`, `proficiency`, `tools`, `weapons` repeated/compound | Corresponding proficiency arrays | Normalize only established values; preserve unsupported text. |
| `autolevel` with `level`, `scoreImprovement` | `features` only where flattening is lossless | Preserve every level and attribute in raw data. The current Class schema has no level-indexed progression field. |
| `autolevel/feature` | `features` | May be represented only if level association is not required; otherwise explicit schema gap. |
| `autolevel/slots` | `spellcasting` or progression gap | Preserve source; do not flatten without a level association. |
| `autolevel/counter` | progression gap or feature description | Preserve source; no direct Class schema field exists. |
| empty `spellAbility` | Optional spellcasting field | Preserve raw emptiness and do not infer spellcasting. |

Representative source values: `Barbarian`, `Cleric`, `Bard`, and `Spellcaster Sidekick`.
Known gap: class level progression, score-improvement metadata, slots, and counters are not
represented as level-indexed structures by the current Class schema. This is a documented
schema boundary for Chunk 17, not a reason to weaken the schema in this chunk.

## Source Boundaries and Unsupported Records

The inventory found no top-level `weapon`, `equipment`, or `subclass` records. These
remain schema concepts. Item category values may normalize into weapon, armor, magic-item,
or generic item structures, but must not be treated as separate source entities. Class
features that resemble subclasses must remain class data until a reliable source boundary
is established.

The matrix deliberately does not prescribe parser implementation, semantic inference, or
schema changes. Those decisions belong to the entity-specific chunks after the relevant
schema and representatives are inspected again.
