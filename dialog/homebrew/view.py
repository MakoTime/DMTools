import json

from pydantic import ValidationError

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from dialog.base.popup_editor import PopupEditorView
from application.imports.registry import SCHEMA_ROOT

from .model import HomebrewEditorModel

ENTITY_SCHEMAS = {
    "item": "Item.schema.json",
    "spell": "Spell.schema.json",
    "race": "Race.schema.json",
    "class": "Class.schema.json",
    "subclass": "Subclass.schema.json",
    "monster": "Creature.schema.json",
    "feat": "Feat.schema.json",
    "background": "Background.schema.json",
    "ability": "Ability.schema.json",
}


class HomebrewEditorView(PopupEditorView):
    """Shared popup editor whose validation adapts to the canonical type."""

    def __init__(self, model: HomebrewEditorModel, parent=None):
        super().__init__(model, parent=parent)
        self.setWindowTitle(f"Homebrew {model.entity_type.title()}")
        self.resize(680, 560)

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
        self.field_widgets = {}
        self.payload_edit = QTextEdit(
            json.dumps(model.payload, indent=2, sort_keys=True)
        )
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Type", self.type_label)
        form.addRow("Name", self.name_edit)
        form.addRow("State", self.state_combo)
        form.addRow("Published", self.published_check)
        form.addRow("Version", self.version_spin)
        self._build_schema_fields(form)
        form.addRow("Entity data", self.payload_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(self.create_button_box())

    def _build_schema_fields(self, form):
        schema = json.loads(
            (SCHEMA_ROOT / "entities" / ENTITY_SCHEMAS[self.model.entity_type]).read_text(
                encoding="utf-8"
            )
        )
        for name, definition in schema.get("properties", {}).items():
            if name == "name" or not self._is_editable_definition(definition):
                continue
            if self._is_structured_list_definition(definition):
                widget = QListWidget()
                for value in self.model.payload.get(name, ()):
                    widget.addItem(json.dumps(value, sort_keys=True))
                detail = QTextEdit()
                detail.setPlaceholderText("JSON object")
                add_button = QPushButton("Add")
                remove_button = QPushButton("Remove")
                add_button.clicked.connect(lambda _checked=False, field=name: self._add_structured_value(field))
                remove_button.clicked.connect(lambda _checked=False, field=name: self._remove_structured_value(field))
                widget.currentRowChanged.connect(
                    lambda row, field=name: self._load_structured_value(field, row)
                )
                row = QVBoxLayout()
                row.addWidget(widget)
                row.addWidget(detail)
                row.addWidget(add_button)
                row.addWidget(remove_button)
                self.field_widgets[name] = (widget, detail)
                form.addRow(name.replace("_", " ").title(), row)
                continue
            if self._is_list_definition(definition):
                widget = QListWidget()
                widget.addItems(str(value) for value in self.model.payload.get(name, ()))
                add_button = QPushButton("Add")
                remove_button = QPushButton("Remove")
                add_button.clicked.connect(lambda _checked=False, field=name: self._add_list_value(field))
                remove_button.clicked.connect(lambda _checked=False, field=name: self._remove_list_value(field))
                row = QVBoxLayout()
                row.addWidget(widget)
                row.addWidget(add_button)
                row.addWidget(remove_button)
                self.field_widgets[name] = (widget,)
                form.addRow(name.replace("_", " ").title(), row)
                continue
            options = self._schema_options(definition)
            if options:
                widget = QComboBox()
                widget.addItems(options)
                widget.setCurrentText(str(self.model.payload.get(name, "")))
            elif definition.get("type") == "boolean":
                widget = QCheckBox()
                widget.setChecked(bool(self.model.payload.get(name, False)))
            elif definition.get("type") in {"integer", "number"}:
                widget = QSpinBox() if definition["type"] == "integer" else QDoubleSpinBox()
                widget.setRange(
                    definition.get("minimum", -999999),
                    definition.get("maximum", 999999),
                )
                if name in self.model.payload:
                    widget.setValue(self.model.payload[name])
            else:
                widget = QLineEdit(str(self.model.payload.get(name, "")))
            self.field_widgets[name] = widget
            form.addRow(name.replace("_", " ").title(), widget)

    @staticmethod
    def _is_editable_definition(definition):
        if (
            HomebrewEditorView._is_list_definition(definition)
            or HomebrewEditorView._is_structured_list_definition(definition)
        ):
            return True
        return definition.get("type") in {"string", "integer", "number", "boolean"} or "$ref" in definition

    @staticmethod
    def _is_list_definition(definition):
        items = definition.get("items", {})
        return definition.get("type") == "array" and (
            items.get("type") == "string"
            or ("$ref" in items and not HomebrewEditorView._is_structured_reference(items))
        )

    @staticmethod
    def _is_structured_reference(items):
        reference = items.get("$ref")
        if not reference:
            return False
        path = SCHEMA_ROOT / reference.replace("../", "", 1)
        if not path.suffix:
            path = path.with_suffix(".schema.json")
        if not path.exists():
            return False
        return json.loads(path.read_text(encoding="utf-8")).get("type") == "object"

    @staticmethod
    def _is_structured_list_definition(definition):
        items = definition.get("items", {})
        return definition.get("type") == "array" and HomebrewEditorView._is_structured_reference(items)

    def _add_list_value(self, name):
        widget = self.field_widgets[name][0]
        widget.addItem("")
        widget.setCurrentRow(widget.count() - 1)
        widget.editItem(widget.currentItem())

    def _remove_list_value(self, name):
        widget = self.field_widgets[name][0]
        current = widget.currentRow()
        if current >= 0:
            widget.takeItem(current)

    def _add_structured_value(self, name):
        widget, detail = self.field_widgets[name]
        widget.addItem("{}")
        widget.setCurrentRow(widget.count() - 1)
        detail.setPlainText("{}")

    def _remove_structured_value(self, name):
        widget, detail = self.field_widgets[name]
        current = widget.currentRow()
        if current >= 0:
            widget.takeItem(current)
            detail.clear()

    def _load_structured_value(self, name, row):
        widget, detail = self.field_widgets[name]
        if 0 <= row < widget.count():
            detail.setPlainText(widget.item(row).text())
        else:
            detail.clear()

    def _sync_structured_value(self, widget, detail):
        current = widget.currentRow()
        if current < 0:
            return
        try:
            value = json.loads(detail.toPlainText())
        except json.JSONDecodeError as error:
            raise ValueError(f"Structured field JSON is invalid: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError("Structured field entries must be JSON objects")
        widget.item(current).setText(json.dumps(value, sort_keys=True))

    @staticmethod
    def _schema_options(definition):
        if "enum" in definition:
            return [str(option) for option in definition["enum"]]
        reference = definition.get("$ref")
        if not reference:
            return []
        path = SCHEMA_ROOT / reference.replace("../", "", 1)
        if not path.suffix:
            path = path.with_suffix(".schema.json")
        if not path.exists():
            return []
        referenced = json.loads(path.read_text(encoding="utf-8"))
        for option in referenced.get("enum", ()):
            return [str(option) for option in referenced["enum"]]
        for alternative in referenced.get("anyOf", ()):
            if "enum" in alternative:
                return [str(option) for option in alternative["enum"]]
        return []

    def _sync_schema_fields(self, payload):
        for name, widget in self.field_widgets.items():
            if isinstance(widget, tuple) and len(widget) == 2 and isinstance(widget[0], QListWidget):
                self._sync_structured_value(widget[0], widget[1])
                payload[name] = [
                    json.loads(widget[0].item(index).text())
                    for index in range(widget[0].count())
                ]
                continue
            if isinstance(widget, tuple):
                payload[name] = [
                    widget[0].item(index).text()
                    for index in range(widget[0].count())
                    if widget[0].item(index).text()
                ]
                continue
            if isinstance(widget, QComboBox):
                value = widget.currentText()
                if value:
                    payload[name] = value
            elif isinstance(widget, QCheckBox):
                payload[name] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                payload[name] = widget.value()
            else:
                value = widget.text()
                if value:
                    payload[name] = value

    def update_model(self):
        self.model.name = self.name_edit.text()
        self.model.draft_state = self.state_combo.currentText()
        self.model.published = self.published_check.isChecked()
        self.model.version = self.version_spin.value()
        return self.model

    def apply_model(self):
        self.error_label.clear()
        try:
            payload = json.loads(self.payload_edit.toPlainText())
            if not isinstance(payload, dict):
                raise ValueError("Entity data must be a JSON object")
            self._sync_schema_fields(payload)
            self.model.payload = payload
            return self.model.apply()
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
                for issue in error.errors()
            )
            self.error_label.setText(details)
            return None
        except (ValueError, json.JSONDecodeError) as error:
            self.error_label.setText(str(error))
            return None