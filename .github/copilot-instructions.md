# DMTools Agent Instructions

- Follow the project's Model, View, Factory dialog pattern for new dialog and workspace features.
- Keep domain and editable state in a model, keep Qt layout and event handling in a view, and construct views through a factory that accepts the model.
- Embedded workspace editors should inherit from `dialog/base/widget_editor/WidgetEditorView`; modal editors should use the popup base and tab-hosted editors should use the tab base.
- Prefer the existing PySide6 and project patterns over introducing a parallel UI architecture.
- Keep SQLite as the source of truth; pandas is a temporary display/editing layer.
- External SQL or database files are import inputs. Persist only the generated project-managed SQLite file under the project's `data` directory.

<!-- Project Foundry managed instructions -->
<projectfoundry>
# Project Foundry development instructions

## Architecture

- Treat `Project` as the authoritative composition root for one project.
- Keep `Project` independently constructible for tests and tooling.
- Use `ProjectManager` for application-level active-project or singleton behavior.
- `Project` owns persistent blocks and project-wide lifecycle; scene/table and editor objects are runtime objects.
- Route add, remove, connect, rename, scene, and task mutations through `Project` APIs.
- Base classes may expose ergonomic methods, but those methods must delegate to `Project`.
- Do not let views, Qt models, or adapters mutate registries or persistent relationships directly.
- Keep application services above `Project`: services coordinate workflows, while `Project` owns domain invariants and canonical mutations.
- Keep editor controllers above services: controllers open editors, pass target context, handle accept/cancel, and forward validated models.
- Do not make a generic service or controller a second composition root; domain-specific workflows belong in application-level subclasses or compositions.

## UID relationships

- Store long-lived relationships as UIDs, never as object references.
- Resolve related objects through `Project` or a project-owned registry at the point of use.
- Use `block_uid` for persistent references from tree and scene/table state to block data.
- Reject duplicate UIDs, missing UIDs, cross-project references, and invalid relationships clearly.
- Validate relationships before mutating either side; failed operations should leave state unchanged.
- Temporary local object references are acceptable inside one operation, task, editor session, scene session, or callback.
- Serialization must persist UIDs, not memory addresses or runtime UI objects.
- Do not serialize temporary editor objects, scene objects, Qt rows, or renderer actors.
- For block editors, distinguish `block_uid` (canonical target), `node_uid` (tree launch context), `scene_uid` (scene-table launch context), and `parent_node_uid` (new-item creation context).
- Do not use one ambiguous target UID when the source namespace matters.

## Block objects

- `BlockObject` owns the persistent block data and metadata for disk-backed output artifacts.
- `prepare()` gathers and validates processing inputs without mutating committed output state.
- `process(prepared, progress_callback)` performs computation from prepared inputs.
- `process()` must not mutate registries, tree state, scene state, or committed block output.
- `commit(result)` atomically persists successful output artifacts and updates committed block metadata.
- Run `commit()` only after successful processing; failed processing must not partially commit.
- Keep large meshes, lines, and other shape data in separate disk-backed artifacts, not in project memory or the main project document.
- Store artifact path, format, version, checksum, and validity metadata with the block data.
- Load block artifacts lazily by `block_uid` when a scene object needs them.
- Preserve the previous valid artifact if processing or artifact persistence fails.
- A successful commit validates the block; invalid dependencies must be processed first.
- Detect missing block tasks and dependency cycles before execution.
- Child and parent block relationships must be created through `Project` or inherited project-aware methods.

## Editor objects

- `EditedObject` is a temporary edited object created from block data when an editor opens.
- Apply validated editor changes back to the relevant block through `Project` or block APIs.
- Destroy the edited object after apply, cancel, or editor close.
- Do not store editor-only state on `BlockObject` or serialize the edited object.

## Dialogs and mixins

- Every dialog feature has separate `model.py`, `view.py`, and `factory.py` modules.
- Popup/dialog editors and tab editors have separate model, view, and factory implementations.
- Dialog and tab models inherit their appropriate base editor model.
- Dialog and tab views inherit the shared editor view contract and their native Qt widget.
- Use mixins for shared apply, close, button-box, naming, and editor behavior.
- Models contain domain state, validation, and Project interaction.
- Views contain Qt widgets, layout, and widget-to-model synchronization.
- Factories construct and configure the correct model/view presentation.
- Dialogs must not create or register domain items directly when a Project API exists.
- Editor models hold draft state and validation; applying a dialog must not partially mutate Project state.
- Editor views synchronize widgets into models; they do not own domain workflows.
- Reusable editor controllers should own dialog lifecycle and accepted-model delivery, not domain-specific block creation.

## Dependency direction

- Keep the import graph one-way: core, models, adapters, views, then application composition.
- `core` must not import PySide6, PyVista, views, dialogs, or application modules.
- Tree, scene, table, task, and dialog models may depend on core and `Project`.
- Qt models may depend on core and subsystem models, but not on views.
- PySide6 and PyVista code belongs in explicit adapters, views, or templates.
- PyVista adapters own runtime actors, not canonical domain objects.
- Factories may import their views; views must not import their factories.
- Use protocols or small contracts at subsystem boundaries to avoid circular imports.
- Application composition is responsible for wiring Project, models, adapters, views, and dialogs together.
- Main windows should compose dependencies and wire commands, but should not coordinate create/edit/process workflows.
- Use application-level controllers and services for New/Edit commands from root nodes, tree nodes, and scene-table rows.

## Tree, scene, and table

- `TreeManager` owns tree roots and hierarchy; `TreeNode` stores UID relationships.
- `TreeModel` delegates edits and mutations through `Project`.
- One coupled scene/table manager owns scene membership, table state, and temporary scene objects.
- Persist scene/table state separately using `block_uid`; do not persist mesh, line, or other shape payloads there.
- Create a temporary scene object when a block is added to the scene or when persisted scene state is restored at startup.
- Fetch shape data from the block's disk-backed artifact through `block_uid`.
- Keep the scene and table alive for the same duration as the project.
- Release temporary scene objects and loaded shape data during project shutdown.
- Keep the Qt table model as a presentation adapter over the coupled scene/table manager.
- Renderer actors are runtime resources owned by the rendering adapter, not by blocks or table rows.
- The canonical block name is the source for synchronized tree and scene-table display names; projections must not become independent name owners.

## Events and lifecycle

- Emit Project events only after successful mutations.
- Events identify affected UIDs and related UIDs where applicable.
- Do not emit success events for failed or rolled-back operations.
- The scene/table manager responds to block output, invalidation, scene-added, scene-object-created, scene-object-refreshed, and scene-object-removed events.
- Blocks must not create or destroy scene objects.
- Renderer adapters respond to scene/table lifecycle events and own actor cleanup.
- Subsystems must unsubscribe from a Project when it is shut down.
- Removal must clean dependent tree, scene/table, task, block, and UID references.
- Repeated removal and destruction should be deterministic and harmless where practical.
- Keep Qt/PyVista mutations on the GUI thread; worker threads may prepare and process data but must not commit, emit UI-facing project events, or update actors.
- Explicitly stop timers and close/finalize embedded VTK render windows before dialog destruction; prevent queued preview renders after close.

## Serialization

- Serialize block data and artifact metadata as the primary project data.
- Serialize tree state and coupled scene/table state as separate sections.
- Store only `block_uid` references between those sections.
- Load and validate blocks before loading tree or scene/table state.
- Validate missing, duplicate, stale, and cross-project UIDs before mutating project state.
- Use atomic writes and preserve rollback when project persistence or loading fails.

## Testing

- Add focused tests for lifecycle, dependency, serialization, ownership, UID, and model behavior.
- Test success, failure, cancellation, invalidation, duplicate UID, missing reference, cycle, and cross-project cases.
- Test both standalone compatibility and project-backed paths during migrations.
- Add integration coverage for one complete item across object, block, node, scene, table, task, dialog, and serializer layers.
- Run the full test suite and Ruff before marking a task complete.
- Do not mark a task complete until relevant focused tests and full regression checks pass.
- Exercise complete application workflows, not only isolated models: New, tree Edit, scene-table Edit, processing, scene insertion, save/reopen, cancellation, and shutdown.
</projectfoundry>
<!-- End Project Foundry managed instructions -->
