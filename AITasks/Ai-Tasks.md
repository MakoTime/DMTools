# DMI Class Progression Table Editor

## Objective

Add a table editor button to the DMI entity dialog. The button opens a window
where the user can configure class resources and progression columns, edit the
values shown for each class level, and change the column order. Saving the
editor must update the class raw JSON data so the configuration is preserved
when the entity is rendered, reopened, or edited again.

User-configured table metadata is the authority for the editable presentation.
Do not solve this by adding a separate hard-coded extraction branch for every
class. Existing XML/API data can seed defaults, but it must remain possible for
the user to define resources that cannot be extracted generically.

## Implementation Tasks

- [x] Locate the DMI entity dialog and identify its model, view, factory,
	controller, entity payload, and persistence path. Confirm which object owns
	the canonical raw class JSON and which renderer consumes progression data.

- [x] Define a persisted table-configuration schema for class JSON. Include a
	stable table identifier, ordered columns, stable column keys, display names,
	column type/source, level-indexed values, optional formulas or notes, and
	visibility state where needed. Preserve unknown JSON fields and existing
	class feature data.

- [x] Define compatibility behavior for classes with no saved configuration,
	partially configured tables, invalid data, and older payloads. Existing
	default progression rendering must continue to work when no custom table is
	present.

- [x] Implement a progression-table editor model following the existing dialog
	model conventions. It must own a detached draft, support adding/editing/
	removing columns, edit level values, reorder columns, validate input, and
	expose an accepted configuration without mutating the source entity before
	acceptance.

- [x] Implement the table editor view and factory using the existing editor
	base classes. Provide controls for resource/progression columns, level
	values, labels, visibility, and column ordering. Keep Qt layout and signal
	handling in the view and keep domain validation in the model.

- [x] Add the table-editor button/action to the DMI entity dialog. Open the
	editor with the selected class and its current configuration, route accepted
	data through the existing controller/service boundary, refresh the entity
	display after saving, and leave the entity unchanged on cancel.

- [x] Persist accepted table configuration into the canonical raw class JSON
	through the existing entity/project serializer. Preserve unrelated fields,
	source metadata, feature order, and unknown values. Make persistence
	atomic or rollback-safe so a failed save cannot replace a previously valid
	configuration.

- [x] Update progression-table generation and Markdown/HTML rendering to use
	the persisted configuration when present. Render columns in the saved order,
	include custom resource/progression values, omit disabled columns, and keep
	the existing default renderer for unconfigured classes.

- [x] Define import and reimport behavior. Existing imported data may seed a
	default table, but reimport must not silently overwrite a user-configured
	table. Keep generic shared parsing where possible and avoid class-specific
	extraction as the required mechanism for adding a resource column.

- [x] Add focused tests for the configuration schema and round-trip JSON,
	editor-model validation and cancel behavior, column reordering, DMI button
	integration, persistence failure rollback, rendering order, custom
	resources, default rendering, and import/reimport preservation.

- [x] Validate the complete workflow with representative classes that have
	different resource patterns, including spell slots, formulas, dice-based
	resources, and recharge/reset text. Run focused tests first, then the full
	suite and diagnostics for changed files.

## Completion Criteria

- [x] A user can open the table editor from the DMI entity dialog.
- [x] A user can add or edit resource/progression columns and reorder them.
- [x] Saving changes the canonical raw JSON data, including the custom order.
- [x] Reopening and rendering the entity uses the saved configuration.
- [x] Cancelling leaves the entity and JSON unchanged.
- [x] Existing classes without custom configuration retain current behavior.
- [x] No per-class hard-coded extraction is required for user-defined columns.
