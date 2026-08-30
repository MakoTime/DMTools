# AI Tasks

Tasks are completed in order unless the user explicitly changes the scope.

The rules and development methodology for all tasks are defined in `AGENTS.md`.

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
