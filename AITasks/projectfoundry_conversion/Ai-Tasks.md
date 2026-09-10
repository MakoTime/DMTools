# DMTools ProjectFoundry Conversion

## Goal

Adopt ProjectFoundry as the application foundation for DMTools while preserving
DMTools' scene-oriented workflow. Use ProjectFoundry for project packages,
project context, registries, nodes, lifecycle, serialization, and scene
membership. Do not introduce the ProjectFoundry `sceneTable` UI; the scene view
and existing DMTools database/tree views remain the primary presentation.

The LFCube conversion is the reference implementation for structure and
ownership boundaries. DMTools-specific database objects, importers, schemas,
and editors should become adapters on top of the framework rather than a second
project architecture.

## Current Baseline

- DMTools already depends on ProjectFoundry from GitHub in `requirements.txt`.
- Project state is currently coordinated by `application.ProjectController` and
	`application.ProjectSerializer`.
- Tree nodes and roots are implemented under `components.tree`.
- Project objects and payload persistence are implemented under `objects`.
- The main window and project launcher are composed directly in `main.py` and
	`application.file_window.py`.
- Scene behavior exists, but project objects, tree nodes, and view state are
	still coupled through DMTools-owned conventions.

## Migration Tasks

### P0 - Establish the target architecture

- [ ] Document the DMTools-to-ProjectFoundry ownership map, using LFCube as the
	structural reference.
- [ ] Pin or otherwise define the ProjectFoundry version/source used by DMTools
	and verify the required APIs against the local checkout.
- [ ] Create the target package boundaries for `core`, `application`, `views`,
	and `editors` without moving behavior until the contracts are tested.
- [ ] Define the composition order for project context, registries, tree
	manager/model, scene model/adapter, serializers, and Qt views.
- [ ] Preserve the existing Model/View/Factory dialog pattern for all migrated
	editors.

### P0 - Move project ownership to ProjectFoundry

- [ ] Replace the DMTools-owned project controller/serializer orchestration
	with ProjectFoundry `Project`, `ProjectContext`, `ProjectService`, and
	project package APIs where applicable.
- [ ] Make ProjectFoundry registries the canonical lookup path for project,
	object, block, node, and relationship identities.
- [ ] Define stable UID-backed DMTools records and remove long-lived references
	to live Qt widgets, pandas objects, or transient scene objects.
- [ ] Migrate new, open, save, save-as, recent-project, and close workflows to
	the ProjectFoundry project lifecycle.
- [ ] Preserve compatibility for current DMTools project files through an
	explicit import/migration step rather than silently changing their meaning.

### P0 - Convert the tree and node model

- [ ] Map `components.tree` roots, nodes, and models onto ProjectFoundry tree
	contracts while preserving DMTools root categories and context menus.
- [ ] Define which DMTools concepts are ProjectFoundry blocks, nodes, or
	application-only commands.
- [ ] Route create, rename, move, delete, and duplicate operations through the
	project/application service boundary.
- [ ] Persist tree hierarchy and node state as UID-based project data.
- [ ] Add tests for node registration, parent/child relationships, duplicate
	names, deletion, project replacement, and reload.

### P1 - Convert DMTools objects and data persistence

- [ ] Adapt JSON, table, database, query, and shopkeeper objects to the
	ProjectFoundry block/data lifecycle where they have durable project state.
- [ ] Keep SQLite as the source of truth; treat pandas and other tabular
	representations as temporary display/editing layers.
- [ ] Separate persistent block metadata from large or external payloads and
	artifacts, using ProjectFoundry artifact metadata and storage contracts.
- [ ] Make importers write project-managed SQLite/data artifacts through an
	application service instead of exposing external files as project state.
- [ ] Register DMTools object types with a framework type/serializer registry and
	reject unknown types with actionable migration errors.

### P1 - Preserve and simplify the scene workflow

- [ ] Make the ProjectFoundry scene model/adapter the canonical scene state and
	membership mechanism.
- [ ] Keep the existing DMTools scene view as the primary scene presentation;
	do not add or restore `sceneTable`.
- [ ] Define explicit scene object creation, refresh, visibility, and removal
	events, with updates occurring only after successful state changes.
- [ ] Keep scene objects and rendered actors separate from persistent blocks and
	tree nodes; store only stable UID references in project data.
- [ ] Restore scene membership during project load through explicit loading
	APIs, and release scene/renderer resources during project replacement and
	shutdown.
- [ ] Add focused tests for scene reload, visibility, object removal, failed
	processing, and repeated shutdown.

### P1 - Rebuild application and editor boundaries

- [ ] Move startup composition and project commands out of `main.py` into an
	application-level service/composition boundary.
- [ ] Keep Qt views responsible for layout, signals, selection, and presentation
	refresh; keep mutations in models/services.
- [ ] Convert database, query, table, and object editors to dedicated
	`model.py`, `view.py`, and `factory.py` modules using the existing dialog base
	classes.
- [ ] Ensure editor state is temporary and validated, then applied through
	ProjectFoundry-backed application operations.
- [ ] Ensure cancel, apply, editor destruction, and project replacement release
	temporary objects and callbacks cleanly.

### P2 - Migrate project UI and remove duplicate infrastructure

- [ ] Adapt the file/project launcher to ProjectFoundry project package and
	recent-project contracts while retaining the DMTools preview experience.
- [ ] Update menus, actions, and window wiring to use application services rather
	than directly mutating tree or project internals.
- [ ] Remove or deprecate duplicate DMTools registries, serializers, lifecycle
	callbacks, and scene bookkeeping only after replacement coverage exists.
- [ ] Update package exports, dependency metadata, and developer documentation.

### P0 - Verification gates

- [ ] Add a conversion fixture covering one complete DMTools project with roots,
	database data, imported objects, scene state, and editor metadata.
- [ ] Test new project, open, save, reopen, save-as, project replacement, and
	shutdown workflows.
- [ ] Test UID integrity and cross-subsystem consistency across project, tree,
	blocks, scene objects, and persisted SQLite data.
- [ ] Run focused migration tests after each ownership boundary changes.
- [ ] Run the complete test suite, Ruff, and a desktop GUI smoke test with the
	scene view, while documenting any platform-specific PySide6/PyVista limits.

## First Implementation Slice

1. Add a DMTools architecture/ownership test fixture that can create an empty
	 ProjectFoundry project and expose its project context, tree manager, and
	 scene model to DMTools.
2. Adapt one low-risk object type and one tree root to the new registry and
	 serialization contracts.
3. Wire the existing main window to the new context without adding `sceneTable`.
4. Prove new/save/reopen plus scene restoration, then use that slice as the
	 template for database and importer objects.

## Out of Scope for the Initial Conversion

- Replacing the DMTools scene view with ProjectFoundry `sceneTable`.
- Rewriting schemas or generated files under `schemas/bundled`.
- Redesigning database import formats or domain-specific editors before their
	ownership contracts are established.
- Broad UI restyling unrelated to the ProjectFoundry composition migration.
