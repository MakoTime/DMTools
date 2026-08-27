# DMTools Agent Instructions

- Follow the project's Model, View, Factory dialog pattern for new dialog and workspace features.
- Keep domain and editable state in a model, keep Qt layout and event handling in a view, and construct views through a factory that accepts the model.
- Embedded workspace editors should inherit from `dialog/base/widget_editor/WidgetEditorView`; modal editors should use the popup base and tab-hosted editors should use the tab base.
- Prefer the existing PySide6 and project patterns over introducing a parallel UI architecture.
- Keep SQLite as the source of truth; pandas is a temporary display/editing layer.
- External SQL or database files are import inputs. Persist only the generated project-managed SQLite file under the project's `data` directory.
