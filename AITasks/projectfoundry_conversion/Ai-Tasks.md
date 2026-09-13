# DMTools Development Plan

## Goal

Complete the full set of tasks in this plan to improve DMTools' architecture,
ownership, persistence, workflows, user interface, and reliability. Preserve
existing user-facing workflows while replacing fragile or duplicated
infrastructure with well-tested, maintainable implementations.

Treat every task below as part of the deliverable. Implement work in coherent
increments, validate success and failure paths, maintain compatibility where
required, and continue until all applicable tasks are complete. Task-specific
framework, data, and UI constraints are defined in their respective
sections below.

## Current Baseline

- DMTools already depends on ProjectFoundry from GitHub in `requirements.txt`.
- Project state is currently coordinated by `application.ProjectController` and
	`application.ProjectSerializer`.
- Tree nodes and roots are implemented under `components.tree`.
- Project objects and payload persistence are implemented under `objects`.
- The main window and project launcher are composed directly in `main.py` and
	`application.file_window.py`.
- The MDI presentation is the supported view workflow; no separate scene
	subsystem is in scope.

## Task Organization

The task list has two parts, in this order:

1. **Incomplete Tasks** contains only work that still needs implementation.
2. **Completed Tasks** contains the historical record of delivered work.

Do not mix the two parts. Move a task to **Completed Tasks** only after its
implementation, focused tests, broader validation, and documentation are
complete. Add newly discovered work to **Incomplete Tasks**, even when it is
related to an already completed feature.

Organize incomplete work by dependency rather than by artificial priority
labels: foundations and ownership first, then data and workflows, then user
interface and presentation, and finally cleanup and verification. Each task
should appear once, use a clear action statement, and include its tests or
acceptance criteria in the same task when those criteria are specific.

## Agent execution contract

Each unchecked checkbox (- [ ]) is an independent implementation task.

Section headings are grouping mechanisms only and are not themselves tasks.

The agent must work through incomplete tasks in dependency order.

After completing a checkbox, the agent must:

 1. Mark that checkbox [x].
 2. Update any relevant task notes.
 3. Re-read this file from disk.
 4. Find the next unchecked locally actionable task.
 5. Begin that task immediately.

Completing one checkbox does not complete the work session.

The work session is complete only when there are no remaining locally actionable unchecked tasks.

If a task is blocked, leave it unchecked, document the blocker, and continue with the next locally actionable task.

If implementation discovers new work, add a new unchecked task to the appropriate section and continue the existing workflow.

Do not stop merely because tests pass for the current task or because the current section is complete.

## Incomplete Tasks

Work through the following domain sections in order. Completed items have been
removed from this part of the document and are recorded below.

### Review generated entity presentation

- [x] Add an automated inspection review that renders representative canonical
	entities and reports presentation-contract violations, including missing
	progression values, raw mapping representations, adjacent metadata, and
	storage-oriented labels. Acceptance: the review produces actionable issue
	records without mutating SQLite data.

	> `tools/inspection_report.py` now writes `review.json`, `review.md`, and
	`review.html` alongside representative entity artifacts. Focused review,
	rendering, and parser tests pass.
- [x] Fix class cantrip progression extraction for source text that states the
	initial cantrip count in a general sentence and introduces later increases
	with ordinal counts. Acceptance: the real Bard source produces 2 cantrips at
	levels 1-3, 3 at levels 4-9, and 4 at levels 10-20, with focused regression
	tests.

	> `ClassAdaptor.cantrips_known()` now handles the actual Bard wording,
	including the abbreviated `and a 4th` phrase. The real-source regression and
	all class-parser tests pass.
- [x] Improve feature and source rendering for generated entity inspections.
	Acceptance: feature name, description, level, and source are visually
	separated; source mappings render as readable text; and reader-facing labels
	do not expose underscore-separated storage identifiers.

	> Feature metadata now renders as a separate block, source mappings use their
	readable text value, and generic list/scalar values humanize storage labels.
	Focused rendering and inspection-review tests pass.
- [x] Run the representative inspection report and focused presentation tests
	after the fixes, record remaining discrepancies, and add follow-up tasks for
	any unresolved source-shape issues.

	> Full `5eFile.xml` review examined 4,630 records: 4,605 valid and 25
	duplicate-identity diagnostics. The report produced 12 representative
	presentation findings, which became the follow-up tasks below.

- [x] Normalize nested mapping values in entity rendering for representative
	monster and spell records. Acceptance: Acolyte and Fireball inspection output
	does not expose Python dictionary syntax, while structured values remain
	readable and deterministic.

	> Reader-facing labels and table cells now use the shared scalar formatter,
	which removes Python mapping representations while preserving deterministic
	structured output. Focused rendering and review tests pass.
- [x] Separate feature metadata for all named feature shapes, including
	features whose description or entries are nested rather than a single string.
	Acceptance: the representative class, subclass, race, item, background, and
	feat outputs contain no feature-text/metadata adjacency findings.

	> Named features now separate descriptions, nested entries, levels, and
	sources. The complete-source representative report is clean with 0
	presentation issues, and the focused presentation suite passes.
- [x] Define and test duplicate source-identity handling for the full XML
	import. Acceptance: the 25 duplicate records are either intentionally
	deduplicated with documented policy or retained with distinct source
	identities; valid import counts and diagnostics are explicit.

	> The application import workflow uses `duplicate_policy="replace"` for
	full-source imports. With that explicit policy, `5eFile.xml` produces 4,605
	valid records, 0 issues, and `can_commit=True`; strict preview rejection
	remains available as the low-level default. Existing duplicate-policy tests
	cover reject, skip, and replace behavior; the final focused regression suite
	passes 48 tests and Ruff reports no issues.

### Define entity presentation contracts

Each task in this section defines the expected reader-facing, statblock-style
layout before implementation. Contracts must describe section order, optional
sections, field transformations, omission rules, and one representative source
record. Canonical SQLite/JSON payloads remain unchanged.

- [x] Define the expected monster stat-block layout using Frog as the reference
	record and Acolyte as a populated comparison record. Acceptance: document
	identity, defenses, movement, ability table, proficiencies, senses,
	challenge, traits, actions, reactions, legendary actions, and omission rules.
- [x] Define the expected spell-block layout using Fireball as the reference
	record. Acceptance: document level/school, casting time, range/target,
	components, duration, effects, description, higher-level text, classes,
	ritual, concentration, and source ordering.
- [x] Define the expected item-block layout using Backpack and a weapon or
	magic item as references. Acceptance: document category, armor/weapon
	statistics, weight, cost, properties, features, granted content, description,
	charges, and source ordering.
- [x] Define the expected class-block layout using Bard as the reference
	record. Acceptance: document proficiencies, spellcasting, level progression,
	subclass markers, class features, optional features, description, and source
	ordering.
- [x] Define the expected subclass-block layout using College of Lore as the
	reference record. Acceptance: document parent class, subclass features by
	level, granted spells or proficiencies, description, and source ordering.
- [x] Define the expected race-block layout using Human as the reference
	record. Acceptance: document size, speed, ability increases, proficiencies,
	languages, traits, granted content, description, and source ordering.
- [x] Define the expected feat-block layout using Alert or Lucky as the
	reference record. Acceptance: document prerequisites, ability increases,
	proficiencies, features, actions, description, and source ordering.
- [x] Define the expected background-block layout using Acolyte as the
	reference record. Acceptance: document skill/tool proficiencies, languages,
	equipment, features, description, and source ordering.
- [x] Define the expected ability-block layout using Action Surge or Arcane
	Recovery as the reference record. Acceptance: document category, class,
	level, prerequisites, effects, granted content, description, and source
	ordering.
- [x] Review all nine presentation contracts together and resolve shared
	conventions. Acceptance: labels, source handling, feature treatment, links,
	missing-value policy, and section-heading rules are consistent without
	flattening entity-specific layouts.

	> All nine contracts and their shared conventions are defined in
	`docs/entity-presentation-contracts.md`.

### Generate entity presentation templates

- [x] Add the shared presentation-model and template-rendering boundary.
	Acceptance: canonical records are converted into read-only presentation
	models before rendering; templates cannot mutate payloads; the generic
	renderer remains a fallback for unsupported fields and types.
- [x] Generate and test the monster stat-block template from the approved
	monster contract. Acceptance: Frog and Acolyte render in PHB-style order with
	ability modifiers, grouped stat lines, and conditional Traits/Actions/
	Reactions/Legendary Actions sections.
- [ ] Generate and test the spell-block template from the approved spell
	contract. Acceptance: Fireball renders its spell metadata and effects in the
	agreed order without raw mapping or storage-field output.
- [ ] Generate and test the item-block template from the approved item
	contract. Acceptance: Backpack, a weapon, and a magic item use the correct
	item-specific sections and omit irrelevant sections.
- [x] Generate and test the class-block template from the approved class
	contract. Acceptance: Bard renders its PHB progression table before Class
	Features, with the detailed feature blocks in PHB order.

	> Dedicated class rendering now keeps the Bard table before the feature
	sequence and preserves the existing derived progression behavior for sparse
	fixtures.
- [x] Generate and test the subclass-block template from the approved subclass
	contract. Acceptance: College of Lore renders its parent class and overview
	followed by leveled features without a fabricated progression table; source-
	backed table-bearing features such as Eldritch Knight Spellcasting remain in
	their source position.

	> Dedicated subclass rendering now distinguishes overview-led subclasses from
	legacy sparse fixtures and covers College of Lore and Eldritch Knight ordering.
- [ ] Generate and test the race-block template from the approved race
	contract. Acceptance: Human renders identity, movement, ability changes,
	proficiencies, traits, and languages in the agreed order.
- [ ] Generate and test the feat-block template from the approved feat
	contract. Acceptance: the selected feat renders prerequisites and effects in
	the agreed order with optional sections omitted cleanly.
- [ ] Generate and test the background-block template from the approved
	background contract. Acceptance: Acolyte renders proficiencies, equipment,
	features, and description without generic Details output.
- [ ] Generate and test the ability-block template from the approved ability
	contract. Acceptance: the selected ability renders category, class/level,
	prerequisites, effects, and description in the agreed order.
- [ ] Route the viewer to the dedicated template for each supported entity type
	and retain the generic renderer as a deliberate fallback. Acceptance: all
	nine representative records render through their dedicated templates and
	unknown fields remain visible without corrupting the primary layout.
- [ ] Run a cross-entity snapshot and HTML validation pass against the approved
	templates. Acceptance: no representative output exposes raw Python mappings,
	storage-oriented labels, incorrect section order, or fabricated data; the
	canonical payloads and SQLite records remain byte-for-byte unchanged.

### Move project ownership to ProjectFoundry

- [x] Replace the DMTools-owned project controller/serializer orchestration
	with ProjectFoundry `Project`, `ProjectContext`, `ProjectService`, and
	project package APIs where applicable.
- [ ] Make ProjectFoundry registries the canonical lookup path for project,
	object, block, node, and relationship identities.
	
	> Blocked pending the tree-contract migration: the remaining parallel
	> `root_objects` registry is still required by the explicit legacy import
	> path and compatibility database controller; migrated block, relationship,
	> and canonical node lookups already use ProjectFoundry registries.
- [x] Replace compatibility-only root registry lookups with an explicit
	ProjectFoundry-backed legacy tree projection adapter, preserving legacy
	import and round-trip behavior while making ProjectFoundry the lookup source.

	> `LegacyTreeProjectionAdapter` now owns the legacy-root projection boundary;
	controller refresh and project replacement resolve through the canonical
	Project tree, while legacy roots remain available only for compatibility
	serialization. Tree and lifecycle regression tests pass.
- [ ] Define stable UID-backed DMTools records and remove long-lived references
	to live Qt widgets or pandas objects.
	
	> Blocked pending the object/artifact migration: `TableDataObject` still
	> retains a pandas `DataFrame` for the legacy editor path, and removing it
	> requires the disk-backed `EditedObject` migration below.
- [x] Migrate `TableDataObject` payload ownership to a disk-backed artifact and
	retain only UID, metadata, and artifact references on the edited object.

	> `TableDataObject` now releases its editable DataFrame after a successful
	artifact commit and reloads committed data lazily through ProjectFoundry;
	table compatibility and failure-preservation tests remain green.
- [x] Migrate new, open, save, save-as, recent-project, and close workflows to
	the ProjectFoundry project lifecycle.
- [x] Preserve compatibility for current DMTools project files through an
	explicit import/migration step rather than silently changing their meaning.
	
	> Added explicit lifecycle/controller legacy import APIs; normal migrated
	> loading now rejects roots-only files, with focused regression coverage.

### Create the Compendium hierarchy

- [x] Add context-menu actions for import, refresh, search, and category-level
	query operations where applicable. Actions are callback-driven so application
	services retain ownership of project mutations.

### Convert the tree and node model

- [x] Map `components.tree` roots, nodes, and models onto ProjectFoundry tree
	contracts while preserving DMTools root categories and context menus.
	
	> Canonical ProjectFoundry nodes now feed the framework tree model after each
	> projection refresh; the legacy tree remains available for compatibility
	> serialization and context-menu behavior.
- [x] Define which DMTools concepts are ProjectFoundry blocks, nodes, or
	application-only commands.
	
	> Added the ownership mapping to `docs/projectfoundry-architecture.md`,
	> including blocks, UID-backed tree nodes, and application-only commands.
- [ ] Route create, rename, move, delete, and duplicate operations through the
	project/application service boundary.
	
	> Partially implemented: registered block renames now route through the
	> active Project. Move and duplicate remain blocked because the pinned
	> ProjectFoundry API exposes no move/duplicate node operations; deletion and
	> creation need that same application-level contract before legacy callers
	> can be removed safely.
- [x] Add an application tree mutation service for supported create, rename,
	delete, and relationship validation operations, with rollback and UID tests.

	> `ProjectTreeMutationService` now validates parent and block/node UIDs,
	rolls back failed creation, and routes rename/delete through ProjectFoundry;
	`test_project_tree_mutation_service_validates_and_rolls_back_block_changes`
	covers the supported operations.
- [ ] Define a ProjectFoundry-compatible move/duplicate node contract and
	implement it when the pinned framework exposes the required operations.
- [x] Persist tree hierarchy and node state as UID-based project data.
	
	> Framework serialization now round-trips block node identity and parent
	> relationships through ProjectFoundry registries, with lifecycle coverage.
- [x] Add tests for node registration, parent/child relationships, duplicate
	names, deletion, project replacement, and reload.
	
	> Existing entity, collection, query, object, and lifecycle tests now cover
	> registration, UID parentage, duplicate handling, deletion, replacement,
	> and reload; lifecycle coverage also verifies a persisted block node.

### Convert DMTools objects and data persistence

- [x] Adapt JSON, table, database, query, and shopkeeper objects to the
	ProjectFoundry block/data lifecycle where they have durable project state.
	
	> JSON, table, database, query, and shopkeeper objects expose registered
	> ProjectFoundry blocks; controller and round-trip tests cover their durable
	> state, UID relationships, and artifact commits.
- [x] Replace the legacy DMTools `ObjectBase` and `ObjectData` abstractions with
	ProjectData `EditedObject`; migrate every subclass, serializer, editor, and
	call site so neither legacy symbol remains in the repository when this work is
	complete.
	
	> Project wrappers now inherit ProjectFoundry `EditedObject`, and repository
	> searches plus migration tests confirm the legacy symbols are absent.
- [ ] Keep `EditedObject` strictly temporary: persistent state must live in the
	ProjectFoundry block data or a disk-backed artifact, with only lightweight
	identity, metadata, and artifact references retained in memory. Do not keep
	full JSON payloads, pandas DataFrames, SQLite contents, or other durable data
	on project objects as a second in-memory source of truth.
	
	> Blocked pending the disk-backed editor migration: legacy compatibility
	> wrappers still retain JSON payloads and `TableDataObject` retains a pandas
	> DataFrame for its existing editor path.
- [ ] Audit JSON/table/database/query/shopkeeper compatibility wrappers and
	remove durable payload retention after their artifact-backed editor paths
	are available.

	> Blocked for JSON and legacy compatibility wrappers: inline JSON artifact
	loading and a complete artifact-backed editor contract are not available;
	`TableDataObject` is migrated, while database/query/shopkeeper wrappers retain
	legacy projection state required by their current compatibility serializers.
- [x] Add regression coverage proving ProjectData `EditedObject` owns temporary
	edited state and that no import, type annotation, compatibility alias, or
	serialized type depends on `ObjectBase` or `ObjectData`.
	
	> `tests/test_project_object_migration.py` covers EditedObject identity and
	> rejects legacy symbol exports.
- [x] Keep SQLite as the source of truth; treat pandas and other tabular
	representations as temporary display/editing layers.
- [x] Separate persistent block metadata from large or external payloads and
	artifacts, using ProjectFoundry artifact metadata and storage contracts.
- [x] Register DMTools object types with a framework type/serializer registry and
	reject unknown types with actionable migration errors.
	
	> ProjectController registers all migrated block types and the legacy
	> serializer rejects unsupported object types with their type name.

### Homebrew hierarchy and authoring

- [x] Support editing existing Homebrew items from their inspection view and
	Homebrew tree/query results using a temporary `EditedObject` draft. Keep the
	canonical Homebrew block unchanged until validation and explicit acceptance.
- [x] Validate Homebrew item drafts with the Pydantic model, JSON Schema, field
	constraints, canonical entity type, and reference/provenance rules before
	applying them to the ProjectFoundry block or project-managed SQLite store.
	
	> `HomebrewDraft` validates through the canonical entity registry and applies
	> only after explicit controller acceptance; focused tests cover edit,
	> cancel, invalid values, provenance, and reopen behavior.
- [x] Show field-level validation errors in the editor, preserve the last valid
	block on failure, and guarantee cancel/close leaves the Homebrew item and
	project registries unchanged.
	
	> Homebrew dialogs surface validation errors without applying drafts, and
	> controller coverage verifies invalid edits preserve the last valid row and
	> UID-backed tree state.
- [x] Re-render the item's derived Markdown/HTML inspection after a successful
	accept, invalidate stale generated output, and keep the inspection linked to
	the same Homebrew UID.
	
	> Accepted Homebrew edits now refresh an open inspection by canonical UID;
	> focused tests verify updated derived HTML while preserving identity.
- [x] Add end-to-end tests for inspecting a Compendium item, cloning it to
	Homebrew, editing fields, rejecting invalid values, cancelling edits,
	accepting valid edits, reopening the project, and confirming the source item
	was never mutated.
	
	> `test_homebrew_workflow_round_trips_without_mutating_compendium_source`
	> covers the complete import, clone, invalid/cancelled/accepted edit,
	> save/reopen, and source-immutability path.

### Shared entity links and navigation

- [x] Make clicking a shared reference resolve the canonical entity and open a
	modeless MDI inspection view without creating a second copy of the entity.
	
	> `EntityInspectionController` resolves canonical UIDs, routes generated
	> links through navigation history, reuses one MDI view per entity, and keeps
	> cycle protection; focused tests cover link opening and view reuse.

### Import, query, and authoring UX refinement

- [x] Make every entity row in the Compendium, Homebrew, and collection views
	openable from the tree or table presentation through the canonical UID
	navigation service. Preserve the existing source namespace, selection, and
	MDI reuse behavior; do not instantiate a second entity payload in the click
	handler.

	Acceptance criteria: opening an item, spell, class, subclass, monster, feat,
	race, background, or ability from each supported tree/table surface activates
	the corresponding inspection MDI child; missing or stale UIDs show the normal
	application error path; repeated activation reuses the existing child.

	> Tree entity activation now resolves the canonical entity UID before opening;
	query, collection, and search results route through the same navigation
	controller. Focused tree/search coverage passes.

- [x] Make recognized spells in creature inspections selectable and openable.
	Render each spell reference as a UID-backed link when it resolves, preserve
	unresolved spell names as readable text with a diagnostic, and route clicks
	through the same navigation controller used by other entity links.

	Acceptance criteria: a creature with prepared, known, or innate spell entries
	shows clickable spell names; clicking one opens or activates the spell
	inspection; back navigation returns to the creature; ambiguous and missing
	spell names never open an arbitrary entity.

	> Monster spell references now render in a dedicated clickable Spells section
	through the existing UID link/navigation pipeline; unresolved references keep
	diagnostics. Rendering and reference tests pass.

- [x] Add pagination or bounded-page navigation to all entity/table views that
	can exceed 100 rows. Keep the canonical query/database source unpaginated and
	load only the requested page into the Qt model; provide next, previous, and
	page-selection controls with disabled states at the boundaries.

	Acceptance criteria: datasets with 0, 1, 99, 100, 101, and multiple-page
	counts render correctly; changing pages preserves the active filter and source
	namespace; selection and open actions use the UID from the current page; no
	view silently truncates results at 100.

	> Entity query/search results and Collections now expose previous/next/page
	selection controls backed by page-aware UID presentation models. Boundary
	tests cover empty, exact-page, over-page, and final partial-page results.

- [x] Convert the entity search dialog into a non-modal MDI search child.
	The search window must not block interaction with the main window, tree, menus,
	or other MDI children while it is open. Give it a dedicated model/view/factory
	boundary: the model owns the query text, filters, source namespace, sort/page
	state, validation, and result UIDs; the view owns only Qt controls, layout,
	selection, and presentation refresh; and the factory creates or activates the
	MDI child.

	Retain the model's query/filter state while other MDI children are used, and
	route result activation through the canonical inspection/navigation service.
	Opening search again should activate the existing search child for the same
	project rather than create a modal dialog or duplicate search state. Closing
	the search window must detach callbacks, release result rows, and remove it
	from the MDI registry.

	Acceptance criteria: the main window, tree, menus, and another inspection MDI
	child remain interactive while search is open; search remains usable after
	activating an inspection; result activation reuses existing entity windows;
	project replacement clears the search model and callbacks; and
	closing/reopening the search child does not leave stale results or duplicate
	MDI children. Add a Qt smoke test that proves the search window is non-modal
	and a model test that proves query/filter state survives result activation.

	> Entity search is now a model/view/factory-backed QWidget hosted in a
	non-modal MDI child. It preserves criteria/results, reuses one child per
	category/project, routes activation through UID navigation, and cleans up on
	close or project replacement. Focused lifecycle tests pass.

- [x] Add filters/search across Compendium, Homebrew, and Collections while
	keeping source namespace visible.
- [x] Add keyboard/context actions for opening linked entities, adding selected
	rows to Collections, and creating Homebrew copies.
	
	> Entity search covers both database namespaces, collection search now
	> filters canonical members, and query-result actions cover UID-backed open,
	> collection add, and Homebrew clone/edit while displaying Source.
- [x] Add complete desktop workflow coverage for import, query, collection,
	homebrew edit, linked popup navigation, save, reopen, and shutdown.

	> `test_desktop_workflow.py` exercises the controller, query-results view,
	collection, Homebrew draft, modeless MDI reuse, persistence, and cleanup.

### Entity inspection and generated presentation

- [x] Keep class progression tables concise when imported subclass records contain
	many optional features. Show one class-specific marker such as `Bard College
	Feature` per level instead of repeating every subclass name and feature in the
	class table; preserve full subclass feature details in subclass records.

	> Class-table subclass projections now deduplicate entries by level while
	retaining detailed subclass imports for direct subclass inspection.

- [x] Derive and persist class cantrip progression during import. Inspect the
	XML class `autolevel`/slot data and adaptor output, map cantrips known and
	spell-known/prepared progression into the canonical Pydantic model where the
	source provides it, and keep the display projection separate from import
	validation when the source is incomplete.

	Acceptance criteria: representative full, half, third, pact, and
	non-spellcasting classes are covered; cantrip data survives parser, adaptor,
	Pydantic validation, SQLite persistence, reload, and class-table rendering;
	missing values remain explicit rather than guessed; import/export schemas and
	presentation-only metadata are not conflated.

- [x] Make every monster spell reference selectable and openable through the
	canonical UID navigation path. Trace parsed monster spell lists through the
	monster adaptor, `Creature.spell_casting`, entity-reference extraction,
	SQLite metadata, Markdown/HTML links, and the MDI inspection controller.

	Acceptance criteria: `spells_known` entries, cantrips, and at-will monster
	spells resolve to spell UIDs when unique; missing and ambiguous names produce
	diagnostics without broken links; links work from Markdown and HTML and open
	the canonical spell inspection without duplicating the entity; regression
	tests cover imported and Homebrew monsters.

- [x] Repair the PDF comparator and presentation comparison workflow so its
	output represents the actual `PlayersHandbook.pdf` structures rather than the
	current generic field dump. Compare normalized headings, tables, labels,
	grouping, typography-relevant line breaks, and section order separately from
	canonical data correctness, while avoiding protected book prose in runtime
	fixtures.

	Acceptance criteria: the comparator can inspect Markdown, HTML, and compact
	display output; reports identify structural differences with stable paths and
	severity; representative class, subclass, monster, spell, item, race, feat,
	background, and ability comparisons are reproducible; tests prove that HTML
	tables, bold name/description blocks, links, and source placement are compared
	as their rendered structures rather than as raw text alone.

- [x] Review and realign display ordering for every supported entity type using
	the proposed contract in `docs/entity-display-order-review.md` and
	`PlayersHandbook.pdf` as the presentation reference. Apply the same semantic
	order to Markdown, HTML, compact inspection objects, nested features/actions,
	progression tables, links, and provenance labels.

	Acceptance criteria: the review document is approved or amended before the
	implementation contract changes; deterministic ordering tests cover item,
	spell, monster, class, subclass, race, feat, background, and ability outputs;
	missing fields, repeated levels, unknown fields, and nested name/description
	objects do not change the position of later sections; intentional deviations
	from the PDF are documented.

- [x] Split Compendium and Homebrew JSON project data out of `project.json`
	into separately managed project files so users can share either dataset
	without sharing the complete project. Keep `project.json` as the project
	manifest and record the managed data-file paths, format versions, and source
	namespaces there.

	Acceptance criteria: saving writes independent Compendium and Homebrew data
	files atomically; loading resolves and validates both files before mutating
	the project; missing, stale, duplicate, or cross-project references fail with
	clear diagnostics; legacy monolithic `project.json` files remain readable and
	can be migrated; sharing one data file does not expose the other namespace.

	> Namespace-scoped JSON object payloads now persist in
	`data/compendium.json` and `data/homebrew.json`, while `project.json` stores
	 the manifest references. Legacy inline payloads remain readable and keyed
	 payloads are restored before object construction.

- [x] Render display objects with a reader-facing name/description treatment.
	When an object has both `name` and `description`, omit those keys from the
	field list, render the name in bold, insert a line break, and render the
	description beneath it. Preserve the canonical payload, escaping behavior,
	unknown-field fallback, and equivalent Markdown/HTML output.

	Acceptance criteria: objects with both fields, either field, empty values,
	long text, nested values, and unsafe text have deterministic tests; generated
	output does not expose duplicate raw `name` or `description` fields.

	> Renderer contract v3 renders named display objects as bold labels followed
	 by descriptions on a new line in Markdown and HTML while preserving payloads.

- [x] Move the class level progression table near the beginning of class
	inspection output using `PlayersHandbook.pdf` as the presentation reference.
	Keep identity and essential class metadata first, then show the level table
	before lengthy feature descriptions, spellcasting details, and source notes.
	Apply the same ordering to Markdown, HTML, and compact display objects.

	Acceptance criteria: heading/order tests assert the table appears at the PHB
	reference position for classes and remains appropriate for subclasses; table
	content and links are unchanged; missing progression data does not reorder or
	remove later sections; the audit records any intentional terminology or
	grouping differences without copying protected prose.

	> Class progression now appears before feature details in the derived payload;
	 the audit records this ordering as the PHB-aligned presentation position.

- [x] Avoid repeating source/provenance labels on every feature in display
	objects when the containing entity already supplies the source. Retain source
	metadata in the canonical payload and expose feature-level source only when it
	differs from the containing entity or is needed for an explicit provenance
	action.

	Acceptance criteria: same-source feature records omit redundant visible source
	labels in Markdown, HTML, and compact views; differing-source features retain
	their label and link; canonical serialization and source navigation remain
	unchanged.

	> Same-entity feature source labels are omitted from derived Markdown/HTML;
	 canonical source metadata remains intact for navigation and provenance.

- [x] Reorder creature, spell, item, class, subclass, race, feat, background,
	and ability inspections to follow the corresponding D&D/Players Handbook
	reading order. Define a versioned presentation schema per entity type rather
	than relying on parser field order, and keep optional sections omitted or
	placed in their canonical position.

	Acceptance criteria: each supported renderer has a documented ordered section
	list, deterministic output tests assert heading order, and missing fields do
	not cause later sections to move into an invalid order.

	> Renderer version 2 now uses explicit schema-backed contracts for stat-block,
	spell-block, equipment, class, race, feat, background, and ability ordering;
	unknown fields remain deterministic after the documented fields. Focused
	ordering tests pass.

- [x] Add Player's Handbook-style class and subclass progression sections.
	Render level-by-level feature tables, spell-slot progression, cantrip and spell
	known/prepared progression where the source data supports it, and subclass
	feature levels in the appropriate class context. Keep rules text and source
	provenance linked to canonical entities rather than duplicating durable data.

	Acceptance criteria: class inspections show levels 1 through the available
	maximum with feature names and links; spellcasting classes show the correct
	spell-slot table shape; non-spellcasting classes do not show misleading slot
	columns; subclass features appear at their levels; incomplete imported data
	shows an explicit unavailable-data state instead of fabricated values.

	> Class and subclass inspections now render a presentation-only 20-level table
	> with ordinal levels, proficiency bonuses, feature names, cantrips, and
	> standard full/half/third-caster slot columns when spellcasting progression
	> supports them. Explicit presentation metadata can provide exact cantrip and
	> slot values without changing the import/export schema; non-spellcasting
	> classes omit slot columns. Focused and full regression tests pass.

- [x] Add a Players Handbook presentation audit for all object/entity views and
	common structured fields. Compare generated Markdown/HTML and compact object
	views against `PlayersHandbook.pdf`, recording field-order, terminology,
	labeling, grouping, unit, and omission differences for senses, speeds,
	proficiencies, actions, traits, damage, equipment, spell properties, and
	progression tables.

	Deliverables: a versioned audit document, representative extracted PHB
	examples or fixtures, a prioritized discrepancy list, and renderer tests for
	each corrected pattern. The PDF is a reference for presentation and wording;
	do not copy protected prose wholesale or use it as a runtime data source.

	> Added the versioned audit at `docs/phb-presentation-audit.md`, documenting
	ordered sections, normalized fields, current source-data gaps, and follow-up
	fixtures without storing PHB prose as runtime data. Follow-up fixes now render
	direct class/subclass progression tables and expose resolved spell links for
	all spell-bearing entity types, including creatures and magic items.

- [x] Normalize structured object fields into reader-facing PHB-style text
	without losing the underlying typed data. For example, render a sense record
	like `{type: darkvision, distance: 60, distance_type: feet}` as
	`Darkvision: 60 ft`, and apply the same formatting policy to speeds,
	proficiencies, resistances, immunities, damage, ranges, durations, and costs.

	Acceptance criteria: formatter helpers have typed-input tests for singular,
	plural, missing, zero, and unknown values; generated output never exposes
	internal keys such as `distance_type` unless no presentation mapping exists;
	unknown fields remain visible through a safe fallback; Markdown and HTML use
	the same normalized values.

	> Renderer normalization now covers typed senses, movement, ranges, durations,
	costs, proficiencies, resistances, immunities, and vulnerabilities while
	retaining canonical payloads unchanged. Zero, missing, unknown, Markdown, and
	HTML cases are covered by focused tests.

- [x] Define an entity inspection presentation contract for items, spells,
	races, classes, subclasses, monsters, feats, backgrounds, and abilities,
	with a shared layout plus type-specific sections and field ordering.
- [x] Generate a readable Markdown inspection document from the canonical
	block/database record, using a versioned template and stable entity UID
	metadata. Treat Markdown as a derived view; never use it as a second source
	of truth or store full entity payloads on an in-memory UI object.
	
	> Added a versioned entity presentation contract and applied its stable field
	> ordering to the canonical Markdown/HTML renderers; focused tests cover all
	> supported entity types and UID metadata.
- [x] Make the Markdown output compatible with the structure and conventions
	of HomeBrewery-style content, including headings, callout sections, lists,
	tables, emphasis, source/provenance, and optional descriptive text.
- [x] Add Markdown rendering tests for every supported entity type, empty or
	missing optional fields, long descriptions, nested features, lists, tables,
	and unresolved references.

	> The renderer supports deterministic headings, metadata callouts, nested
	> lists, explicit tables, emphasis, provenance, optional fields, and visible
	> unresolved-reference diagnostics across all supported entity types.
- [x] Convert generated Markdown into styled HTML through a controlled
	rendering pipeline, with an application-owned HTML template and versioned
	CSS assets. Keep the renderer deterministic and safe for untrusted imported
	text; do not allow arbitrary script injection.

	> Generated Markdown now passes through an allowlisted, escaped HTML
	> converter with versioned template/CSS metadata and restricted entity links.
- [x] Add a polished inspection stylesheet with readable typography, spacing,
	section hierarchy, responsive layouts, compact metadata, source labels,
	feature blocks, spell/item properties, and print-friendly rules.

	> The versioned inspection stylesheet is loaded by MDI HTML documents and
	provides responsive tables, callouts, metadata, feature spacing, and print
	 rules without introducing a second presentation asset.
- [x] Render inspection HTML lazily from the canonical UID when an entity is
	opened, rather than retaining all generated Markdown, HTML, or large payloads
	in memory. Cache only bounded derived output when profiling demonstrates a
	benefit, and invalidate it when the source block/database revision changes.

	> MDI inspections resolve records by UID only when opened/refreshed, release
	> the resolved payload after rendering, and expose UID-based invalidation;
	> no derived-output cache is retained.
- [x] Turn recognized spell, item, class, subclass, monster, feat, race,
	background, and ability mentions into UID-backed links during rendering.
	Preserve unresolved names as plain text with a diagnostic or visible fallback.
	
	> Reference normalization stores UID-backed metadata and unresolved
	> diagnostics; Markdown/HTML rendering emits canonical entity links and
	> visible unresolved-reference details.
- [x] Handle clicks on generated entity links through an application navigation
	service that resolves the target UID and opens or activates its modeless MDI
	inspection view. Do not create duplicate entity objects or copy payloads into
	the link handler.
- [x] Add back/return navigation from linked inspections, prevent cycles from
	creating unbounded windows, and reuse an existing MDI view for an already
	open entity when appropriate.
- [x] Add tests for reference extraction, generated link targets, missing and
	ambiguous names, cross-namespace links, click-to-open behavior, MDI view
	reuse, and navigation history.

	> Entity navigation tests cover UID resolution, generated URI opening, view
	> reuse, back navigation, cycle protection, and unresolved references.

### Rebuild application and editor boundaries

- [ ] Make Homebrew entities editable from every supported tree/table entry
	with schema-aware validation and an adaptive editor view. Build the editor
	from the canonical entity schema: use dropdowns/comboboxes for enumerations,
	UID-backed entity pickers for references, bounded numeric controls for levels,
	ranges, counts, and distances, and repeatable structured editors for actions,
	traits, senses, spell lists, and progression data.

	The editor must preserve a temporary draft until validation succeeds, show
	field-level errors without discarding valid edits, adapt visible controls to
	the selected entity type and subtype, and apply changes through the
	ProjectFoundry-backed application service. Invalid drafts must not mutate the
	canonical block, database row, tree display, or committed artifact.

	Acceptance criteria: item, spell, class, subclass, creature, feat, race,
	background, and ability drafts can be opened, edited, validated, cancelled,
	accepted, and reopened; enum/reference fields use constrained controls;
	conditional sections appear and disappear with the relevant type or toggle;
	invalid required fields, malformed references, duplicate entries, impossible
	level ranges, and invalid dice/formula values are reported inline; focused
	model, view, persistence, cancellation, and project-replacement tests cover
	the workflow.

	> Partially implemented: the editor now generates schema-driven enum, boolean,
	bounded numeric, scalar-list, and nested-object repeatable controls while
	retaining temporary draft validation. UID-backed reference pickers remain
	blocked because the current entity schemas store several references as names
	and the editor factory has no project-scoped resolver contract yet.

- [x] Move startup composition and project commands out of `main.py` into an
	application-level service/composition boundary.

	> `application.startup.ApplicationLauncher` now owns launcher callbacks,
	project-window composition, and the Qt event loop; `main.py` is a thin entry
	point.
- [x] Keep Qt views responsible for layout, signals, selection, and presentation
	refresh; keep mutations in models/services.

	> View/tree scans found no direct Project registry mutations; accepted entity,
	Homebrew, query, collection, and tree changes route through controllers or
	services. The legacy database workspace remains a separate editor migration.
- [x] Convert database definition, database workspace, and query editors to
	dedicated `model.py`, `view.py`, and `factory.py` modules using the existing
	dialog base classes.

	> Database definition, database workspace, and query editors have these
	modules and focused factory/base-class coverage.
- [x] Define dedicated table and object editor contracts.

	> `TableEditorMdiContract` and `ObjectInspectionMdiContract` now define the
	refresh, commit, close, and inspection boundaries used by future editors.
- [x] Convert concrete table and object editor paths to `model.py`, `view.py`,
	and `factory.py` modules.

	> `dialog.table_editor` and `dialog.object_inspection` now provide dedicated
	model/view/factory modules with UID-backed loading and lifecycle coverage.
- [x] Build a concrete table editor using the existing model/view/factory and
	`TableEditorMdiContract`, backed by the table artifact rather than a project
	object-held DataFrame.

	> Added `dialog.table_editor` with UID/lazy-loader model, editable
	`DataFrameModel` view, factory, commit callback, and close-time release;
	focused and surrounding editor regression tests pass.
- [x] Replace modal entity inspection dialogs with modeless MDI child views
	that fit inside the main window's MDI area, can be resized and tiled, and
	remain available while the user navigates the tree or query results.

	> Entity inspection uses `EntityInspectionController` and a reusable MDI
	child per canonical UID; the Qt smoke test covers link navigation, reuse,
	back navigation, and shutdown.
- [x] Define and replace any remaining modal object inspection paths with
	modeless MDI child views.

	> No separate modal object inspection entry point exists locally; the generic
	object inspection path is now provided by the modeless MDI package below.
- [x] Define a generic object inspection model/view/factory and replace any
	remaining modal object inspection entry points with an MDI child.

	> Added `dialog.object_inspection` with a UID/lazy-loader model, read-only
	MDI view, factory, and close-time payload release; focused and MDI regression
	tests pass. No remaining modal object inspection entry point exists locally.
- [x] Define separate MDI view contracts for read-only entity inspection,
	editable Homebrew/entity drafts, database workspaces, and query results;
	retain modal dialogs only for short confirmations, destructive actions, and
	blocking validation decisions.

	> `dialog.base.mdi_contracts` now declares structural contracts for all four
	> MDI roles; existing views retain popup dialogs only where they are still
	> used for definition or confirmation workflows.
- [x] Make entity inspection MDI views resolve their target by UID and load
	presentation data lazily from the canonical entity store. Closing the view
	releases generated HTML, callbacks, and the resolved payload.

	> `EntityDetailModel` supports UID/loader-backed resolution and releases the
	resolved entity after rendering; controller refreshes re-resolve by UID.
- [x] Make database workspace MDI views resolve their target by UID and load
	presentation data lazily from the database store. Closing the view releases
	the resolved payload.

	> Database workspaces accept a UID plus loader, resolve their database payload
	on demand, preserve direct-object compatibility callers, and release the
	resolved payload on close. Focused workspace coverage passes.
- [x] Make query-results MDI views resolve their result set by UID and load
	rows lazily from the supplied store. Closing the view releases loaded rows
	and detaches the loader.

	> `EntityQueryResultsModel` accepts a result UID plus loader, preserves the
	existing row-based compatibility path, and releases rows through the actual
	widget close path. Focused editor lifecycle coverage passes.
- [x] Make remaining editor MDI views resolve targets by UID and load
	presentation data lazily from ProjectFoundry blocks, artifacts, or SQLite
	stores. Closing each view must release loaded payloads and callbacks.

	> The local MDI inventory contains only entity inspection, Homebrew draft,
	database workspace, and query-results views. Entity and Homebrew lifecycle
	coverage was already present; database and query-results UID/lazy-loading
	coverage now passes. Remaining modal dialogs are confirmation, import, search,
	or saved-query workflows rather than MDI views.
- [x] Add an MDI inspection factory/controller that activates an existing view
	for the same project and entity UID, tracks navigation history, and routes
	accepted edits through the appropriate ProjectFoundry block API.

	> `EntityInspectionController` and the entity-detail factory reuse one MDI
	> child per UID, track back/cycle history, and route Homebrew edits through
	> the application controller.
- [x] Ensure editor state is temporary and validated, then applied through
	ProjectFoundry-backed application operations.
- [x] Ensure cancel, apply, editor destruction, and project replacement release
	temporary objects and callbacks cleanly.

	> Homebrew draft tests cover validation, cancel/close, accepted application,
	MDI callback cleanup, and project replacement lifecycle behavior.

### Migrate project UI and remove duplicate infrastructure

- [ ] Adapt the file/project launcher to ProjectFoundry project package and
	recent-project contracts while retaining the DMTools preview experience.

	> Partially covered: launcher composition now uses the ProjectFoundry-backed
	> lifecycle and retains preview/recent behavior. The pinned ProjectFoundry
	> release exposes no recent-project or project-package launcher contract;
	> `RecentProjectStore` remains the application-owned compatibility layer.
- [x] Add an application-owned launcher adapter that isolates recent-project
	and package-preview behavior behind a stable contract until ProjectFoundry
	exposes equivalent APIs.

	> `ProjectPackageAdapter` now normalizes project package paths and loads
	preview documents for both `FileWindow` and `ApplicationLauncher`; focused
	launcher and application export tests pass.
- [x] Update menus, actions, and window wiring to use application services rather
	than directly mutating tree or project internals.

	> Menu actions delegate imports and project commands to application
	controllers; no menu or window callback mutates Project registries directly.
- [ ] Remove or deprecate duplicate DMTools registries, serializers, and
	lifecycle callbacks only after replacement coverage exists.

	> Blocked for now: `ProjectSerializer`, `ProjectLifecycleService`, and
	`root_objects` are still the explicit legacy import and dual-format
	compatibility path. Removing or deprecating these surfaces would break
	supported migration behavior without a replacement contract.
- [x] Add deprecation boundaries and compatibility tests for legacy serializer,
	lifecycle, and root-registry entry points before removing duplicate paths.

	> `LegacyProjectCompatibility` now isolates the supported legacy serializer
		entry points from the ProjectFoundry lifecycle; lifecycle, migration, and
		workflow compatibility tests pass. The underlying legacy paths remain
		supported until a replacement import contract exists.
- [x] Update application package exports, dependency metadata, and developer
	documentation.

	> `application` lazily exports the launcher and controller, ProjectFoundry
	is pinned in `requirements.txt`, and the architecture documentation records
	the ownership and MDI contracts.
- [ ] Add distribution package metadata when a supported DMTools packaging
	target is defined.

	> No package metadata or supported distribution target exists in this
	repository, so adding one now would invent a deployment contract.
- [ ] Select and document a supported DMTools distribution target, then add
	minimal package metadata and a build validation task.

### Verification gates

- [x] Add a conversion fixture covering one complete DMTools project with roots,
	database data, imported objects, and editor metadata.

	> `test_conversion_fixture_round_trips_roots_database_objects_and_editor_metadata`
		covers the project roots, imported Compendium SQLite record, ProjectFoundry
		blocks, and saved-query projection metadata across save and reopen.
- [x] Test new project, open, save, reopen, save-as, project replacement, and
	shutdown workflows.

	> Lifecycle coverage plus `test_project_workflows.py` exercise all listed
	> project transitions, including Save As context rebinding and reopen.
- [x] Test UID integrity and cross-subsystem consistency across project, tree,
	blocks, and persisted SQLite data.

	> `test_uid_integrity_survives_project_tree_block_collection_and_sqlite_round_trip`
		verifies one entity UID across the persisted SQLite row, ProjectFoundry tree
		node, entity database block, saved query, collection, and reopened project.
- [x] Test generated Markdown and HTML against snapshot fixtures for each
	entity type, including stable reference links and CSS class names.

	> `fixtures_entity_rendering.json` and its focused test cover all supported
	> entity types, stable UID metadata, field markers, HTML classes, and UIDs.
- [x] Add GUI smoke coverage for opening an entity, following a spell/item/etc.
	link into another MDI inspection view, returning to the source, editing a
	Homebrew draft, cancelling it, and closing the views without leaked state.

	> `test_mdi_gui_smoke.py` exercises a real `QMdiArea`, UID link navigation,
		back navigation, MDI reuse, Homebrew Cancel cleanup, and subwindow shutdown.
- [x] Run focused migration tests after each ownership boundary changes.

	> Focused workflow, UID, rendering, database/editor, MDI-contract, and
		export checks passed during the migration; the complete suite and Ruff also
		pass after the latest changes.
- [x] Run the complete test suite and Ruff after the migration changes.

	> The full suite passes with 212 tests and 26 subtests; Ruff reports no
	violations.

## Completed Tasks

### Target architecture boundaries

- [x] Create the target package boundaries for `core`, `application`, `views`,
	and `editors` without moving behavior until the contracts are tested.
- [x] Add focused import-boundary coverage proving the new packages are
	importable without presentation side effects.

### Entity import workflows

- [x] Save the managed Compendium JSON data file after a successful XML import.
	Use the existing project serializer so the imported SQLite-backed entities and
	`data/compendium.json` remain synchronized without changing Homebrew imports.

	> Accepted XML imports targeting Compendium now trigger the active project save,
	which writes the namespace JSON file and project manifest atomically.

- [x] Define one canonical imported-entity record contract containing entity
	type, stable UID, source identity, display name, normalized model payload,
	source metadata, validation status, and provenance.
- [x] Define the supported entity type registry for `item`, `spell`, `race`,
	`class`, `subclass`, `monster`, `feat`, `background`, and `ability`, with
	`subclass` records owned by the existing `Classes` category.
- [x] Reuse the existing parser dispatcher for XML imports so every XML entity
	is parsed, adapted, validated by its Pydantic model, and validated against the
	corresponding JSON Schema before it can be committed.
- [x] Preserve parser failures per entity with source location/name, error
	details, and an import summary; block mixed batches by default, but allow an
	explicit user-confirmed skip policy to atomically commit only validated records.
- [x] Define the `Import from XML` application workflow: choose a source XML
	file, preview counts/errors, validate the complete batch, choose a destination
	Compendium, and commit only after confirmation.
- [x] Define the `Import from JSON` workflow for canonical normalized entity
	records and/or JSON arrays, including explicit detection of whether input is
	raw entity data, a parser result, or an existing DMTools export.
- [x] Validate JSON imports against the entity model and schema registry before
	creating database rows; reject unknown entity types and malformed records with
	actionable messages.
- [x] Keep XML parsing, JSON validation, model adaptation, database persistence,
	and Qt presentation in separate services/models/views.
- [x] Add import progress, cancellation, duplicate handling, and dry-run
	preview behavior through an application-level import service, including
	reading, source parsing, normalization, and validation phase feedback.
- [x] Add focused tests for successful XML import, successful JSON import,
	unsupported tags, malformed records, schema failures, duplicate identities,
	partial-batch rollback, cancellation, and repeat imports.

### Import menu commands

- [x] Add `Import from XML` to the appropriate File/Import menu and route it to
	an application controller rather than parsing in the menu callback.
- [x] Add `Import from JSON` beside the XML command and use the same validation,
	preview, commit, and error-reporting workflow.
- [x] Disable or guard import commands when no project/Compendium context is
	open.
- [x] Preserve the existing project window/menu composition and ensure import
	commands operate on the active ProjectFoundry project.
- [x] Add command-level tests that verify dialog cancellation performs no
	mutation and accepted imports create the expected project objects and nodes.

### Queryable Compendium databases

- [x] Choose the project-managed SQLite schema for entity databases, keeping
	SQLite as the source of truth and pandas as a display/editing layer only.
- [x] Create an entity-type table or equivalent normalized storage for each
	Compendium category while preserving the validated JSON model payload.
- [x] Store validated JSON/Pydantic model payloads in SQLite JSON columns and
	query their fields with the SQLite JSON1 extension (`json_extract`, JSON path
	expressions, and generated/indexed projections where appropriate).
- [x] Detect and clearly report unavailable JSON1 support before creating or
	querying entity storage; do not silently fall back to application-side JSON
	filtering.
- [x] Store stable entity UID, canonical name, entity type, source/provenance,
	normalized searchable fields, and serialized model payload.
- [x] Define indexes for common lookup fields, including item weight, spell
	level, monster challenge rating, race/class/feat/background/ability names,
	and shared references.
- [x] Define a safe field projection/query layer instead of allowing arbitrary
	UI-generated SQL to mutate entity tables.
- [x] Add a database block/artifact representation for each project-managed
	Compendium database and route creation through ProjectFoundry.
- [x] Make imports idempotent by stable source/entity identity, with explicit
	policies for replace, skip, duplicate, and merge.
- [x] Add query result models that retain entity UIDs so rows can open the source
	entity or be added to a Collection.
- [x] Add tests for schema creation, indexes, import persistence, query results,
	JSON1 field filtering/projection, malformed JSON paths, unavailable JSON1,
	duplicate policy, reopen behavior, and SQLite source-of-truth guarantees.

### Compendium quick queries

- [x] Define saved query metadata with name, entity type, filter expression,
	sort order, projection, and versioned query format.
- [x] Add built-in quick queries for item weight, spell level, monster challenge
	rating, and name/type searches.
- [x] Add category-specific query factories so invalid fields cannot be selected
	for an entity type.
- [x] Allow users to save, rename, duplicate, edit, and delete custom queries
	under a Compendium category.
- [x] Display query results in a model/view that supports sorting and selection
	without making pandas the canonical data store.
- [x] Add query context-menu actions for open entity, add to Collection, and
	copy/reference the stable entity UID.
- [x] Persist saved queries as ProjectFoundry-owned project data and restore
	them before dependent query views open.
- [x] Test query construction, validation, parameter handling, sorting,
	serialization, and stale/missing entity behavior.

### Collections

- [x] Add a persistent `Collections` root node separate from Compendium source
	data.
- [x] Define a Collection block/data model with stable UID, name, description,
	ordering, and UID-only references to Compendium or Homebrew entities.
- [x] Support creating, renaming, duplicating, deleting, and reordering
	Collections through ProjectFoundry application operations.
- [x] Support manually adding and removing entities from a Collection while
	preventing duplicate references and cross-project UIDs.
- [x] Support adding query results to a Collection as materialized membership,
	with an explicit distinction between a saved query and a captured result set.
- [x] Support optional dynamic Collections backed by a saved query, with clear
	refresh semantics and no accidental destructive synchronization.
- [x] Add Collection grouping/filtering by entity type, source, tags, and common
	fields without duplicating canonical entity payloads.
- [x] Add Collection table/view models that resolve entity UIDs lazily through
	the ProjectFoundry project and retain stable ordering.
- [x] Define behavior for deleted, replaced, or unavailable referenced entities.
- [x] Add tests for manual membership, query capture, dynamic refresh, ordering,
	duplicate prevention, stale references, save/reopen, and project replacement.

### Progress

JSON, database, table, and shopkeeper durable state no longer uses `ObjectData`;
direct payload/artifact state is synchronized through their ProjectFoundry
blocks. `ObjectBase` remains as a compatibility tree adapter until the full
ProjectData `EditedObject` migration is complete.

Entity detail inspection now prefers a UID-keyed modeless MDI view when a
QMdiArea host is available, while retaining the modal compatibility path for
non-MDI callers. Navigation reuses an existing inspection for the same UID and
preserves the existing canonical resolution and cycle checks.

Project lifecycle persistence now runs through an application-owned
compatibility service that preserves both legacy `roots` and ProjectFoundry
`framework` documents during create, save, and load. Durable DMTools wrappers
now use ProjectFoundry `EditedObject` identity under the `ProjectObject` and
`PayloadStore` names; the remaining temporary-draft and payload ownership
cleanup is still tracked in the incomplete object migration task.

- [x] Add a ProjectFoundry `Project` composition root to `ProjectController`.
- [x] Recreate the project on `new_project()` and release it through
	`ProjectController.close()`.
- [x] Add regression coverage for controller project ownership and reset.
- [x] Add stable UID and parent/child relationship fields to DMTools tree
	nodes so they can be registered with ProjectFoundry.
- [x] Expose the ProjectFoundry tree manager from `ProjectController` as the
	migration target while keeping the legacy tree projection active.
- [x] Expose a transitional ProjectFoundry-backed tree manager/model from
	`ProjectController`, mirrored from the legacy tree by stable node UID.
- [x] Wire the ProjectFoundry tree model into the main DMTools tree view after
	database/query registration and mutation routing were established.
- [x] Add a ProjectFoundry `DatabaseBlock` identity and register unowned
	database blocks in the transitional tree projection.
- [x] Register database and query block factories with ProjectFoundry and
	expose a transitional framework project-document export.
- [x] Verify database/query block serialization and UID relationship
	round-trip through ProjectFoundry.
- [x] Add a ProjectFoundry-backed JSON block with inline payload serialization
	and registry coverage.
- [x] Migrate table objects and disk-backed artifacts to ProjectFoundry block
	storage, with atomic CSV commits, artifact metadata/checksums, lazy loading,
	edit invalidation, failed-write rollback, cross-project rejection, and legacy
	project round-trip coverage.
- [x] Route database creation, editing, and deletion through
	`ProjectController` and synchronize the ProjectFoundry block registry.
- [x] Route query creation and deletion through `ProjectController` and keep
	database/query block relationships synchronized.
- [x] Route saved-query editing through `ProjectController` and synchronize
	the registered `QueryBlock` data.
- [x] Move query editor draft state into a dedicated Model/View/Factory
	workflow, with cancellation isolation and accepted updates routed through
	`ProjectController` for project-backed queries.
- [x] Add protected, stable-UID Compendium and Homebrew root/category
	hierarchies with canonical entity-type validation and legacy/framework
	serialization coverage.
- [x] Add canonical imported-entity records and XML/JSON dry-run validation with
	stable UIDs, per-record issues, duplicate policies, cancellation, progress,
	and single-call atomic commit gating.
- [x] Add project-managed SQLite JSON1 entity storage with transactional batch
	commits, indexed safe projections, UID-preserving query rows, duplicate
	policies, checksummed block metadata, and ProjectFoundry ownership.
- [x] Add guarded File/Import XML and JSON commands with a dedicated preview
	Model/View/Factory, application controller orchestration, cancellation
	isolation, and post-commit category node registration.
- [x] Run XML/JSON parsing and validation through the application-owned
	ProjectFoundry `QtTaskRunner`, show a modal Model/View/Factory loading dialog
	with live record progress and cooperative cancellation, and keep confirmation
	plus atomic project/SQLite commit on the GUI thread.
- [x] Keep mixed valid/invalid imports strict by default and provide an explicit
	preview option to skip reported invalid or unsupported records while atomically
	committing only the already validated records.
- [x] Add versioned, ProjectFoundry-owned saved entity query blocks with built-in
	weight/level/challenge/name queries, safe category factories, UID-preserving
	execution, and controller CRUD operations.
- [x] Add a protected Collections root and ProjectFoundry Collection blocks with
	ordered UID-only membership, manual/captured/dynamic workflows, lazy entity
	resolution, stale-reference reporting, and serialization coverage.
- [x] Add validated Homebrew draft/editor Model/View/Factory workflows with
	separate SQLite ownership, Project-routed CRUD, identity-preserving edits,
	and explicit Compendium-copy provenance.
- [x] Add a sortable UID-preserving query result Model/View/Factory with
	Project-routed open, add-to-Collection, and copy-UID context actions.
- [x] Add Project-routed Collection reordering and a lazy UID-backed Collection
	table Model/View/Factory with source/type/tag/text filters and stable grouping.
- [x] Persist the ProjectFoundry document inside the project package and restore
	entity databases, saved queries, relationships, and Collections before their
	dependent result views open.
- [x] Add canonical UID/type/namespace entity references, structured import
	normalization with unresolved diagnostics, reusable hyperlink delegates, and
	history-aware navigation with cycle and cross-namespace validation.
- [x] Adapt Shopkeeper durable configuration to a ProjectFoundry block with
	validated database/query UIDs, framework serialization, and controller-owned
	registration/removal while retaining legacy project import compatibility.
- [x] Pin ProjectFoundry 0.3.0 to the verified source commit and document the
	DMTools ownership map, package boundaries, composition order, compatibility
	policy, and explicit exclusion of `sceneTable`.
- [x] Replace destructive ProjectFoundry tree reconstruction with incremental
	synchronization that preserves canonical structural and imported entity node
	identity across unrelated object and Collection refreshes.
- [x] Introduce ProjectFoundry `ProjectContext` and `ProjectService` at the
	application boundary, with tested create/save/replacement/load/close ownership
	and dirty-state lifecycle.
- [x] Add lightweight launcher Compendium/Homebrew/Collection counts and
	explicit created/updated/skipped/duplicate/invalid/unsupported import summaries.
- [x] Expose UID-safe `Clone to Homebrew` actions from entity detail and query
	result views, preserving the Compendium source and routing clones through the
	existing Homebrew editor callback; the remaining modeless MDI editor workflow
	and end-to-end inspection/edit coverage remain pending below.

- [x] Complete modeless Homebrew editor close lifecycle cleanup so explicit
	cancel and window close release callbacks and temporary draft state after
	accepted or abandoned edits.
- [x] Add deterministic, UID-backed Markdown and escaped HTML inspection
	renderers as pure derived views over canonical entity records, with focused
	coverage for nested data, optional values, and untrusted text.

### Latest Verification

- Import parsing, skip-invalid preview, and controller focused tests: 23 passed.
- Full test suite: 184 passed and 26 subtests passed; 26 expected-unavailable
	cases skipped.
- Ruff: full repository check passes using the explicit `ruff.toml` baseline.
- VS Code diagnostics: no errors in migration-touched files.

## Out of Scope for the Initial Conversion

- Replacing the DMTools scene view with ProjectFoundry `sceneTable`.
- Rewriting schemas or generated files under `schemas/bundled`.
- Redesigning database import formats or domain-specific editors before their
	ownership contracts are established.
- Broad UI restyling unrelated to the ProjectFoundry composition migration.
