import json
from types import SimpleNamespace

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QTextBrowser,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)
from PySide6.QtCore import Qt

from dialog.base.editor import EditorButtonBoxImplementation
from dialog.base.widget_editor import WidgetEditorView
from application.entity_rendering import render_entity_html
from application.imports.registry import SCHEMA_ROOT

from .model import HomebrewEditorModel

ENTITY_SCHEMAS = {
    "item": "Item.schema.json", "spell": "Spell.schema.json",
    "race": "Race.schema.json", "class": "Class.schema.json",
    "subclass": "Subclass.schema.json", "monster": "Creature.schema.json",
    "feat": "Feat.schema.json", "background": "Background.schema.json",
    "ability": "Ability.schema.json",
}


class HomebrewEditorMdiView(WidgetEditorView, EditorButtonBoxImplementation):
    """Modeless Homebrew draft editor for the main window MDI area."""

    def __init__(self, model: HomebrewEditorModel, *, on_accept=None, parent=None):
        super().__init__(model, parent=parent)
        EditorButtonBoxImplementation.__init__(self)
        self.on_accept = on_accept
        self._close_reason = None
        self._dirty = False
        self.setWindowTitle(f"Homebrew {model.entity_type.title()}")

        self.type_label = QLabel(model.entity_type.title())
        self.name_edit = QLineEdit(model.name)
        self.state_combo = QComboBox()
        self.state_combo.addItems(("draft", "published", "archived"))
        self.state_combo.setCurrentText(model.draft_state)
        self.published_check = QCheckBox()
        self.published_check.setChecked(model.published)
        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 9999)
        self.version_spin.setValue(model.version)
        self.name_edit.textChanged.connect(self.update_preview)
        self.state_combo.currentTextChanged.connect(self.update_preview)
        self.published_check.stateChanged.connect(self.update_preview)
        self.version_spin.valueChanged.connect(self.update_preview)
        self.name_edit.textChanged.connect(self._mark_dirty)
        self.state_combo.currentTextChanged.connect(self._mark_dirty)
        self.published_check.stateChanged.connect(self._mark_dirty)
        self.version_spin.valueChanged.connect(self._mark_dirty)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        self.field_widgets = {}
        self.property_table = QTableWidget(self)
        self.property_table.setColumnCount(2)
        self.property_table.setHorizontalHeaderLabels(("Property", "Value"))
        self.property_table.horizontalHeader().setStretchLastSection(True)
        self.property_table.verticalHeader().setVisible(False)
        self.property_table.itemChanged.connect(self._mark_dirty)
        self.property_table.cellDoubleClicked.connect(self._edit_property)
        self._build_property_table()
        self._dirty = False

        metadata = QHBoxLayout()
        metadata.addWidget(QLabel("Type"))
        metadata.addWidget(self.type_label)
        metadata.addWidget(QLabel("Name"))
        metadata.addWidget(self.name_edit, 1)
        metadata.addWidget(QLabel("State"))
        metadata.addWidget(self.state_combo)
        metadata.addWidget(QLabel("Published"))
        metadata.addWidget(self.published_check)
        metadata.addWidget(QLabel("Version"))
        metadata.addWidget(self.version_spin)

        editor_panel = QWidget(self)
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addLayout(metadata)
        editor_layout.addWidget(self.property_table, 1)
        editor_layout.addWidget(self.error_label)
        editor_layout.addWidget(self.create_button_box())

        self.preview = QTextBrowser(self)
        self.preview.setOpenLinks(False)
        splitter = QSplitter(self)
        splitter.addWidget(editor_panel)
        splitter.addWidget(self.preview)
        splitter.setSizes((420, 580))

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.update_preview()

    def update_model(self):
        self.model.name = self.name_edit.text()
        self.model.draft_state = self.state_combo.currentText()
        self.model.published = self.published_check.isChecked()
        self.model.version = self.version_spin.value()
        return self.model

    def _mark_dirty(self):
        self._dirty = True

    def _build_property_table(self):
        schema_path = SCHEMA_ROOT / "entities" / ENTITY_SCHEMAS[self.model.entity_type]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        names = list(schema.get("properties", {}))
        requested = (
            "description", "hit_dice", "saving_throws", "armor_proficiencies",
            "weapon_proficiencies", "tool_proficiencies", "spellcasting", "features",
            "repeating_features", "required_stats", "starting_class", "multiclassing",
            "ability_score_increase",
        )
        names = [name for name in requested if name in names] + [
            name for name in names if name not in requested and name != "name"
        ]
        self.property_table.setRowCount(len(names))
        for row, name in enumerate(names):
            definition = schema["properties"][name]
            label = QTableWidgetItem(name.replace("_", " ").title())
            label.setFlags(label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.property_table.setItem(row, 0, label)
            value = self.model.payload.get(name)
            if self._requires_subdialog(value, definition):
                item = QTableWidgetItem(self._display_value(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.property_table.setItem(row, 1, item)
            else:
                item = QTableWidgetItem(self._display_inline_value(value))
                self.property_table.setItem(row, 1, item)
            self.field_widgets[name] = (row, definition)

    @staticmethod
    def _requires_subdialog(value, definition):
        return definition.get("input") == "textarea" or HomebrewEditorMdiView._is_complex_value(value, definition)

    @staticmethod
    def _is_complex_value(value, definition):
        if definition.get("type") == "array":
            item_definition = definition.get("items", {})
            if item_definition.get("type") in {"string", "integer", "number", "boolean"}:
                return False
            return not item_definition.get("$ref", "").startswith("../values/")
        if isinstance(value, dict):
            return True
        return "$ref" in definition and not definition["$ref"].startswith("../values/")

    @staticmethod
    def _display_inline_value(value):
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return "" if value is None else str(value)

    @staticmethod
    def _display_value(value):
        if isinstance(value, list):
            return f"{len(value)} item(s)"
        if isinstance(value, dict):
            return "Structured value"
        if isinstance(value, str):
            first_line = value.strip().splitlines()[0] if value.strip() else ""
            return first_line[:80] or "Text value"
        return ""

    @staticmethod
    def _schema_options(definition):
        if "enum" in definition:
            return [str(value) for value in definition["enum"]]
        reference = definition.get("$ref")
        if not reference:
            return []
        path = SCHEMA_ROOT / reference.replace("../", "", 1)
        if not path.suffix:
            path = path.with_suffix(".schema.json")
        if not path.exists():
            return []
        referenced = json.loads(path.read_text(encoding="utf-8"))
        if "enum" in referenced:
            return [str(value) for value in referenced["enum"]]
        return [
            str(value)
            for alternative in referenced.get("anyOf", ())
            for value in alternative.get("enum", ())
        ]

    def _sync_schema_fields(self, payload):
        for name, (row, definition) in self.field_widgets.items():
            item = self.property_table.item(row, 1)
            if item is None:
                continue
            if self._requires_subdialog(payload.get(name), definition):
                continue
            text = item.text()
            if not text:
                payload.pop(name, None)
            elif definition.get("type") == "array":
                item_definition = definition.get("items", {})
                values = [part.strip() for part in text.split(",") if part.strip()]
                if item_definition.get("type") == "integer":
                    payload[name] = [int(value) for value in values]
                elif item_definition.get("type") == "number":
                    payload[name] = [float(value) for value in values]
                else:
                    payload[name] = values
            elif definition.get("type") == "integer":
                payload[name] = int(text)
            elif definition.get("type") == "number":
                payload[name] = float(text)
            elif definition.get("type") == "boolean":
                payload[name] = text.lower() == "true"
            else:
                payload[name] = text

    def _edit_property(self, row, column):
        if column != 1:
            return
        name = self.property_table.item(row, 0).text().lower().replace(" ", "_")
        _, definition = self.field_widgets[name]
        value = self.model.payload.get(name)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {name.replace('_', ' ').title()}")
        editor = QTextEdit(dialog)
        is_text = definition.get("input") == "textarea"
        if is_text:
            editor.setPlainText(value or "")
        else:
            editor.setPlainText(json.dumps(value if value is not None else {}, indent=2, sort_keys=True))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout = QVBoxLayout(dialog)
        layout.addWidget(editor)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if is_text:
            parsed = editor.toPlainText()
        else:
            try:
                parsed = json.loads(editor.toPlainText())
            except json.JSONDecodeError as error:
                self.error_label.setText(f"Invalid JSON: {error.msg}")
                return
        self.model.payload[name] = parsed
        self.property_table.item(row, 1).setText(self._display_value(parsed))
        self._mark_dirty()

    def apply_model(self):
        self.error_label.clear()
        try:
            payload = dict(self.model.payload)
            self._sync_schema_fields(payload)
            self.model.payload = payload
            result = self.model.apply()
            self._dirty = False
            return result
        except (ValueError, json.JSONDecodeError) as error:
            self.error_label.setText(str(error))
            return None

    def update_preview(self):
        if self.model is None:
            return
        try:
            payload = dict(self.model.payload)
            self._sync_schema_fields(payload)
            payload["name"] = self.name_edit.text()
            entity = SimpleNamespace(
                uid="homebrew-draft",
                entity_type=self.model.entity_type,
                name=self.name_edit.text(),
                payload=payload,
                source_namespace="homebrew",
                source_metadata={
                    "draft_state": self.state_combo.currentText(),
                    "published": self.published_check.isChecked(),
                    "version": self.version_spin.value(),
                },
            )
            self.preview.setHtml(render_entity_html(entity))
            self.error_label.clear()
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            self.preview.setHtml(
                "<p>Preview unavailable until the draft JSON is valid.</p>"
            )
            self.error_label.setText(str(error))

    def apply_changes(self):
        record = super().apply_changes()
        if record is not None and self.on_accept is not None:
            on_accept = self.on_accept
            self.on_accept = None
            on_accept(self.model)
        return record

    def _cancel(self):
        self._close_reason = "cancel"
        self.close()

    def _button_clicked(self, button):
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.ButtonRole.AcceptRole:
            if self.apply_changes() is not None:
                self._close_reason = "ok"
                self.close()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:
            self._cancel()

    def create_button_box(self, buttons=None):
        if buttons is None:
            buttons = QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        self.button_box = QDialogButtonBox(buttons, self)
        self.button_box.clicked.connect(self._button_clicked)
        return self.button_box

    def closeEvent(self, event):
        if self._dirty:
            answer = QMessageBox.question(
                self,
                "Unsaved Homebrew Changes",
                "Discard unsaved changes?",
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Discard:
                event.ignore()
                return
        self.notify_closed(self._close_reason or "window")
        self.on_accept = None
        self.model = None
        super().closeEvent(event)
