 # API/XML Core Parity Audit

 ## Goal

 Make API imports and XML imports produce the same canonical **shared core** for every supported entity type, using the XML examples as the semantic reference.

 The API and XML payloads are not guaranteed to be identical. XML may contain longer descriptions or source citations that the API does not provide. The API may contain additional structured data that is not present in XML. The audit must preserve valid source-specific data, omit data unavailable from a source, and never fabricate missing values.

 Do not stop until all tasks are complete. A failing test is not a cause for stopping. ALL tasks MUST be complete before progressing

 **Audit completion note:** The comparison harness, canonical field contracts, representative XML/API coverage, adaptor fixes, hydration checks, import validation, and focused regression checks are complete. The live 2014 API does not expose the XML-derived `College of Lore` subclass; that case is covered by deterministic hydrated-resource fixtures and documented as an unavailable live source.

 ## Canonical Validation References

 Use these project artifacts as the canonical contract during the audit:

 - Pydantic models:
	 - `models/monster.py` -> `Monster`
	 - `models/spell.py` -> `Spell`
	 - `models/class_model.py` -> `Class`
	 - `models/race.py` -> `Race`
	 - `models/background.py` -> `Background`
	 - `models/feat.py` -> `Feat`
	 - `models/item.py` -> `Item`
	 - `models/subclass.py` -> `Subclass`
	 - `models/ability.py` -> `Ability` when a spell-shaped XML record is dispatched as a custom ability.
 - JSON schemas in `schemas/entities/`:
	 - `Monster.schema.json`
	 - `Spell.schema.json`
	 - `Class.schema.json`
	 - `Race.schema.json`
	 - `Background.schema.json`
	 - `Feat.schema.json`
	 - `Item.schema.json`
	 - `Subclass.schema.json`
	 - `Ability.schema.json`
 - Validation registry: `application/imports/registry.py` and `ENTITY_REGISTRY`.
 - Shared validation and record construction: `application/imports/service.py`, especially `_preview_results()`.
 - XML dispatch/reference path: `parsers/dispatcher.py` and the corresponding `parsers/*_parser.py` and `parsers/*_adaptor.py` modules.
 - API source path: `api/client.py` for fetching/hydration and `api/adaptor.py` for API-to-canonical translation.

 The comparison harness must validate both adapted payloads through the matching `EntityDefinition.validate_payload()` entry in `ENTITY_REGISTRY`. Compare the resulting model dumps, not raw source dictionaries. Pydantic/schema success proves structural validity only; it does not prove XML/API semantic parity.

 ## Supported Entity Types

 - Monster
 - Spell
 - Class
 - Race
 - Background
 - Feat
 - Item/equipment
 - Subclass

 ## Tasks

 ### 1. Locate and catalogue XML examples

 - Locate `XMLExample` and identify representative records for every supported entity type.
 - Include more than one example where the entity has meaningful variants or nested data.
 - Record the XML source identifier and entity name for each comparison case.
 - Treat the XML parser, XML adaptor, canonical Pydantic model, and entity schema as the reference path.
 - Record the model class and schema file used for each comparison case.

 ### 2. Define the shared-core comparison contract

 - List the canonical fields that constitute the shared core for each entity type.
 - Compare shared fields after both sources have passed through their source adaptor and `ENTITY_REGISTRY[entity_type].validate_payload()`.
 - Compare semantic values, not source-specific representation details.
 - Normalize only where the canonical model requires it, including casing, names, units, nested object shape, and numeric types.
 - Do not require equality for fields present in only one source.
 - Do not treat XML-only descriptions, book citations, or API-only metadata as parity failures when the other source has no equivalent data.
 - Do treat dropped, incorrectly mapped, wrongly cased, incorrectly shaped, or incorrectly defaulted shared data as failures.

 ### 3. Build a temporary comparison harness

 - Add an executable comparison task or script that can be run repeatedly during the audit.
 - Load XML examples through the real XML parser and dispatcher path.
 - Fetch corresponding API records through the real `SRDClient` path.
 - Hydrate nested API resources before adaptation where the XML core contains equivalent nested data.
 - Run both results through the shared import-service validation and normalization path.
 - Compare only the declared shared core fields.
 - Produce a report containing:
	 - entity type and name;
	 - canonical field path;
	 - XML value;
	 - API value;
	 - source field or hydration path;
	 - difference classification.

 ### 4. Classify every difference

 Use one of these classifications:

 - `equal`: shared canonical values match;
 - `source-only`: data exists in one source but not the other and is valid to preserve;
 - `missing`: a source contains comparable data but the adaptor dropped it;
 - `shape-mismatch`: equivalent data has the wrong canonical structure;
 - `normalization-mismatch`: casing, naming, units, or numeric normalization differs;
 - `value-mismatch`: both sources provide the same semantic field but values differ;
 - `hydration-mismatch`: nested API data was not fetched or resolved;
 - `invalid`: the adapted value cannot pass the canonical Pydantic model or JSON schema.

 Only `equal` and justified `source-only` differences are acceptable for the shared-core audit.

 ### 5. Audit each entity adaptor

 For every supported entity type, compare representative examples and repair `api/adaptor.py` only at the source-normalization boundary:

 - For each mismatch, first identify the expected field in the Pydantic model and JSON schema before changing the API adaptor.
 - Do not change a schema or Pydantic model merely to make an incorrect API mapping pass; change the model/schema only when the shared canonical contract itself is demonstrably incomplete.

 - Monster: ability scores, creature type, alignment, armor class, hit points/dice, movement, saves, skills, resistances, immunities, senses, languages, features, actions, reactions, legendary actions, challenge rating, and environments.
 - Spell: level, school, classes, casting time, target/range, components, material requirements, duration, ritual/concentration, description, and effects.
 - Class: name, hit die, primary/saving abilities, armor/weapons/tools, skill choices, spellcasting, base features, ability-score-improvement levels, and multiclass requirements.
 - Race: name/subtype, size, movement, ability increases, languages, skill proficiencies, senses, traits, and spell grants.
 - Background: description, skills, tools, languages where explicitly available, features, and starting-data fields represented by the canonical model.
 - Feat: description, prerequisites, ability increases, proficiencies, and other canonical effects.
 - Item/equipment: category, weight, cost, weapon data, armor data, magic-item data, properties, special features, description, and source information when present.
 - Subclass: parent class, description, levelled features, spells, tags, and subclass-specific progression data.

 ### 6. Audit API hydration and follow-through

 - Verify the importer’s actual collection/resource path, not only direct adaptor calls.
 - Hydrate class levels and feature records.
 - Hydrate subclass levels and feature records.
 - Hydrate race traits and other referenced records needed for the shared core.
 - Verify that hydrated records retain their parent context and are not duplicated.
 - Verify that unresolved references remain omitted or represented according to the canonical contract rather than being guessed.

 ### 7. Add executable checks where direct comparison is difficult

 - Use live API comparison for stable, publicly available records.
 - Use deterministic source fixtures for cases affected by API availability, changing records, rate limits, or nested resource behavior.
 - Add focused tests for each discovered mapping defect and hydration defect.
 - The comparison harness and fixtures may remain temporary audit tooling unless they provide lasting regression value.
 - Do not consider Pydantic validation alone sufficient evidence of parity.
 - Include at least one assertion that the normalized payload passes both the Pydantic model and its corresponding JSON schema.
 - Include at least one comparison assertion for semantic equality of shared fields after model dumping, rather than only checking that validation succeeds.

 ### 8. Validate the final result

 - Run the comparison harness across the selected examples from all entity types.
 - Confirm that all shared-core differences are resolved or explicitly explained as source-only data.
 - Confirm that source-specific extra data is preserved without contaminating the shared core.
 - Confirm that unavailable fields are omitted rather than fabricated.
 - Run the actual API import preview and commit preparation path.
 - Run focused tests, Ruff, compilation, and the broader regression suite.
 - Document remaining unavoidable differences, including XML-only prose/citations and API-only structured fields.

 ## Acceptance Criteria

 - Every supported entity type has at least one XML/API comparison case.
 - Complex entities have additional cases covering nested or optional data.
 - Shared canonical fields match semantically after normalization.
 - XML-only and API-only fields are preserved when valid and ignored when comparing the shared core.
 - Missing data is never invented.
 - Nested API data required for core parity is hydrated through the real importer path.
 - The comparison output contains no unexplained `missing`, `shape-mismatch`, `normalization-mismatch`, `value-mismatch`, `hydration-mismatch`, or `invalid` results.
