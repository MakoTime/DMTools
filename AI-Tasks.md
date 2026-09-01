# AI Tasks

Tasks are completed in order unless the user explicitly changes the scope.

The rules and development methodology for all tasks are defined in `AGENTS.md`.

## Qwen3 Execution Chunks

Give the local agent one chunk at a time. Do not combine adjacent chunks unless the assigned chunk explicitly requires it. Each chunk should end with a focused test run and an update to `agent-handoff.md`.

### Chunk 0: Establish the Handoff

* Scope: `agent-handoff.md` only.
* Record the assigned chunk, allowed files, acceptance criteria, and validation command.
* Do not modify implementation files.
* Validation: `git diff --check -- agent-handoff.md`.

### Chunk 1: Verify the XML Inventory

* Scope: read-only inspection plus an inventory note if needed.
* Count top-level records and record direct child tags, attributes, nesting, and representative names.
* Confirm whether top-level `weapon`, `equipment`, and `subclass` records exist.
* Do not implement entity parsing.
* Validation: rerun the inventory command and compare the recorded counts.

### Chunk 2: Lock Down Generic XML Behavior

* Scope: `parsers/xml_parser.py` and `tests/test_xml_parser.py`.
* Verify or implement preservation of attributes, repeated elements, empty elements, ordering, text, and nested children.
* Do not add schema-specific normalization.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_xml_parser.py -v`.

### Chunk 3: Create the XML Coverage Matrix

* Scope: coverage documentation or a narrowly scoped data file selected after inspection.
* Map each entity tag to a schema field, normalization rule, preserved text, or explicit gap.
* Do not modify schemas or models in this chunk.
* Validation: inspect every top-level XML entity type and every direct child tag against the matrix.

### Chunk 4: Generalize Item Source Parsing

* Scope: `parsers/item_parser.py` and its focused tests.
* Ensure raw item parsing preserves all category-dependent fields, repeated text, modifiers, rolls, and attributes.
* Do not normalize items or change Pydantic models yet.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_item_parser.py -v`.

### Chunk 5: Adapt Basic Items

* Scope: `parsers/item_adaptor.py` and one or two basic item fixtures/tests.
* Normalize name, category, weight, cost/value, description, and source for nonmagical items.
* Preserve unsupported mechanics as text.
* Validation: focused basic-item adaptor test plus schema validation.

### Chunk 6: Adapt Weapons and Armor

* Scope: item adaptor/model tests and only the files required by the existing item hierarchy.
* Handle damage, versatile damage, range, properties, armor class, stealth, and strength where the schemas support them.
* Use actual XML representatives before adding parsing rules.
* Validation: focused weapon/armor tests and root-schema validation.

### Chunk 7: Adapt Magic Items

* Scope: `parsers/item_adaptor.py`, item fixtures, and focused tests.
* Generalize the existing Wand-specific logic for rarity, attunement, bonuses, charges, spells, and features.
* Keep malformed or ambiguous source values descriptive rather than fabricating values.
* Validation: item parser/model tests and Item schema validation.

### Chunk 8: Complete Item Models

* Scope: `models/item.py` and item model tests only.
* Align typed models with the normalized Item, Weapon, Armor, MagicItem, and Equipment structures actually produced.
* Do not redesign schemas.
* Validation: item construction and round-trip tests.

### Chunk 9: Implement Spell Raw Parsing

* Scope: new spell parser module and focused parser tests.
* Preserve spell fields, repeated text, optional values, and explicit `roll` elements.
* Use `Cure Wounds` and `Prismatic Spray` as source representatives.
* Do not extract effects into schema structures yet.
* Validation: focused spell raw-parser tests.

### Chunk 10: Adapt Basic Spells

* Scope: spell adaptor and one simple spell fixture/test.
* Normalize name, level, school, casting time, range, components, duration, ritual, classes, and description.
* Preserve all source paragraphs.
* Validation: Spell schema validation and focused adaptor test.

### Chunk 11: Adapt Complex Spell Mechanics

* Scope: spell adaptor, `Prismatic Spray` fixture, and focused tests.
* Add supported concentration, higher-level text, effects, damage, conditions, saving throws, and roll-table structures.
* Do not duplicate text or invent mechanics not established by the source.
* Validation: Spell schema validation and spell round-trip test.

### Chunk 12: Complete Spell Models

* Scope: spell model module and spell model tests.
* Create typed Pydantic models from validated JSON fixtures.
* Confirm model dumps remain valid against the Spell schema.
* Validation: focused spell model test.

### Chunk 13: Implement Race Import

* Scope: race parser/adaptor, race fixtures, and focused tests.
* Handle size, speed, ability increases, subtype, proficiencies, languages, senses, spell grants, and traits.
* Preserve nested `special` and `modifier` content.
* Validation: Race schema and round-trip tests.

### Chunk 14: Implement Feat Import

* Scope: feat parser/adaptor, feat fixtures, and focused tests.
* Handle prerequisites, ability choices, proficiencies, spell grants, actions, modifiers, and full descriptions.
* Use the existing Fey Touched fixture as a reference where applicable.
* Validation: Feat schema and round-trip tests.

### Chunk 15: Implement Background Import

* Scope: background parser/adaptor, background fixtures, and focused tests.
* Handle proficiencies, languages, repeated traits, feature descriptions, and equipment text.
* Do not convert ambiguous equipment prose into invented item objects.
* Validation: Background schema and round-trip tests.

### Chunk 16: Implement Class Base Fields

* Scope: class parser/adaptor and focused tests.
* Normalize name, hit die, primary abilities, saving throws, armor/weapons/tools, skill choices, spell ability, and wealth where supported.
* Preserve class description and source values.
* Validation: focused class base-field test.

### Chunk 17: Implement Class Level Progression

* Scope: class progression structures, models, and tests.
* Preserve every `autolevel`, its `level`, `scoreImprovement`, features, slots, and counters.
* First determine whether the existing Class schema can represent this data; document a genuine gap before changing anything.
* Validation: representative class fixture validation and progression round-trip test.

### Chunk 18: Resolve Subclass and Schema Boundaries

* Scope: coverage matrix, relevant schema/model tests, and only a justified schema/component change.
* Confirm whether subclass data has a reliable source boundary.
* Do not create Subclass records from text that cannot be separated confidently.
* Validation: schema tests for any changed or newly covered structure.

### Chunk 19: Audit Creature Edge Cases

* Scope: existing creature parser/adaptor/models and focused tests.
* Cover reactions, legendary actions, spellcasting, slots, environments, senses, roll tables, nested attacks, and unusual defenses.
* Resolve invalid or compound values at the normalization boundary without weakening enums.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest tests/test_monster_parser.py -v`.

### Chunk 20: Build the Import Dispatcher

* Scope: one dispatcher module and focused dispatcher tests.
* Route each supported top-level XML tag to its parser, adaptor, and Pydantic model.
* Report unsupported entities and record-level failures without hiding them.
* Validation: dispatcher test over a small representative XML sample.

### Chunk 21: Add Full-File Batch Validation

* Scope: batch importer and batch tests.
* Process all 4,507 records in `5eFile.xml` and produce an explicit success/review report.
* Validate serialized output against each entity's root schema.
* Do not require unsupported mechanics to pass silently.
* Validation: full batch test using the project-local Python interpreter.

### Chunk 22: Final Review and Cleanup

* Scope: no new feature work; documentation and tests needed to close known gaps.
* Review the complete diff, unsupported-mechanics report, schema changes, and test results.
* Remove only demonstrably redundant code or documentation.
* Validation: `.\\.venv\\Scripts\\python.exe -m pytest -q` and `git diff --check`.

For every chunk, the worker must report changed files, tests run, failures, unsupported mechanics, and the exact next chunk. The reviewer may return a chunk with `changes requested`; the worker must resolve that chunk before continuing.

## 1. XML Source Parser

Create the smallest reusable XML parsing/extraction layer required to work with the supplied D&D 5e XML source.

### XML Inventory

* [ ] Count every top-level entity in `5eFile.xml`.
* [ ] Record the direct child tags for each entity type.
* [ ] Record optional, repeated, empty, and ordered elements.
* [ ] Record XML attributes and nested child structures.
* [ ] Select simple, moderate, and complex representatives for each entity type.
* [ ] Confirm whether separate top-level Weapon, Equipment, or Subclass records exist.
* [ ] Document the inventory and any source structures that need manual review.

### Acceptance Criteria

* [ ] Implement a focused, reusable XML extraction layer.
* [ ] Add tests covering the parser's important behaviour.
* [ ] Relevant tests pass.
* [ ] No unrelated project architecture is changed.

Do not build a generalized XML framework beyond what the actual source format requires.

### Shared Extraction Requirements

* [ ] Preserve element names, attributes, source order, repeated elements, empty elements, and all text nodes.
* [ ] Preserve nested structures such as `attack`, `modifier`, `roll`, `slots`, and class level data.
* [ ] Add reusable extraction helpers only where multiple entity parsers need the same behavior.
* [ ] Keep schema-specific normalization out of the low-level parser.

## 2. XML Coverage Matrix

Create a field-by-field mapping from the XML source to the authoritative schemas before implementing each entity adaptor.

* [ ] Record the XML entity and tag.
* [ ] Record representative source values.
* [ ] Identify the target schema field and normalization rule.
* [ ] Identify the reusable component, enum, or model used by the mapping.
* [ ] Mark whether structured mechanics can be extracted reliably.
* [ ] Mark when the original source text must also be preserved.
* [ ] Record ambiguous values and unsupported mechanics explicitly.
* [ ] Identify genuine schema gaps without weakening existing schemas.

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
