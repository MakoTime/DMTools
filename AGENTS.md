# Schema Data Agent

## Mission

Convert D&D 5e XML source data in:

* `C:\Users\Dungeon Master\Documents\git\DMTools\5e Official Only.xml`

into:

1. Schema-valid JSON fixtures.
2. Additional synthetic fixtures that exercise schema capabilities.
3. Pydantic models capable of constructing and validating those objects.
4. Tests covering schema validation and Pydantic round-tripping.

The existing JSON Schemas define the normalized data model. The XML provides the source data.

Do not redesign the data model unless a genuine schema gap is discovered.

## Autonomous Execution Rules

The agent operates incrementally.

* Do NOT attempt to process the entire repository in a single task.
* Do NOT attempt to process every entity type unless explicitly instructed.
* Work on ONE entity type at a time.
* Within an entity type, work on ONE coherent implementation unit at a time.
* Before modifying files, inspect the relevant existing implementation.
* After each meaningful change, run the most relevant tests.
* Do not continue to the next entity type until the current one satisfies the Definition of Done.
* If a decision is ambiguous and cannot be resolved from the repository, schema, or source XML, stop and report the ambiguity rather than guessing.
* The current user request defines the task scope.
* If no specific entity type is specified, inspect the repository and determine the first incomplete entity type according to the existing implementation. Report the proposed scope before making substantial changes.
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
* Rewrite the XML parser/importer.
* Modify unrelated schemas.
* Modify unrelated entity types.
* Generate large numbers of fixtures.
* "Clean up" unrelated code.
* Change project architecture.
* Remove existing tests because they are inconvenient.
* Weaken validation to make a fixture pass.
* Change working behaviour merely for stylistic reasons.

## Workflow

Always perform the following steps in order.

### 1. Inspect the project

Identify:

* JSON Schema location.
* Existing fixtures.
* Existing schema tests.
* Pydantic model location.
* Existing model tests.
* XML parser/importer code.
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

For example, do not add a generic feature solely because a dedicated structured field already contains the same information, unless the source trait itself is useful and should be preserved. In that case retain the trait description as source information.

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

Pay particular attention to:

* `oneOf` accidentally matching multiple branches.
* `anyOf` being used where `oneOf` is required.
* Missing `additionalProperties: false`.
* Incorrect `$ref` paths.
* `$id` values that do not match project conventions.
* Incorrect conditional requirements.
* Incorrect nesting.
* Required fields incorrectly omitted.
* Optional fields incorrectly required.

After fixing a validation failure, rerun the relevant validation before continuing.

### 7. Add synthetic examples

After the XML-derived fixtures pass validation, create a small number of synthetic examples.

Synthetic examples exist to test schema functionality that the source XML does not cover.

Examples include:

```text
alignment with only order
alignment with only morality
alignment = any

instantaneous duration

roll with only modifier
roll with dice + modifier

target count with minimum + maximum

ability score choice
spell choice

magic item with full charge recharge
magic item with rolled recharge
magic item numerical bonus
magic item non-numeric grant
```

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

### 9. Test and iterate

For each implementation unit:

1. Inspect.
2. Plan.
3. Make the smallest required change.
4. Run the most relevant tests.
5. Read the complete failure output.
6. Determine whether the failure is caused by:

   * implementation,
   * fixture,
   * schema,
   * test,
   * import/configuration,
   * or environment.
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

Do not modify the schema merely because a single unusual source example is difficult to represent.

### Case 4 — Source text is ambiguous

Do not guess.

Preserve the source text and report the ambiguity.

## Pydantic Models

### Model requirements

Pydantic models MUST:

* Mirror the JSON Schema structure.
* Use the same field names.
* Reuse existing nested models.
* Use typed fields instead of unstructured dictionaries where practical.
* Use enums/literals where schemas define finite values.
* Represent optional fields as optional.
* Preserve nested structures.
* Avoid duplicating existing shared models.

Do not create models merely because a JSON object exists if an appropriate shared model already exists.

### Model/schema parity

Where practical, mirror schema constraints:

```text
enum
→ Enum / Literal

minimum
→ numeric constraint

minItems
→ list constraint

required
→ non-optional field

optional schema field
→ Optional field
```

Complex JSON Schema conditional logic may require Pydantic validators or discriminated model structures.

Do not make the Pydantic model stricter than the schema without a clear reason.

## Pydantic Round-Trip Tests

For every representative fixture:

```text
fixture JSON
    ↓
schema validation
    ↓
Pydantic model_validate()
    ↓
model_dump()
    ↓
schema validation
```

The dumped Pydantic representation MUST remain schema-valid.

Tests should verify:

```python
model = Model.model_validate(data)
data = model.model_dump(...)
```

and validate `data` against the corresponding JSON Schema.

Where serialization options are required by the project's existing conventions, use those conventions consistently.

## Test Strategy

Add tests for:

* XML-derived fixtures.
* Synthetic fixtures.
* Important invalid cases.
* Pydantic construction.
* Pydantic round-tripping.
* Newly introduced schema constraints.
* Newly introduced schema components.

Tests should verify the data contract, not implementation details.

Prefer targeted tests during development, followed by the broader relevant test suite before declaring the task complete.

## Entity Coverage

When processing a source XML file, consider all supported entity types represented in the file.

Current major entity types include:

```text
Creature
Spell
Race
Feat
Item
Class
```

The agent should not assume every XML file contains every entity type.

For each entity type that is explicitly selected for processing:

1. Select representative source examples.
2. Generate normalized JSON.
3. Validate it.
4. Add synthetic examples where useful.
5. Create/update Pydantic models.
6. Add tests.
7. Run the relevant test suite.
8. Complete the Definition of Done before moving to another entity type.

Do not automatically move to the next entity type unless the current task explicitly authorizes continued processing.

## Naming

Follow project conventions.

JSON fields and Python fields should normally use:

```text
snake_case
```

Fixture filenames should be descriptive and stable:

```text
acolyte.json
beholder.json
high_elf.json
prismatic_spray.json
fey_touched.json
wand_of_orcus.json
```

Do not rename existing fixtures without a reason.

## Output Expectations

At the end of a task, report:

```text
Entity types processed:

Source fixtures added:

Synthetic fixtures added:

Schemas changed:

Pydantic models added/updated:

Tests added:

Tests passing:

Known unsupported mechanics:
```

For unsupported mechanics, explain whether they were:

* intentionally preserved as description,
* ambiguous in the source,
* or blocked by a schema limitation.

Also report any unresolved issues that prevent the Definition of Done from being satisfied.

Do not report an item as complete if the relevant tests have not passed.

## Definition of Done

A task is complete only when:

* Representative source fixtures have been generated.
* Fixtures pass JSON Schema validation.
* Useful synthetic examples have been added.
* Pydantic models exist for the represented structures.
* Fixtures can be parsed into Pydantic models.
* Pydantic round-tripped data remains schema-valid.
* Relevant tests pass.
* No unrelated schemas or models were unnecessarily changed.
* No known failing tests have been ignored, disabled, or weakened.
* Any unsupported or ambiguous mechanics have been explicitly reported.

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
