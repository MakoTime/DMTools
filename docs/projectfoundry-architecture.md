# DMTools ProjectFoundry Architecture

## Framework Baseline

DMTools targets ProjectFoundry 0.3.0 from
`https://github.com/MakoTime/ProjectFoundry.git` at commit
`8f75666c855be598fd5ac6bea3d4b435dfca49e4`. The dependency is pinned in
`requirements.txt`. The verified installation exports `Project`,
`ProjectContext`, `ProjectService`, `SerializerRegistry`, and `ArtifactStore`.

The ProjectFoundry `sceneTable` presentation and separate scene subsystem are
intentionally out of scope. DMTools uses its MDI presentation workflows.

## Ownership Map

| Concern | Canonical owner | DMTools adapter or compatibility layer |
| --- | --- | --- |
| Project lifetime and registries | ProjectFoundry `Project` | `application.ProjectController` |
| Block type construction | ProjectFoundry `SerializerRegistry` | registrations in `ProjectController` |
| Persistent block data | ProjectFoundry `BlockObject` and `BlockData` | classes under `objects/` |
| Large generated data | ProjectFoundry `ArtifactStore` | table CSV and entity SQLite stores |
| Entity records | project-managed SQLite | `application.entity_database` |
| Tree identity and hierarchy | ProjectFoundry tree/node registries | `application.project_tree` projection |
| Editor drafts | dialog models | `dialog/*/model.py` |
| Accepted workflows | application controllers/services | `application/` and `application/controllers/` |
| Qt layout and interaction | views | `dialog/*/view.py` and `components/tree/view.py` |
| View construction | factories | `dialog/*/factory.py` |
| Legacy project import | DMTools legacy serializer | `application.project_serializer` |

## DMTools Concept Mapping

| DMTools concept | ProjectFoundry representation | Ownership rule |
| --- | --- | --- |
| Database, query, JSON, table, and shopkeeper data | ProjectFoundry block and block data | The block UID is the durable identity; payloads use artifact metadata when they are large or external. |
| Compendium and Homebrew entity database | Entity-database block plus project-managed SQLite artifact | SQLite rows are the source of truth; tree nodes reference entity UIDs. |
| Collection and saved entity query | Collection or entity-query block | Entity and query relationships are stored as UIDs and validated by the application controller. |
| Compendium, Homebrew, Databases, and Collections categories | ProjectFoundry tree nodes projected from DMTools root definitions | Root/category nodes are structural and protected; they do not own durable payloads. |
| Imported entity or block tree entry | ProjectFoundry tree node with `object_uid` | The node identifies placement and display state; the block or SQLite row owns the data. |
| Import, search, refresh, open, and query commands | Application/controller operations | Commands coordinate workflows and must not become persistent blocks or tree payloads. |
| Qt models and views | Runtime presentation objects | They resolve canonical UIDs for an interaction and are never serialized as project state. |

Long-lived relationships are UIDs. Views and Qt models may resolve them for one
interaction, but may not mutate Project registries or persist live Qt or pandas
objects.

## Package Boundaries

- `models/`, `schemas/`, and parser normalization are domain/data contracts and
  do not depend on Qt or ProjectFoundry views.
- `objects/` contains ProjectFoundry block/data adapters. Legacy object wrappers
  remain only for explicit old-project import until their callers are migrated.
- `application/` owns project composition, persistence, imports, queries,
  references, and accepted mutations.
- `dialog/` contains editor and workspace Model/View/Factory packages. Draft
  models are temporary; views synchronize widgets; factories construct views.
  MDI-hosted views follow separate structural contracts for read-only entity
  inspection, editable drafts, database workspaces, and entity query results.
- `components/tree/` is a transitional compatibility projection. Canonical
  identity and relationships live in the ProjectFoundry project.
- Core/domain modules must not depend on PySide6, PyVista, views, or renderer
  actors.

## Composition Order

1. Create the serializer registry and register every supported block type.
2. Create `ArtifactStore` for the selected project directory.
3. Create a fresh ProjectFoundry `Project` as the composition root.
4. Load and validate framework blocks and UID relationships.
5. Construct Qt tree/table models over those project-owned managers.
6. Construct application services and editor controllers.
7. Construct views and connect commands to application controllers.

On replacement, build and validate the candidate project first, switch models
and adapters to it, then shut down the previous project. On close, unsubscribe
subsystems before shutting down the Project.

## Persistence And Compatibility

`project.json` currently carries both the legacy `roots` document and the
ProjectFoundry `framework` document. The framework document is authoritative
for migrated blocks, relationships, and nodes. The legacy document remains an
explicit compatibility input while legacy object wrappers still exist.

New project-managed SQLite and artifact files live below the project directory.
External XML, JSON, SQL, and database files are inputs and are never persisted
as canonical external paths for migrated data.

## Verification Status

Project lifecycle, UID round trips across project/tree/block/SQLite projections,
and deterministic Markdown/HTML rendering are covered by focused tests and the
full Python suite. No separate scene fixture or GUI smoke gate is required for
the supported MDI presentation workflow.