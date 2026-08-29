# AI Tasks

Tasks are completed in order unless the user explicitly changes the scope.

The rules and development methodology for all tasks are defined in `AGENTS.md`.

## 1. XML Source Parser

Create the smallest reusable XML parsing/extraction layer required to work with the supplied D&D 5e XML source.

### Acceptance Criteria

* [ ] Inspect the actual XML structure before implementing the parser.
* [ ] Identify the top-level structure and how entities are represented.
* [ ] Identify how Creature entities are represented.
* [ ] Implement a focused, reusable XML extraction layer.
* [ ] Preserve source text and relevant XML information.
* [ ] Do not perform schema-specific normalization inside the low-level parser unless necessary.
* [ ] Add tests covering the parser's important behaviour.
* [ ] Demonstrate extraction of representative Creature entities.
* [ ] Relevant tests pass.
* [ ] No unrelated project architecture is changed.

Do not build a generalized XML framework beyond what the actual source format requires.

## 2. Creature

### Representative XML Fixtures

* [ ] Select a small, diverse representative set of Creature entries from the XML.
* [ ] Normalize them into the existing JSON schema.
* [ ] Preserve useful source descriptions.
* [ ] Validate every fixture against its root schema.
* [ ] Add the fixtures using the repository's existing test-data conventions.
* [ ] Add/update schema tests as required.
* [ ] Relevant tests pass.

### Synthetic Fixtures

* [ ] Identify schema capabilities not exercised by the XML-derived Creature fixtures.
* [ ] Create a small number of plausible synthetic fixtures covering those capabilities.
* [ ] Validate every synthetic fixture.
* [ ] Add/update tests.
* [ ] Relevant tests pass.

### Pydantic Models

* [ ] Inspect existing Pydantic models for reusable structures.
* [ ] Create/update Creature models as required.
* [ ] Match the existing JSON Schema structure.
* [ ] Reuse shared models.
* [ ] Add Pydantic construction tests.
* [ ] Add round-trip tests.
* [ ] Confirm round-tripped output remains schema-valid.
* [ ] Relevant tests pass.

## 3. Spell

### Representative XML Fixtures

* [ ] Select representative Spell entries.
* [ ] Normalize them into the existing JSON schema.
* [ ] Validate fixtures.
* [ ] Add/update tests.

### Synthetic Fixtures

* [ ] Identify uncovered Spell schema capabilities.
* [ ] Add targeted synthetic fixtures.
* [ ] Validate fixtures.
* [ ] Add/update tests.

### Pydantic Models

* [ ] Create/update Spell models.
* [ ] Reuse existing shared models.
* [ ] Add construction and round-trip tests.
* [ ] Confirm schema validity after round-tripping.

## 4. Race

* [ ] Representative XML fixtures.
* [ ] Synthetic fixtures.
* [ ] Pydantic models.
* [ ] Schema validation tests.
* [ ] Pydantic round-trip tests.

## 5. Feat

* [ ] Representative XML fixtures.
* [ ] Synthetic fixtures.
* [ ] Pydantic models.
* [ ] Schema validation tests.
* [ ] Pydantic round-trip tests.

## 6. Item

* [ ] Representative XML fixtures.
* [ ] Synthetic fixtures.
* [ ] Pydantic models.
* [ ] Schema validation tests.
* [ ] Pydantic round-trip tests.

## 7. Class

* [ ] Representative XML fixtures.
* [ ] Synthetic fixtures.
* [ ] Pydantic models.
* [ ] Schema validation tests.
* [ ] Pydantic round-trip tests.

## Final Verification

* [ ] All selected entity types have representative fixtures.
* [ ] All fixtures pass JSON Schema validation.
* [ ] Synthetic fixtures cover meaningful schema capabilities.
* [ ] Pydantic models cover represented structures.
* [ ] Pydantic round-trips remain schema-valid.
* [ ] Relevant tests pass.
* [ ] No unnecessary unrelated changes were introduced.
