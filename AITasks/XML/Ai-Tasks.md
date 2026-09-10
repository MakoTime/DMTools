### Chunk 1: Verify the XML Inventory

* Scope: read-only inspection plus an inventory note if needed.
* Count top-level records and record direct child tags, attributes, nesting, and representative names.
* Confirm whether top-level `weapon`, `equipment`, and `subclass` records exist.
* Do not implement entity parsing.
* Validation: rerun the inventory command and compare the recorded counts.

#### Chunk 1 Verification Note

Verified 2026-09-10 with a read-only ElementTree inventory using the project-local
Python interpreter. The root is `compendium` with 4,507 direct children. Counts
match the inventory in `AGENTS.md`: `item` 1,847, `monster` 1,492, `spell` 824,
`feat` 130, `race` 104, `background` 94, and `class` 16. No top-level `weapon`,
`equipment`, or `subclass` records exist.

| Entity | Direct child tags | Repeated tags | Empty tags | Attributes | Nested structures | Representatives |
| --- | --- | --- | --- | --- | --- | --- |
| `item` | `ac`, `detail`, `dmg1`, `dmg2`, `dmgType`, `magic`, `modifier`, `name`, `property`, `range`, `roll`, `stealth`, `strength`, `text`, `type`, `value`, `weight` | `text` | `detail`, `dmg1`, `dmg2`, `dmgType`, `property`, `range`, `roll`, `stealth`, `strength`, `text`, `value`, `weight` | `modifier.category` | none beyond direct fields | Copper (cp), Wand of Orcus, Powered Armor |
| `monster` | `ac`, `action`, `alignment`, `cha`, `con`, `conditionImmune`, `cr`, `dex`, `environment`, `hp`, `immune`, `int`, `languages`, `legendary`, `name`, `passive`, `reaction`, `resist`, `save`, `sense`, `senses`, `size`, `skill`, `slots`, `speed`, `spells`, `str`, `trait`, `type`, `vulnerable`, `wis` | `action`, `trait` | `alignment`, `conditionImmune`, `cr`, `environment`, `immune`, `languages`, `resist`, `save`, `sense`, `senses`, `skill`, `slots`, `spells`, `vulnerable` | none | `action`, `legendary`, `reaction`, and `trait` contain `name`, `text`, and optional `attack` | Giant Fly, Lich, Lhammaruntosz |
| `spell` | `classes`, `components`, `duration`, `level`, `name`, `range`, `ritual`, `roll`, `school`, `text`, `time` | `text` | `classes`, `components`, `duration`, `range`, `roll`, `text`, `time` | none | none beyond direct fields | Acid Splash, Cure Wounds, Prismatic Spray |
| `feat` | `modifier`, `name`, `prerequisite`, `proficiency`, `text` | `text` | `prerequisite`, `text` | `modifier.category` | none beyond direct fields | Actor, Fey Touched, Telepathic (Charisma) |
| `race` | `ability`, `modifier`, `name`, `proficiency`, `size`, `speed`, `spellAbility`, `trait` | `trait` | `ability`, `proficiency`, `spellAbility` | `modifier.category` | `trait` contains `name`, `text`, and optional `special` or `modifier` | Elf, Dragonborn (Black), Custom Lineage |
| `background` | `name`, `proficiency`, `trait` | `trait` | `proficiency` | none | `trait` contains `name` and `text` | Acolyte, Charlatan, Anthropologist |
| `class` | `armor`, `autolevel`, `hd`, `name`, `numSkills`, `proficiency`, `spellAbility`, `tools`, `wealth`, `weapons` | `autolevel` | `spellAbility` | `autolevel.level`, `autolevel.scoreImprovement` | `autolevel` contains `counter`, `feature`, and `slots` | Barbarian, Cleric, Spellcaster Sidekick |

The inventory preserves source order through ElementTree child order. Empty
elements remain distinguishable from absent elements, and repeated elements are
retained as separate ordered children. No schema-specific parsing or
normalization was performed in this chunk.

### Chunk 2: Lock Down Generic XML Behavior

* Scope: `parsers/xml_parser.py` and `tests/test_xml_parser.py`.
* Verify or implement preservation of attributes, repeated elements, empty elements, ordering, text, and nested children.
* Do not add schema-specific normalization.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_xml_parser.py -v`.

#### Chunk 2 Verification Note

Completed 2026-09-10. The generic XML representation preserves element names,
attributes, source order, repeated elements, empty elements, element text,
nested children, and mixed-content tail text through the `tail` field. No
schema-specific normalization was added.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_xml_parser.py -v` — 10 passed.
* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py tests/test_monster_parser.py tests/test_spell_parser.py -v` — 8 passed, 12 subtests passed.

### Chunk 3: Create the XML Coverage Matrix

* Scope: coverage documentation or a narrowly scoped data file selected after inspection.
* Map each entity tag to a schema field, normalization rule, preserved text, or explicit gap.
* Do not modify schemas or models in this chunk.
* Validation: inspect every top-level XML entity type and every direct child tag against the matrix.

#### Chunk 3 Verification Note

Completed 2026-09-10. Added `XML-COVERAGE-MATRIX.md` with mappings for every
inventoried entity and direct child tag. The matrix records target schema fields,
normalization decisions, reusable schema concepts, source-text preservation,
ambiguous values, unsupported mechanics, and the class progression schema gap.

Validation confirmed that every direct child tag from all seven top-level XML
entity types appears in the matrix. No schemas or models were modified.

### Chunk 4: Generalize Item Source Parsing

* Scope: `parsers/item_parser.py` and its focused tests.
* Ensure raw item parsing preserves all category-dependent fields, repeated text, modifiers, rolls, and attributes.
* Do not normalize items or change Pydantic models yet.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v`.

#### Chunk 4 Verification Note

Completed 2026-09-10. The raw item parser now preserves the inventoried scalar
fields (`ac`, damage, range, stealth, strength, value, and category metadata),
ordered repeated `text`, `property`, and `roll` elements, root attributes, and
all modifier attributes plus source text. Category interpretation, item
normalization, and model changes remain deferred to later chunks.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v` — 3 passed, 3 subtests passed.

### Chunk 5: Adapt Basic Items

* Scope: `parsers/item_adaptor.py` and one or two basic item fixtures/tests.
* Normalize name, category, weight, cost/value, description, and source for nonmagical items.
* Preserve unsupported mechanics as text.
* Validation: focused basic-item adaptor test plus schema validation.

#### Chunk 5 Verification Note

Completed 2026-09-10. Basic item adaptation now maps the observed mundane
category codes, handles optional numeric weight, maps whole-number source values
to gold-piece costs, preserves all non-source description paragraphs, and keeps
source metadata. Fractional, malformed, or otherwise unrepresentable values are
left unstructured rather than converted by inference.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v` — 4 passed, 3 subtests passed. The basic-item case passed Pydantic and Item schema validation.

### Chunk 6: Adapt Weapons and Armor

* Scope: item adaptor/model tests and only the files required by the existing item hierarchy.
* Handle damage, versatile damage, range, properties, armor class, stealth, and strength where the schemas support them.
* Use actual XML representatives before adding parsing rules.
* Validation: focused weapon/armor tests and root-schema validation.

#### Chunk 6 Verification Note

Completed 2026-09-10. Weapon adaptation now maps source damage, damage type,
range, and supported property codes. Armor adaptation maps armor category, AC,
stealth disadvantage, and Strength requirements, including shields. Repeated and
comma-packed source property values are handled consistently. Actual `Shield`,
`Longbow`, and `Longsword` records were validated through the raw parser,
adaptor, Pydantic model, and Item root schema.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py::TestItemParser::test_adapt_weapon_and_armor -v` — 1 passed.
* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py::TestItemParser::test_adapt_source_weapon_and_armor_representatives -v` — 1 passed.
* The full item parser suite is run after this note is recorded.

The source `dmg2` versatile-damage value is preserved by the raw parser and is
emitted as a second damage effect in the active weapon component, alongside
the base damage effect. The separate entity-level `Weapon.schema.json` also
defines `versatile_damage`, but the current Item hierarchy uses the component
weapon schema and its existing `effects` representation.

### Chunk 7: Adapt Magic Items

* Scope: `parsers/item_adaptor.py`, item fixtures, and focused tests.
* Generalize the existing Wand-specific logic for rarity, attunement, bonuses, charges, spells, and features.
* Keep malformed or ambiguous source values descriptive rather than fabricating values.
* Validation: item parser/model tests and Item schema validation.

#### Chunk 7 Verification Note

Completed 2026-09-10. Magic adaptation now handles comma-qualified rarity
details, attunement, source bonus modifiers, charge and recharge text spread
across multiple paragraphs, spell charges, and feature headings used by items
other than the Wand of Orcus. Actual `Arrows +1`, `Armor of Vulnerability
(Bludgeoning)`, and `Staff of Power` records were validated through the raw
parser, adaptor, Pydantic model, and Item root schema.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v` — 7 passed, 3 subtests passed.
* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py::TestItemParser::test_adapt_source_magic_item_representatives -v` — 1 passed.

Unsupported or ambiguous source mechanics remain in the preserved description;
no schema or model changes were needed. The next task is Chunk 8, completing
typed item models against the normalized structures now produced by the
adaptor.

### Chunk 8: Complete Item Models

* Scope: `models/item.py` and item model tests only.
* Align typed models with the normalized Item, Weapon, Armor, MagicItem, and Equipment structures actually produced.
* Do not redesign schemas.
* Validation: item construction and round-trip tests.

#### Chunk 8 Verification Note

Completed 2026-09-10 as a verification-only task. The existing typed item
models already cover the normalized weapon, range, armor, magic-item, charge,
spell-charge, bonus, feature, cost, source, and item structures produced by the
adaptors. Source-backed weapon, armor, and magic-item cases all pass Pydantic
construction and Item root-schema validation, and the existing fixture models
round-trip successfully. No model changes were needed.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v` — 7 passed, 3 subtests passed.

### Chunk 9: Implement Spell Raw Parsing

* Scope: new spell parser module and focused parser tests.
* Preserve spell fields, repeated text, optional values, and explicit `roll` elements.
* Use `Cure Wounds` and `Prismatic Spray` as source representatives.
* Do not extract effects into schema structures yet.
* Validation: focused spell raw-parser tests.

#### Chunk 9 Verification Note

Completed 2026-09-10. The existing raw spell parser preserves all direct scalar
fields, ordered repeated description text, optional empty values, and explicit
roll elements. Actual `Cure Wounds` and `Prismatic Spray` records are covered;
Prismatic Spray retains its full condition-reference text blocks and both
source rolls.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -v` — 2 passed, 1 subtest passed.

### Chunk 10: Adapt Basic Spells

* Scope: spell adaptor and one simple spell fixture/test.
* Normalize name, level, school, casting time, range, components, duration, ritual, classes, and description.
* Preserve all source paragraphs.
* Validation: Spell schema validation and focused adaptor test.

#### Chunk 10 Verification Note

Completed 2026-09-10. Basic spell adaptation now normalizes source level and
school codes, casting time, touch/self/range targets, verbal/somatic/material
components, concentration and duration, ritual, classes, full descriptions,
and source metadata. Actual `Cure Wounds` is validated against the Spell root
schema. Complex effects and roll tables remain deferred to Chunk 11.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -v` — 3 passed, 1 subtest passed.

### Chunk 11: Adapt Complex Spell Mechanics

* Scope: spell adaptor, `Prismatic Spray` fixture, and focused tests.
* Add supported concentration, higher-level text, effects, damage, conditions, saving throws, and roll-table structures.
* Do not duplicate text or invent mechanics not established by the source.
* Validation: Spell schema validation and spell round-trip test.

#### Chunk 11 Verification Note

Completed 2026-09-10. The spell adaptor now extracts the established Prismatic
Spray d8 table, including damage rays, saving-throw abilities, restrained and
blinded conditions, and descriptive special outcomes while retaining the full
source description. The normalized result passes the Spell root schema.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -v` — 4 passed, 1 subtest passed.

### Chunk 12: Complete Spell Models

* Scope: spell model module and spell model tests.
* Create typed Pydantic models from validated JSON fixtures.
* Confirm model dumps remain valid against the Spell schema.
* Validation: focused spell model test.

#### Chunk 12 Verification Note

Completed 2026-09-10. Added typed `Spell`, `CastingTime`, and
`MaterialComponent` models and reused the shared target, effect, roll-table,
source, grant, and duration models. Actual `Cure Wounds` and `Prismatic Spray`
adaptations construct successfully and their JSON dumps remain valid against
the Spell root schema.

Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -v` — 5 passed, 3 subtests passed.

#### Ordinary Spell Damage Verification Note

Extended the shared damage extraction to support ordinary spell wording such
as `8d6 lightning damage`, not only monster-style `8 (8d6) fire damage` text.
Spell adaptation now emits schema-valid `effects` for damage spells, including
saving-throw failure and halved-success results and multiple damage types in a
single spell such as Ice Storm. The original spell description remains intact.

Validation passed:

* Lightning Bolt: Dexterity save, 8d6 lightning damage, halved success damage.
* Ice Storm: bludgeoning and cold damage effects.
* Full XML dispatch: 4,635 successful records, zero failures.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 84 passed, 26 subtests passed.

#### Cross-Entity Effect Coverage Note

Audited effect-like descriptions across spells, monsters, classes, and
subclasses. Ordinary spell damage now uses structured `Spell.effects`, while
monster actions already derive structured targets and effects through the
shared `Action` model. Extended the reusable `Feature` component and schema
with optional `effects`, and populate it for class, subclass, and monster
features when the shared effect parser recognizes a mechanic. Descriptions
remain preserved for unsupported or ambiguous wording.

Validation passed:

* Full XML dispatch — 4,635 successful records, zero failures.
* 480 class, subclass, and monster features contain structured effects.
* 4,689 monster/creature actions contain structured effects.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 85 passed, 26 subtests passed.

### Chunk 13: Implement Race Import

* Scope: race parser/adaptor, race fixtures, and focused tests.
* Handle size, speed, ability increases, subtype, proficiencies, languages, senses, spell grants, and traits.
* Preserve nested `special` and `modifier` content.
* Validation: Race schema and round-trip tests.

#### Chunk 13 Verification Note

Implemented the raw race parser, adaptor, typed model, and source-backed tests.
Race names with parenthesized or comma-separated subtypes are split into
`name` and `subtype`; size, walking speed, ability increases, skill
proficiencies, common named languages, darkvision, High Elf cantrip choices,
casting ability, traits, source text, and nested `special`/`modifier` content
are preserved or normalized where the schema supports them. Free-choice prose
remains in feature descriptions rather than being converted into invented
fixed values.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_race_parser.py -v` — 3 passed.
* Dragonborn (Black), Custom Lineage, High Elf, and a synthetic nested-content
	record pass Pydantic construction and `Race.schema.json` validation.

The next task is Chunk 14, feat import.

### Chunk 14: Implement Feat Import

* Scope: feat parser/adaptor, feat fixtures, and focused tests.
* Handle prerequisites, ability choices, proficiencies, spell grants, actions, modifiers, and full descriptions.
* Use the existing Fey Touched fixture as a reference where applicable.
* Validation: Feat schema and round-trip tests.

#### Chunk 14 Verification Note

Implemented the raw feat parser, adaptor, typed model, and source-backed tests.
The adaptor preserves full variant names, prerequisites, descriptions, source
text, and modifier data, and normalizes ability-score modifiers. Fey Touched
spell grants are represented as one guaranteed `misty step` grant plus one
level-one divination/enchantment choice with one long-rest use and the
source-derived casting ability. Saving-throw proficiency and other mechanics
without a corresponding Feat schema field remain in the preserved description.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_feat_parser.py -v` — 3 passed.
* Fey Touched (Intelligence) and Resilient (Constitution) pass Pydantic
	construction and `Feat.schema.json` validation.

The next task is Chunk 15, background import.

### Chunk 15: Implement Background Import

* Scope: background parser/adaptor, background fixtures, and focused tests.
* Handle proficiencies, languages, repeated traits, feature descriptions, and equipment text.
* Do not convert ambiguous equipment prose into invented item objects.
* Validation: Background schema and round-trip tests.

#### Chunk 15 Verification Note

Implemented the raw background parser, adaptor, typed model, and source-backed
tests. Skill and tool proficiencies are normalized from direct and descriptive
source values, `Feature:` traits become typed features, descriptions and source
metadata are preserved, and equipment/language choice prose remains
descriptive because the XML does not provide reliable concrete item or choice
records.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_background_parser.py -v` — 2 passed.
* Acolyte and Charlatan pass Pydantic construction and `Background.schema.json`
	validation.

The next task is Chunk 16, class base fields.

### Chunk 16: Implement Class Base Fields

* Scope: class parser/adaptor and focused tests.
* Normalize name, hit die, primary abilities, saving throws, armor/weapons/tools, skill choices, spell ability, and wealth where supported.
* Preserve class description and source values.
* Validation: focused class base-field test.

#### Chunk 16 Verification Note

Implemented raw class base-field parsing, normalization, typed models, and
source-backed tests. Hit dice, class name, primary abilities, saving throws,
armor, weapons, tools, skill choices, and known spellcasting ability and
progression are normalized against the existing Class schema. `autolevel`
records, features, slots, counters, and score-improvement attributes remain
preserved only by the generic XML parser for Chunk 17 analysis.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_class_parser.py -v` — 2 passed.
* Barbarian and Cleric pass Pydantic construction and `Class.schema.json`
	validation.

The next task is Chunk 17, class level progression.

### Chunk 17: Implement Class Level Progression

* Scope: class progression structures, models, and tests.
* Preserve every `autolevel`, its `level`, `scoreImprovement`, features, slots, and counters.
* First determine whether the existing Class schema can represent this data; document a genuine gap before changing anything.
* Validation: representative class fixture validation and progression round-trip test.

#### Chunk 17 Verification Note

Inspected the authoritative Class schema and source `autolevel` records. The
existing `class_progression` component represents a character's current class
and level, not a catalog class's level-indexed features, slots, counters, and
score-improvement metadata. Added raw preservation of every `autolevel`, its
attributes, and recursively nested children in `class_parser.py`, with source
tests covering level attributes, slots, and score improvements. No normalized
Class-schema representation was invented and no schema was weakened.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_class_parser.py -v` — 3 passed.

Known schema gap: the source progression cannot currently be serialized as a
valid `Class.schema.json` object without discarding or misrepresenting source
data. The next task is Chunk 18, subclass and schema boundaries.

### Chunk 18: Resolve Subclass and Schema Boundaries

* Scope: coverage matrix, relevant schema/model tests, and only a justified schema/component change.
* Confirm whether subclass data has a reliable source boundary.
* Do not create Subclass records from text that cannot be separated confidently.
* Validation: schema tests for any changed or newly covered structure.

#### Chunk 18 Verification Note

Inspected `Subclass.schema.json`, the complete XML inventory, all class child
tags, and class feature names. The source contains zero top-level `subclass`
records, but subclass ownership is reliably encoded by class-specific selector
labels and repeated subclass names in optional feature names. Added a typed
`Subclass` model and extraction through the existing class adaptor. Explicit
markers are supported in both parenthetical names such as `Feature (College of
Lore)` and selector-prefixed names such as `Bard College: College of Lore`.
Unqualified optional features remain on the parent class and are not assigned
to a subclass. Ownership matching is restricted to explicit parenthetical
markers or an owner followed by a colon, preventing similarly named subclasses
from receiving each other's features. For example, Rogue's `Spellcasting
(Arcane Trickster)` remains on Arcane Trickster and is not assigned to Thief.
Subclass-owned features are emitted only in `Subclass` records; they are not
added to the base `Class` object. Optional feature text that is class-wide or
cannot be assigned confidently is preserved in the normalized `Class.description`
instead of being dropped from the normalized record.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_class_parser.py tests/test_dispatcher.py -q` — 8 passed.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 83 passed, 26 subtests passed.
* Full XML dispatch — 4,635 successful records, including 129 subclasses;
	zero failures and zero unsupported records.
* Class description coverage — 15 of 16 class records contain preserved
	optional-feature descriptions; the remaining sidekick class has no such
	source text.

The next task is Chunk 19, creature edge cases.

### Chunk 19: Audit Creature Edge Cases

* Scope: existing creature parser/adaptor/models and focused tests.
* Cover reactions, legendary actions, spellcasting, slots, environments, senses, roll tables, nested attacks, and unusual defenses.
* Resolve invalid or compound values at the normalization boundary without weakening enums.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_monster_parser.py -v`.

#### Chunk 19 Verification Note

Audited the existing creature parser/adaptor against the full XML inventory and
found that the schema-supported `<reaction>` records were being dropped. Added
reaction extraction and adaptation through the existing action model path, with
source-backed Bandit Captain coverage and Creature schema validation. Existing
legendary actions, nested attacks, roll tables, senses, environments, and
defense normalization remain covered by the prior monster tests. Compound
source values such as `humanoid (any race)` and `any non-lawful alignment` are
normalized to the closest authoritative schema values without inventing enum
members.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_monster_parser.py -v` — 6 passed.

The next task is Chunk 20, the import dispatcher.

### Chunk 20: Build the Import Dispatcher

* Scope: one dispatcher module and focused dispatcher tests.
* Route each supported top-level XML tag to its parser, adaptor, and Pydantic model.
* Report unsupported entities and record-level failures without hiding them.
* Validation: dispatcher test over a small representative XML sample.

#### Chunk 20 Verification Note

Added a dispatcher for item, monster, spell, race, feat, background, and class
records. Each supported record is routed through its raw parser and adaptor,
validated with its Pydantic model, serialized in JSON mode, and checked against
its authoritative root schema. Unsupported tags return an explicit report with
the tag and record name instead of being hidden.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_dispatcher.py -v` — 1 passed.

The next task is Chunk 21, full-file batch validation.

### Chunk 21: Add Full-File Batch Validation

* Scope: batch importer and batch tests.
* Process all 4,507 records in `5eFile.xml` and produce an explicit success/review report.
* Validate serialized output against each entity's root schema.
* Do not require unsupported mechanics to pass silently.
* Validation: full batch test using the project-local Python interpreter.

#### Chunk 21 Verification Note

Extended dispatcher root processing to continue across record-level parser,
model, and schema failures, returning explicit `failed` results with record
names and error text. The representative failure-continuation test passes.
Full-file batch execution is the remaining validation for this chunk; its
report must distinguish successful records, unsupported tags, and failed
records rather than treating any non-success as silently accepted.

Full-file validation rerun after failure-reduction fixes:

* 4,507 records processed.
* 4,500 records succeeded.
* 7 records returned explicit failures.
* No unsupported top-level tags were present.

The completed failure-reduction fixes cover fractional and missing monster
challenge ratings, zero-valued ability scores, free-form alignments, infernal
vehicle creature descriptions, swarm creature extraction, malformed sense and
slot parsing, mile-based spell ranges, `d7` dice, unsupported `d3` item
recharge dice, and a non-numeric item bonus modifier. The remaining 7
failures are spells; no monster, item, or ability records currently fail.
These remain visible in the batch report rather than being silently coerced.

### Chunk 22: Route Customizable Abilities

* Scope: ability schema/model, spell-shaped ability routing, and focused tests.
* Route explicit maneuvers, eldritch invocations, artificer infusions, monk
	techniques, and Arcane Archer abilities to the Ability entity without
	weakening the Spell schema.
* Preserve descriptions, prerequisites, source, classes, and source level.
* Validation: ability/dispatcher tests, full-file batch, and project suite.

#### Chunk 22 Verification Note

Added `Ability.schema.json`, the typed Ability model, raw parser reuse,
normalization, and dispatcher routing for source records marked as eldritch
invocations, artificer infusions, Battle Master/Martial Adept maneuvers, monk
techniques, and Arcane Archer abilities. The full batch now produces 118
successful Ability records and leaves only 16 genuine or incomplete Spell
records for later review.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_ability_parser.py tests/test_dispatcher.py -q` — 4 passed.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 72 passed, 23 subtests passed.

### Chunk 23: Extend Spell Target Modes

* Scope: target schema, spell adaptor, and focused tests.
* Support source target values `Special`, `Sight`, and `Unlimited` without
	representing them as numeric distances.
* Validation: focused spell tests and full-file batch validation.

#### Chunk 23 Verification Note

Added `special`, `sight`, and `unlimited` target modes to the shared target
schema and spell normalization. All ten previously failing non-distance target
records now validate.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -q` — 7 passed, 6 subtests passed.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 73 passed, 26 subtests passed.

The batch now has 4,500 successes and 7 remaining spell failures.

#### Chunk 23 Follow-up Verification Note

Extended casting-time normalization to support either one casting-time object
or a list of alternatives such as `1 action or 8 hours`. Descriptive reaction
triggers remain in the source-preserved spell description while their leading
casting unit is normalized as `reaction`. Alternative splitting is limited to
actual time units so prose such as `lightning, or thunder damage` is preserved.
Duplicate spell class names are removed while preserving source order.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_spell_parser.py -q` — 8 passed, 6 subtests passed.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 74 passed, 26 subtests passed.
* Full-file validation processed 4,507 records: 4,506 succeeded and one
	incomplete source record remains (`Otiluke's freezing sphere`).

The remaining record has no source values for required Spell fields and is not
filled with invented data.

#### Component Model Coverage Verification Note

Added typed Pydantic counterparts for the previously unrepresented component
schemas: ability-score choices, class progression, effect results, spell
filters, spell choices, spell grants, spell slots, and weapon proficiencies.
Feat, Race, and Class weapon/spell-grant fields now use those typed models
instead of untyped dictionaries or strings.

Validation passed:

* `.\\.venv\\Scripts\\python.exe -m pytest tests/test_component_models.py -q` — 6 passed.
* `.\\.venv\\Scripts\\python.exe -m pytest -q` — 80 passed, 26 subtests passed.
* Full-file validation processed 4,506 records: 4,506 succeeded, with zero
	failures and zero unsupported records.

### Chunk 24: Final Review and Cleanup

* Scope: no new feature work; documentation and tests needed to close known gaps.
* Review the complete diff, unsupported-mechanics report, schema changes, and test results.
* Remove only demonstrably redundant code or documentation.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest -q` and `git diff --check`.

For every chunk, the worker must report changed files, tests run, failures, unsupported mechanics, and the exact next chunk. The reviewer may return a chunk with `changes requested`; the worker must resolve that chunk before continuing.

## 1. XML Source Parser

Create the smallest reusable XML parsing/extraction layer required to work with the supplied D&D 5e XML source.

### XML Inventory

* [x] Count every top-level entity in `5eFile.xml`.
* [x] Record the direct child tags for each entity type.
* [x] Record optional, repeated, empty, and ordered elements.
* [x] Record XML attributes and nested child structures.
* [x] Select simple, moderate, and complex representatives for each entity type.
* [x] Confirm whether separate top-level Weapon, Equipment, or Subclass records exist.
* [x] Document the inventory and any source structures that need manual review.

### Acceptance Criteria

* [ ] Implement a focused, reusable XML extraction layer.
* [ ] Add tests covering the parser's important behaviour.
* [ ] Relevant tests pass.
* [ ] No unrelated project architecture is changed.

Do not build a generalized XML framework beyond what the actual source format requires.

### Shared Extraction Requirements

* [x] Preserve element names, attributes, source order, repeated elements, empty elements, and all text nodes.
* [x] Preserve nested structures such as `attack`, `modifier`, `roll`, `slots`, and class level data.
* [x] Add reusable extraction helpers only where multiple entity parsers need the same behavior.
* [x] Keep schema-specific normalization out of the low-level parser.

## 2. XML Coverage Matrix

Create a field-by-field mapping from the XML source to the authoritative schemas before implementing each entity adaptor.

* [x] Record the XML entity and tag.
* [x] Record representative source values.
* [x] Identify the target schema field and normalization rule.
* [x] Identify the reusable component, enum, or model used by the mapping.
* [x] Mark whether structured mechanics can be extracted reliably.
* [x] Mark when the original source text must also be preserved.
* [x] Record ambiguous values and unsupported mechanics explicitly.
* [x] Identify genuine schema gaps without weakening existing schemas.

The matrix must distinguish between data that can be structured, data that must remain descriptive, ambiguous source data, and data blocked by a schema limitation.

## Entity Implementation Workflow

Apply these steps once to every entity-specific parser, adaptor, model, and fixture set. Entity sections below contain only additional requirements for that source type.

* [ ] Inspect existing schemas, shared components, models, and tests before implementation.
* [ ] Select a small, diverse set of simple, moderate, and complex XML representatives.
* [ ] Implement the raw entity parser without schema-specific interpretation.
* [ ] Implement the adaptor using the coverage matrix and existing schema components.
* [ ] Preserve useful source descriptions and unsupported mechanics.
* [ ] Generate normalized JSON fixtures using existing test-data conventions.
* [ ] Validate every source-derived fixture against its root schema.
* [ ] Identify schema capabilities not exercised by source fixtures.
* [ ] Add only targeted, plausible synthetic fixtures for those capabilities.
* [ ] Validate every synthetic fixture.
* [ ] Create or update typed Pydantic models using shared models.
* [ ] Add model construction and round-trip tests using JSON fixtures.
* [ ] Confirm round-tripped output remains schema-valid.
* [ ] Run the narrow relevant tests before moving to the next entity.

## 3. Creature

### Completeness Audit

* [ ] Test reactions and legendary actions.
* [ ] Test spellcasting, spell slots, environments, senses, and roll tables.
* [ ] Test nested attacks and effects.
* [ ] Test unusual alignment and damage immunity/resistance values.
* [ ] Decide how invalid or compound source values are preserved without inventing enum values.

## 4. Spell

* [ ] Select a simple spell such as `Cure Wounds`.
* [ ] Select a moderate spell with optional components, concentration, or higher-level text.
* [ ] Select `Prismatic Spray` as a complex spell representative.
* [ ] Preserve all description paragraphs and higher-level text.
* [ ] Extract casting time, range, components, material, duration, and concentration.
* [ ] Extract effects, saving throws, damage, conditions, and roll tables where supported.
* [ ] Identify uncovered Spell schema capabilities before creating synthetic fixtures.

## 5. Race

* [ ] Select representatives covering size, speed, ability increases, proficiencies, languages, senses, spell grants, and traits.
* [ ] Cover subtype or subrace naming where present.
* [ ] Preserve traits containing nested `special` or `modifier` structures.

## 6. Feat

* [ ] Select representatives covering prerequisites, ability score choices, proficiencies, spell grants, actions, and multiple text paragraphs.
* [ ] Normalize supported modifiers without inferring unsupported mechanics.
* [ ] Preserve the complete feat description.

## 7. Background

* [ ] Select representatives covering skill, tool, and language proficiencies.
* [ ] Parse repeated background traits and all nested text nodes.
* [ ] Map supported feature and equipment data into the Background schema.
* [ ] Preserve equipment and feature text when it cannot be represented structurally.

## 8. Item

Generalize the existing Wand-specific adaptor into category-specific normalization built on shared raw item data.

* [ ] Select representatives for mundane gear, weapons, ammunition, armor, shields, potions, scrolls, rods, staffs, wands, and other magic items.
* [ ] Cover weight, cost, value, damage, versatile damage, range, properties, strength, stealth, modifiers, rolls, charges, and spell uses.
* [ ] Separate generic item extraction from weapon, armor, and magic-item adaptation.
* [ ] Preserve descriptions when mechanics cannot be represented reliably.
* [ ] Generalize defensive parsing for missing, unusual, and nonnumeric source values.
* [ ] Identify whether XML item records should also produce `Weapon` or `Equipment` models.

## 9. Class and Subclass

* [ ] Select class representatives covering hit dice, primary abilities, saving throws, proficiencies, skill choices, spellcasting, wealth, and level progression.
* [ ] Parse every `autolevel` and preserve its level and attributes.
* [ ] Parse level features, spell slots, counters, and score-improvement metadata.
* [ ] Determine whether the Class schema can represent level-indexed progression without flattening or discarding source data.
* [ ] Identify and document any genuine class-progression schema gap.
* [ ] Confirm whether subclass data is embedded in class features or absent from the XML.
* [ ] Do not create Subclass records unless a reliable source boundary exists.

## 10. Import Dispatcher and Batch Processing

Create one orchestration path for the complete XML file after the individual pipelines are available.

* [ ] Dispatch each supported top-level XML tag to its raw parser and adaptor.
* [ ] Validate normalized data with the corresponding Pydantic model.
* [ ] Serialize models using JSON-compatible output.
* [ ] Validate serialized output against the authoritative root schema.
* [ ] Process every record in `5eFile.xml`.
* [ ] Report unsupported entity types, failed records, invalid values, ambiguous mechanics, and schema failures with record names.
* [ ] Ensure unsupported source information is preserved or explicitly reported rather than silently discarded.
* [ ] Add a full-file batch import test.

## Final Verification

* [ ] Every top-level XML entity type has a dispatcher path.
* [ ] All selected entity types have representative fixtures.
* [ ] All fixtures pass JSON Schema validation.
* [ ] Synthetic fixtures cover meaningful schema capabilities.
* [ ] Pydantic models cover represented structures.
* [ ] Pydantic round-trips remain schema-valid.
* [ ] The full XML file produces an explicit success and review report.
* [ ] Unsupported and ambiguous mechanics are documented.
* [ ] No bundled generated schemas are edited.
* [ ] Relevant tests pass.
* [ ] No unnecessary unrelated changes were introduced.

Run the relevant targeted tests first, then the complete suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
