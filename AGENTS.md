# Schema Data Agent

## Mission

Convert D&D 5e XML source data in:

`5eFile.xml`

into:

1. Schema-valid JSON fixtures.
2. Additional synthetic fixtures that exercise schema capabilities.
3. Pydantic models capable of constructing and validating those objects.
4. Tests covering schema validation and Pydantic round-tripping.

The existing JSON Schemas define the normalized data model. The XML provides the source data.

Do not redesign the data model unless a genuine schema gap is discovered.

## Repository Map

Repository root:

`C:\Users\benve\Documents\Programming\DMTools`

Verified project structure:

```text
DMTools/
│
├── 5eFile.xml
├── Ai-Tasks.md
├── main.py
├── menu.py
├── requirements.txt
├── application/
│   ├── database_service.py
│   ├── file_window.py
│   ├── project_controller.py
│   ├── project_serializer.py
│   ├── project_version.py
│   ├── sql_import.py
│   └── controllers/db_controller.py
├── components/
│   ├── database/objects/object_base.py
│   └── tree/{model.py,search.py,view.py}
├── dialog/
│   ├── base/{editor,popup_editor,tab_editor,widget_editor}/
│   ├── database/{factory.py,model.py,view.py}
│   ├── db_base/{factory.py,model.py,view.py}
│   └── notify/{factory.py,model.py,view.py,notify.ui}
├── models/
│   ├── common.py
│   ├── components.py
│   ├── item.py
│   ├── monster.py
│   └── search_strings.py
├── objects/
│   └── Database, JSON, query, shopkeeper, and table objects
├── parsers/
│   ├── item_adaptor.py
│   ├── item_parser.py
│   ├── monster_adaptor.py
│   ├── monster_parser.py
│   └── xml_parser.py
├── schemas/
│   ├── entities/
│   │   └── Entity-level JSON Schemas
│   │
│   ├── components/
│   │   └── Reusable JSON Schema components
│   │
│   ├── values/
│   │   └── Reusable values, enums, and constrained definitions
│   │
│   └── validator.py
│       └── Project JSON Schema validation utilities
│
└── tests/
    ├── test_*.py
    │   └── Parser, model, database, dialog, and schema tests
    │
    └── data/
        ├── schemas/entities/
        │   └── Schema and model fixtures
        └── xml_files/
            └── XML parser and source fixtures
```

### Authoritative Paths

| Purpose                  | Path                                                                 |
| ------------------------ | -------------------------------------------------------------------- |
| Repository root          | `C:\Users\benve\Documents\Programming\DMTools`                       |
| Entity schemas           | `schemas/entities/`                                                  |
| Shared schema components | `schemas/components/`                                                |
| Schema values/enums      | `schemas/values/`                                                    |
| Schema validator         | `schemas/validator.py`                                               |
| Schema tests             | `tests/test_schemas.py`                                              |
| Schema test data         | `tests/data/schemas/entities/`                                       |
| XML source               | `5eFile.xml` |

### Important

The map above contains only locations that have been verified.

Do not assume that an unlisted directory or file exists.

Before creating or modifying files:

1. Inspect the relevant directory.
2. Search for an existing equivalent.
3. Follow the existing project organization.
4. Only create a new file or directory when required by the project's existing architecture.

If a required project location is not listed here, inspect the repository rather than guessing.

## Current XML Inventory

The supplied `5eFile.xml` has a `compendium` root and 4,507 top-level records:

| XML tag | Record count |
|---|---:|
| `item` | 1,847 |
| `monster` | 1,492 |
| `spell` | 824 |
| `feat` | 130 |
| `race` | 104 |
| `background` | 94 |
| `class` | 16 |

There are no separate top-level `weapon`, `equipment`, or `subclass` records in the current source. Treat those as schema concepts until the XML inventory provides evidence otherwise.

Notable source structures:

* `monster` records contain nested `trait`, `action`, `reaction`, and `legendary` elements, along with attacks, spell slots, defenses, and environments.
* `spell` records contain repeated `text` elements and optional `roll` elements.
* `race` records contain repeated traits and occasional nested `special` or `modifier` elements.
* `background` records contain repeated traits with nested text nodes.
* `class` records contain `autolevel` elements with `level` and optional `scoreImprovement` attributes, plus nested features, slots, and counters.
* `item` records use category-dependent fields for damage, armor, modifiers, rolls, charges, properties, range, weight, and value.

Re-run the inventory after source changes rather than relying on these counts indefinitely.

## Application Architecture

The repository also contains a PySide6 application. Preserve its existing Model/View/Factory dialog pattern:

* Keep domain state and editable state in a model.
* Keep Qt layout and event handling in a view.
* Construct views through a factory that accepts the model.
* Embedded workspace editors inherit from `dialog/base/widget_editor/WidgetEditorView`.
* Modal editors use the popup base.
* Tab-hosted editors use the tab base.
* Prefer existing PySide6 and project patterns over a parallel UI architecture.
* Keep SQLite as the source of truth; use pandas only as a temporary display/editing layer.
* Treat external SQL or database files as import inputs and persist only the generated project-managed SQLite file under the project's `data` directory.

Do not mix Qt event handling, database persistence, XML parsing, and schema normalization into one class or module.

## XML Source and Import

The authoritative source data is:

`5eFile.xml`

The repository has a generic XML parser in `parsers/xml_parser.py` and source-specific Monster and Item parsing/adaptation in `parsers/`. A complete dispatcher and import pipeline for every top-level entity is still an explicit task in `Ai-Tasks.md`.

When XML parsing functionality is required:

* Inspect the XML structure directly before designing the parser.
* Do not assume the XML structure matches the JSON Schema structure.
* Keep XML parsing separate from schema-specific normalization where practical.
* Prefer a reusable parser/data-extraction layer over embedding XML parsing logic directly into fixture-generation code.
* Preserve source information during parsing.
* Do not discard XML information merely because the current schema does not represent it.
* Do not invent mechanics during parsing.
* Use the existing JSON Schemas as the authority for normalization.
* Add tests for important XML parsing behaviour.
* Keep the parser focused on the actual XML format present in the source file.
* Do not build a generalized XML framework when a small focused parser is sufficient.

### XML Parsing Development Order

When XML parsing is required:

1. Inspect representative sections of the XML.
2. Identify the XML structure used by the target entity.
3. Determine which information is structural and which is descriptive text.
4. Implement the smallest reusable parser necessary.
5. Add tests for the parser.
6. Extract representative source entities.
7. Normalize the extracted data against the existing JSON Schema.
8. Validate the resulting fixtures.
9. Only then proceed to Pydantic model generation.

The parser should answer:

> What does the XML say?

The normalizer should answer:

> How does our schema represent it?

Do not combine XML parsing, D&D interpretation, schema normalization, fixture generation, and Pydantic generation into one monolithic implementation when they can reasonably be separated.

## Development Commands

Do not assume commands. Inspect the repository's existing configuration and documentation to determine the correct commands.

The primary test framework is expected to be pytest, but the agent MUST verify the project's actual test configuration before relying on this assumption.

At minimum, determine:

* How to run the full test suite.
* How to run `tests/test_schemas.py`.
* How to run an individual test.
* Whether any project-specific pytest configuration or arguments are required.

Once verified, prefer targeted tests during development and the broader relevant suite before declaring a task complete.

## Autonomous Execution Rules

The agent operates incrementally.

* Do NOT attempt to process the entire repository in a single task.
* Do NOT attempt to process every entity type unless explicitly instructed.
* Work on ONE task at a time.
* Within an entity type, work on ONE coherent implementation unit at a time.
* Before modifying files, inspect the relevant existing implementation.
* After each meaningful change, run the most relevant tests.
* Do not continue to the next task until the current task satisfies its Definition of Done.
* If a decision is ambiguous and cannot be resolved from the repository, schema, or source XML, stop and report the ambiguity rather than guessing.
* The current user request defines the task scope.
* If no specific task is specified, use `Ai-Tasks.md` to determine the first incomplete task.
* Never claim a task is complete without running the relevant tests.

## Non-Negotiable Rules

### Existing schemas are authoritative

* MUST inspect the relevant schema before generating data.
* MUST inspect the relevant root schema and all directly referenced schemas before generating data.
* MUST inspect deeper referenced schemas when the selected fixture actually uses those structures.
* MUST search for existing shared components, schemas, models, and values before creating new ones.
* MUST reuse existing schemas and components whenever possible.
* MUST follow existing field names and conventions.
* MUST NOT recreate concepts that already exist elsewhere.
* MUST NOT rename existing concepts for stylistic reasons.
* MUST NOT weaken a schema simply to make generated data validate.

### Preserve source information

When XML contains descriptive text:

* MUST preserve the useful source description.
* Structured data supplements descriptions; it does not replace them.
* If a trait/action/feature contains both descriptive and mechanical information, preserve the original description while extracting the mechanical information separately.

Example:

```json
{
    "features": [
        {
            "name": "Keen Senses",
            "description": "You have proficiency in the Perception skill."
        }
    ],
    "skill_proficiencies": [
        "perception"
    ]
}
```

### Do not invent mechanics

* MUST NOT infer mechanics that cannot be determined confidently.
* MUST NOT fabricate numeric values.
* MUST NOT use placeholder values such as `0` merely to satisfy a schema.
* When a mechanic cannot currently be represented, preserve it in descriptive text.
* Only modify the schema when the missing structure represents a genuine reusable concept.

### Keep changes focused

* Do not modify unrelated schemas.
* Do not refactor working code unnecessarily.
* Prefer the smallest change that correctly represents the source data.
* Follow existing project architecture and coding style.

## Prohibited Behaviour

Unless explicitly required by the current task, DO NOT:

* Rewrite existing working models.
* Rename existing fields, classes, schemas, or fixtures.
* Reorganize directories.
* Replace the project's validation framework.
* Replace existing test infrastructure.
* Introduce new dependencies.
* Modify unrelated schemas.
* Modify unrelated entity types.
* Generate large numbers of fixtures.
* "Clean up" unrelated code.
* Change project architecture.
* Remove existing tests because they are inconvenient.
* Weaken validation to make a fixture pass.
* Change working behaviour merely for stylistic reasons.
* Build a generalized XML parsing framework when a focused parser is sufficient.

## Workflow

Always perform the following steps in order.

### 1. Inspect the project

Identify:

* JSON Schema location.
* Existing fixtures and test data.
* Existing schema tests.
* Pydantic model location, if present.
* Existing model tests, if present.
* XML-related utilities, if present.
* Existing shared components and values.

Determine which conventions the project already uses before creating anything.

Before modifying an existing file, inspect the relevant implementation and its tests.

Do not assume a component or model is missing until the repository has been searched.

### 2. Inventory the target schema

For the current entity type:

* Identify the root schema.
* Identify directly referenced schemas.
* Identify optional and required fields.
* Identify enums and custom-value patterns.
* Identify nested components.
* Identify conditional schemas.
* Identify reusable components already available.

Build the fixture from the actual current schema, not from assumptions.

Inspect deeper referenced schemas when the selected fixture requires them.

### 3. Select representative XML examples

From the supplied XML file, select a small representative sample for the current entity type.

Prefer examples that collectively exercise:

* Basic fields.
* Optional fields.
* Nested components.
* Conditional structures.
* Choices.
* Saving throws.
* Attacks.
* Effects.
* Roll tables.
* Charges.
* Spell grants.
* Proficiency grants.
* Other unusual or complex structures.

Prefer diversity over quantity.

A useful progression is:

```text
simple
→ moderately complex
→ structurally unusual
```

Do not select large numbers of nearly identical examples.

### 4. Normalize XML into JSON

Convert each selected XML entity into the project's normalized JSON format.

Use existing components whenever they apply.

Examples:

```text
<speed>
→ movement

<ability>
→ ability_score_increases

<proficiency>
→ skill_proficiencies / weapon_proficiencies / etc.

<hp>
→ hit_points + hit_dice

<attack>
→ attack/effect structure

<roll>
→ roll / roll_with_modifier

<text>
→ description / feature / effect
```

The exact mapping must come from the existing schemas.

Do not assume these mappings apply universally; inspect the relevant schema and existing fixtures first.

### 5. Extract mechanics where supported

When a description contains mechanics represented by existing schemas, populate those schemas in addition to preserving the description.

Examples:

```text
"Darkvision to 60 feet"
→ senses

"proficiency in Perception"
→ skill_proficiencies

"proficiency with longswords"
→ weapon_proficiencies

"+2 bonus to AC"
→ magic item bonus

"resistance to fire damage"
→ grant

"cast fireball using 1 charge"
→ spell charge
```

Do not duplicate the mechanical information unnecessarily.

### 6. Validate immediately

Every generated fixture MUST be validated against its root schema.

Do not proceed to Pydantic generation while the fixture is invalid unless the failure is caused by a known schema gap being addressed.

When validation fails, determine which layer is wrong:

```text
fixture
schema
referenced schema
$ref
$id
validation test
```

Fix the correct layer.

### 7. Add synthetic examples

After the XML-derived fixtures pass validation, create a small number of synthetic examples.

Synthetic examples exist to test schema functionality that the source XML does not cover.

Synthetic fixtures MUST:

* Represent plausible D&D 5e data.
* Use the existing schema model.
* Target an actual uncovered schema capability.
* Remain small and maintainable.

Do not generate synthetic examples merely to increase fixture count.

### 8. Pydantic models

Only begin model work after representative JSON fixtures validate successfully.

Before creating or modifying a Pydantic model:

1. Search for an existing model representing the same concept.
2. Inspect that model's tests.
3. Determine whether it can be reused.
4. Only create a new model when no suitable existing model exists.

Pydantic models MUST:

* Mirror the JSON Schema structure.
* Use the same field names.
* Reuse existing nested models.
* Use typed fields instead of unstructured dictionaries where practical.
* Use enums/literals where schemas define finite values.
* Represent optional fields as optional.
* Preserve nested structures.
* Avoid duplicating existing shared models.

### 9. Test and iterate

For each implementation unit:

1. Inspect.
2. Plan.
3. Make the smallest required change.
4. Run the most relevant tests.
5. Read the complete failure output.
6. Determine whether the failure is caused by implementation, fixture, schema, test, import/configuration, or environment.
7. Fix the appropriate layer.
8. Run the tests again.
9. Repeat until passing.
10. Only then continue to the next implementation unit.

Do not hide, ignore, disable, or weaken failing tests merely to obtain a passing result.

## Schema Gap Decision Process

When a source mechanic cannot be represented:

### Case 1 — Existing schema supports it

Normalize it using the existing schema.

### Case 2 — Existing schema does not support it, but description is sufficient

Preserve the mechanic in descriptive text.

Do not invent structure.

### Case 3 — Existing schema is missing a reusable concept

Add the smallest reusable schema/component necessary.

Before doing so:

1. Confirm that no existing component can represent it.
2. Determine whether the concept applies beyond the current example.
3. Prefer a reusable component over an entity-specific field.
4. Add a fixture demonstrating the new capability.
5. Add validation tests.

### Case 4 — Source text is ambiguous

Do not guess.

Preserve the source text and report the ambiguity.

## Entity Coverage

Current major entity types include:

```text
Creature
Spell
Race
Feat
Background
Item
Class
```

The current XML also contains `monster` records, which are adapted to the Creature/Monster schema hierarchy. The source currently contains 1,847 items, 1,492 monsters, 824 spells, 130 feats, 104 races, 94 backgrounds, and 16 classes.

The agent should not assume every XML file contains every entity type.

For each entity type explicitly selected for processing:

1. Select representative source examples.
2. Generate normalized JSON.
3. Validate it.
4. Add synthetic examples where useful.
5. Create/update Pydantic models.
6. Add tests.
7. Run the relevant test suite.
8. Complete the Definition of Done before moving to another entity type.

## Naming

Follow project conventions.

JSON fields and Python fields should normally use:

```text
snake_case
```

Fixture filenames should be descriptive and stable.

Do not rename existing fixtures without a reason.

## Output Expectations

At the end of a task, report:

```text
Task completed:

Files added:

Files modified:

Tests added:

Tests passing:

Schemas changed:

Pydantic models added/updated:

Known unsupported mechanics:

Known unresolved issues:
```

For unsupported mechanics, explain whether they were:

* intentionally preserved as description,
* ambiguous in the source,
* or blocked by a schema limitation.

Do not report an item as complete if the relevant tests have not passed.

## Definition of Done

A task is complete only when:

* The required implementation has been completed.
* Relevant tests have been added or updated.
* Relevant tests pass.
* No known failing tests have been ignored, disabled, or weakened.
* No unrelated schemas or models were unnecessarily changed.
* Any unsupported or ambiguous mechanics have been explicitly reported.
* The task's specific acceptance criteria in `Ai-Tasks.md` have been satisfied.

## Guiding Principle

The goal is not to extract every sentence into structured data.

The goal is:

> **Preserve the source faithfully while extracting structured mechanics wherever the existing data model can represent them accurately.**

Prefer:

```text
accurate structured data + preserved description
```

over:

```text
invented structured data + lost source information
```

When uncertain, preserve the source text rather than guessing.

## Development Commands

Run Python tests using the project's project-local Python interpreter:

```text
.\\.venv\\Scripts\\python.exe -m pytest
```

Do NOT use the standalone `pytest` command. Do not assume the system `python` points at the project environment.

This ensures pytest runs through the active Python environment and avoids relying on a separate pytest executable being available on `PATH`.

### Targeted Tests

During development, run the smallest relevant test set first.

For the XML parser:

```text
.\\.venv\\Scripts\\python.exe -m pytest tests/test_xml_parser.py -v
```

For schema tests:

```text
.\\.venv\\Scripts\\python.exe -m pytest tests/test_schemas.py -v
```

For a specific test:

```text
.\\.venv\\Scripts\\python.exe -m pytest tests/test_xml_parser.py::test_name -v
```

Before declaring a task complete, run the broader relevant test suite:

```text
.\\.venv\\Scripts\\python.exe -m pytest -v
```

### Test Failure Procedure

When a test fails:

1. Read the complete traceback.
2. Identify whether the failure is caused by:

   * implementation,
   * fixture,
   * schema,
   * test,
   * import/package configuration,
   * dependency/environment,
   * or an unrelated existing failure.
3. Fix the appropriate layer.
4. Rerun the failing targeted test.
5. Rerun the relevant broader tests.
6. Do not modify environment variables such as `PATH` or `PYTHONPATH` as a first-line workaround.
7. Do not disable or weaken a test to make it pass.

If an import failure occurs, inspect the repository's package structure and existing test configuration before changing imports or project configuration.

## Multi-Agent Handoff

This repository may be worked on by GitHub Copilot and a local Cline agent using Ollama. Agents share the working tree, but they do not share conversation history or task state.

Use `agent-handoff.md` as the task boundary when work is delegated between agents.

### Task Sender Responsibilities

The agent assigning work MUST record:

* A single, narrowly scoped task.
* The files or directories the worker may modify.
* Relevant acceptance criteria.
* Required tests or validation commands.
* Constraints, known issues, and decisions already made.

Do not assign overlapping tasks to multiple agents. Do not ask the worker to modify files currently being edited by another agent.

### Cline Worker Responsibilities

Before editing, Cline MUST:

1. Read `AGENTS.md`, `Ai-Tasks.md`, and `agent-handoff.md`.
2. Inspect the assigned code and nearby tests.
3. State the implementation approach in the handoff file.
4. Keep changes within the assigned scope.
5. Run the required focused tests after editing.
6. Record changed files, test results, blockers, and any follow-up recommendations.

Cline MUST NOT mark a task complete when tests fail, source information was discarded, or a schema was weakened to accept invalid data.

### Review Responsibilities

The reviewing agent MUST inspect the actual working-tree diff and test output. Review findings take priority over summary:

* Identify correctness, schema, source-preservation, regression, and test-coverage problems.
* Refer to concrete files and symbols.
* Reject changes that exceed the assigned scope.
* Record required corrections in `agent-handoff.md`.
* Mark the task approved only after the focused checks pass and no blocking findings remain.

Until a task is approved, the worker must treat the handoff status as `changes requested` rather than complete.

