# API/XML Core Parity Audit

The repeatable comparison runner is `python -m tools.api_xml_parity`. It loads XML through `EntityImportService.preview_xml`, adapts API payloads through `SRDAdaptor`, validates both sides through `ENTITY_REGISTRY`, and compares model dumps for the declared shared core.

## Usage

Use the checked-in representative API records when network access is unavailable:

```text
python -m tools.api_xml_parity --xml 5eFile.xml --api-json tests/data/api_xml_parity_cases.json
```

Use the live SRD client for stable records:

```text
python -m tools.api_xml_parity --xml 5eFile.xml --live monsters:aboleth --case monster:Aboleth
```

API fixture entries have this shape:

```json
[{"collection": "equipment", "payload": {"name": "Backpack"}}]
```

The report includes the entity type, name, canonical field, both normalized values, source field paths, Pydantic model, JSON schema, and one of `equal`, `source-only`, `missing`, `shape-mismatch`, `normalization-mismatch`, `hydration-mismatch`, or `value-mismatch`. A nonzero exit status means an unexplained comparison result remains.

## Canonical contracts

| Entity | Model | Schema | Shared core |
| --- | --- | --- | --- |
| Monster | `Monster` | `Monster.schema.json` | identity, abilities, movement, features/actions, challenge |
| Spell | `Spell` | `Spell.schema.json` | level, school, classes, casting, components, duration, effects |
| Class | `Class` | `Class.schema.json` | hit die, proficiencies, choices, spellcasting, features, progression |
| Race | `Race` | `Race.schema.json` | subtype, size, movement, bonuses, languages, traits, senses, grants |
| Background | `Background` | `Background.schema.json` | description, proficiencies, languages, features |
| Feat | `Feat` | `Feat.schema.json` | description, prerequisites, bonuses, proficiencies, features |
| Item/equipment | `Item` | `Item.schema.json` | category, weight, cost, weapon/armor/magic data, features, description |
| Subclass | `Subclass` | `Subclass.schema.json` | parent class, description, features, spells, tags |

XML-only prose/citations and API-only URLs or structured metadata are preserved in their source records and are not parity failures. XML-present/API-absent shared values are reported as `missing`; XML-absent/API-present values are `source-only`.

Nested class and subclass levels are hydrated through `SRDClient.fetch_collection_resources`; race traits are replaced with their fetched bodies before adaptation. Hydrated feature references are replaced rather than merged so stale URL-only fields cannot contaminate the canonical payload.

## Completed representative run

The live 2014 SRD comparison was run through the real client and import validation path for Goblin, Fireball, Bard, Human, Acolyte, Grappler, and Backpack. All 65 compared shared-core fields were `equal`. The requested `College of Lore` subclass is not exposed by the live 2014 API collection; subclass coverage therefore uses deterministic nested-resource fixtures, including level and feature hydration. No value was invented for the unavailable live record.
