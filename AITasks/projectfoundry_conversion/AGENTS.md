# ProjectFoundry Conversion Agent

## Mission

You are an autonomous backlog implementation agent.

Your job is to execute `AITasks/projectfoundry_conversion/Ai-Tasks.md`.

A single agent run may contain many tasks.

Do not stop after completing a task.

Do not stop after completing a section.

Do not stop merely because tests pass.

After completing every task, update `Ai-Tasks.md`, re-read it, and immediately begin the next locally actionable unchecked task.

Only stop when:
1. No locally actionable unchecked tasks remain; or
2. There is no remaining work that can be performed because of a genuine external blocker or execution limit.

The current task is never the stopping condition.

## Authoritative Task Plan

The living implementation plan is:

`AITasks/projectfoundry_conversion/Ai-Tasks.md`

Before starting substantial work:

1. Read this file.
2. Read the current `Ai-Tasks.md`; it may have been updated by another agent or by the user.
3. Select the highest-priority incomplete task that is locally actionable.
4. Inspect the relevant implementation, tests, and framework API before editing.
5. Complete one coherent task and validate it before moving on.

After every completed task:

1. Update `Ai-Tasks.md`.
2. Mark the completed task `[x]`.
3. Save the task-list change.
4. Re-read `Ai-Tasks.md`.
5. Select the next highest-priority incomplete task that is locally actionable.
6. Continue working immediately.

When implementation reveals new work, update `Ai-Tasks.md` with a concrete task.

Mark work complete only after the relevant tests pass and the task's acceptance criteria are satisfied.

The requested feature scope now includes XML/JSON entity imports, Compendium and Homebrew category roots, queryable entity databases, Collections, and UID-resolved links between entities. Treat those as first-class migration requirements, not as optional UI polish.

## Task Execution Contract

Each unchecked checkbox (`- [ ]`) in `Ai-Tasks.md` is an independent implementation task.

Section headings are organizational only. Completing an entire section is not required before continuing, and completing one checkbox is not sufficient reason to stop.

For each task:

1. Read the complete task description and its acceptance criteria.
2. State one local hypothesis about the controlling code path.
3. Identify one cheap test that could disconfirm the hypothesis.
4. Inspect only the relevant implementation, tests, and framework APIs needed for the task.
5. Make the smallest coherent edit that satisfies the task.
6. Immediately run the narrowest relevant test.
7. Repair failures caused by the change.
8. Run the relevant broader test suite.
9. Run diagnostics on changed files.
10. Confirm the task's acceptance criteria are satisfied.
11. Update `Ai-Tasks.md`.
12. Mark the completed checkbox `[x]`.
13. Re-read `Ai-Tasks.md`.
14. Continue to the next incomplete locally actionable task.

Do not treat a passing test as the end of the task-list workflow.

Do not treat a completed task as the end of the agent run.

## Continuous Execution Rule

The agent MUST continue after completing a task whenever another locally actionable unchecked task remains.

The following are NOT valid reasons to stop:

* one task has been completed;
* one implementation unit has been completed;
* one section has been completed;
* focused tests pass;
* the full test suite passes;
* lint passes;
* diagnostics are clean;
* no additional work was discovered during the current task;
* the current implementation looks complete;
* the repository is currently clean.

After completing any task, the next action must be to inspect `Ai-Tasks.md` and determine whether another incomplete task can be started.

If another locally actionable task exists, begin it immediately.

Do not provide a final progress report between tasks unless the user explicitly asks for a report or pause.

## Task Selection

Work through `Ai-Tasks.md` in its existing dependency/order structure.

Always select the highest-priority incomplete task that is locally actionable.

Do not skip an earlier incomplete task merely because a later task looks easier or more interesting.

If the current task is blocked:

1. Determine whether the blocker is genuinely external or requires information unavailable in the repository.
2. Record the blocker in `Ai-Tasks.md`.
3. Leave the blocked task unchecked.
4. Re-read `Ai-Tasks.md`.
5. Select the next locally actionable incomplete task.
6. Continue working.

A blocked task does not justify stopping the entire work session when other tasks remain actionable.

## Newly Discovered Work

When implementation reveals additional work:

1. Add a concrete unchecked task to the appropriate location in `Ai-Tasks.md`.
2. Keep the new task separate from the task currently being completed.
3. Do not mark the discovered task complete unless it has actually been implemented and validated.
4. Finish and validate the current task.
5. Update `Ai-Tasks.md`.
6. Re-read `Ai-Tasks.md`.
7. Continue with the next incomplete locally actionable task.

Do not use newly discovered work as a reason to abandon the current task.

## Repository Rules

Repository root:

`C:\Users\benve\Documents\Programming\DMTools\`

Relevant conversion paths:

```text
DMTools/
├── application/
│   ├── controllers/db_controller.py
│   ├── file_window.py
│   ├── project_controller.py
│   ├── project_serializer.py
│   ├── project_version.py
│   └── project_tree.py
├── components/tree/
│   ├── model.py
│   ├── search.py
│   ├── view.py
│   └── roots/
├── dialog/
│   ├── base/{editor,popup_editor,tab_editor,widget_editor}/
│   ├── database/{factory.py,model.py,view.py}
│   └── db_base/{factory.py,model.py,view.py}
├── objects/
│   ├── database_object.py
│   ├── json_object.py
│   ├── object_base.py
│   ├── query_object.py
│   ├── shopkeeper_object.py
│   └── table_object.py
├── schemas/
├── tests/
├── main.py
└── requirements.txt
```

Reference projects are available locally:

* ProjectFoundry: `C:\Users\benve\Documents\Programming\ProjectFoundry\`
* LFCube: `C:\Users\benve\Documents\Programming\LFCube\`

Inspect their current source rather than assuming APIs from memory.

## Current Migration State

The repository contains partial ProjectFoundry migration groundwork, including transitional project ownership, UID-backed tree projection, framework block registration, and compatibility serialization.

The exact set of completed features is maintained in `Ai-Tasks.md`; do not infer completion of a task from this section.

Preserve existing migration work while extending it.

In particular, keep the legacy DMTools serializer and tree available for compatibility and migration until their ProjectFoundry replacements have an explicit import path, round-trip coverage, and verified lifecycle behavior.

## Architecture Rules

### ProjectFoundry ownership

* Treat ProjectFoundry `Project` as the canonical composition root for migrated project state.
* Use application services/controllers above `Project` for workflows.
* Do not let Qt views, Qt models, or adapters mutate Project registries directly.
* Route add, remove, rename, connect, scene, and task mutations through Project/application APIs.
* Keep long-lived relationships as UIDs, not object references.
* Reject duplicate UIDs, missing UIDs, cross-project ownership, and invalid relationships before mutating state.
* Emit or forward lifecycle events only after successful mutations.

### Objects, blocks, and editors

* Durable DMTools data belongs in ProjectFoundry-backed blocks and block data.
* Temporary editor state belongs in editor models, not persistent blocks.
* Large payloads and generated outputs belong in disk-backed artifacts with metadata; do not place large pandas frames or meshes in the project document.
* Keep SQLite as the source of truth. Pandas is a temporary display/editing layer.
* External database/SQL files are import inputs. Persist generated, project-managed SQLite data under the project data area.
* Preserve the existing Model/View/Factory pattern:

  * models own editable state and validation;
  * views own Qt widgets, layout, and signal handling;
  * factories construct views from models;
  * application controllers own accepted editor workflows.

### Tree and scene

* ProjectFoundry owns migrated node registries and UID-backed hierarchy.
* DMTools root categories and context-menu behavior must remain available.
* Keep persistent block identity, tree-node identity, scene-object identity, and renderer actor identity distinct.
* The existing DMTools scene view remains primary.
* Do not add a ProjectFoundry `sceneTable` UI.
* Scene membership must be represented through ProjectFoundry scene contracts or a DMTools adapter over them, not through persistent object-owned scene state.
* Scene and renderer resources must be released on project replacement and close.

### Serialization and compatibility

* ProjectFoundry serialization should store blocks, UID relationships, tree state, and scene state separately.
* Preserve the legacy DMTools project format until an explicit migration/import path and round-trip tests exist.
* Never silently reinterpret existing project files.
* Unknown serialized types must produce clear errors.
* Load and validate blocks before dependent tree or scene state.
* Preserve rollback when project loading fails.
* Do not edit generated files under `schemas/bundled`; modify source schemas and regenerate only through the project generator when schema work is required.

## Validation Commands

Use the workspace interpreter because `pytest` may not be on PATH:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_project_objects.py
.\.venv\Scripts\python.exe -m pytest -q
```

Run focused tests for the touched subsystem first, then the full suite before marking a migration task complete.

Ruff is required by the project instructions, but may need to be installed in the active environment before use:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

If a command is unavailable, report that fact and continue with available executable validation.

Do not claim lint success when Ruff was not installed or was not run.

## Diagnostics

After completing each task, inspect diagnostics for changed files.

Fix errors introduced by the current changes before moving on.

Do not claim diagnostics are clean unless they were actually checked.

## Scope Control

Work within the existing architecture and task requirements.

Do not redesign existing schemas, parsers, models, or project structure unless:

* the current task explicitly requires it; or
* a real implementation gap prevents the task from being completed.

Prefer small, focused changes that integrate with existing code.

Do not modify unrelated user changes.

Do not perform broad refactors while a focused migration boundary is still untested.

## Completion Criteria

A migration task is complete only when:

* the ownership boundary is explicit;
* UID relationships and cross-project behavior are tested;
* success and failure paths leave consistent state;
* persistence or migration behavior has focused round-trip coverage;
* relevant tests pass;
* the full suite passes;
* changed files have no diagnostics;
* `Ai-Tasks.md` reflects the actual state;
* no `sceneTable` UI was introduced;
* no generated schema artifacts were edited directly.

These criteria apply to each task where relevant.

They do not mean the agent should stop after satisfying them.

After satisfying the criteria for one task, continue to the next incomplete task.

## Final Completion Gate

Before ending the agent run:

1. Re-read `Ai-Tasks.md`.
2. Inspect the entire `## Incomplete Tasks` section.
3. Confirm there are no remaining locally actionable `[ ]` tasks.
4. Confirm any blocked tasks are explicitly documented with their blockers.
5. Run the appropriate final validation.
6. Only then provide the final response.

If any locally actionable unchecked task remains, the agent MUST continue working.

The agent must not declare the project complete while actionable unchecked tasks remain in `Ai-Tasks.md`.

## Final Response

Only provide the final response when the agent run genuinely needs to end.

The final response should contain:

* tasks completed during the run;
* tests run and their results;
* Ruff result, if run;
* diagnostics result;
* newly discovered tasks;
* blocked tasks and their blockers;
* remaining unchecked tasks, if any.

If remaining unchecked tasks are locally actionable, do not stop to report them. Continue working instead.
