from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from dialog.base.popup_editor import PopupEditorView
from application.entity_rendering import render_entity_html
from types import SimpleNamespace

from .subdialogs.factory import (
    create_effects_dialog,
    create_grants_dialog,
    create_roll_table_dialog,
)
from .subdialogs.view import CastingTimeDialog, DurationDialog, TargetDialog, effect_summary
from .model import SpellPropertyEditorModel


class CheckableComboBox(QComboBox):
    def __init__(self, options, selected=(), parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        model = QStandardItemModel(self)
        for option in options:
            item = QStandardItem(option)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setData(
                Qt.CheckState.Checked if option in selected else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole,
            )
            model.appendRow(item)
        self.setModel(model)
        self.setCurrentIndex(-1)
        self.view().pressed.connect(self._toggle)
        model.itemChanged.connect(lambda _item: self._refresh_text())
        self._refresh_text()

    def _toggle(self, index):
        item = self.model().itemFromIndex(index)
        state = (
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        item.setCheckState(state)
        self._refresh_text()

    def _refresh_text(self):
        self.lineEdit().setText(", ".join(self.values()))

    def values(self):
        return [
            self.model().item(index).text()
            for index in range(self.count())
            if self.model().item(index).checkState() == Qt.CheckState.Checked
        ]


class SpellPropertyEditorView(PopupEditorView):
    """Modeless top-level editor for scalar Spell properties."""

    SCHOOLS = (
        "abjuration", "chronomancy", "conjuration", "divination",
        "dunamancy", "enchantment", "evocation", "illusion",
        "necromancy", "transmutation",
    )
    CLASSES = (
        "artificer", "barbarian", "bard", "blood_hunter", "cleric", "druid",
        "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer",
        "warlock", "wizard",
    )
    COMPONENTS = ("verbal", "somatic", "material")

    def __init__(
        self,
        model: SpellPropertyEditorModel,
        parent=None,
        on_apply=None,
        on_clone=None,
    ):
        super().__init__(model, parent=parent, on_apply=on_apply)
        self.on_clone = on_clone
        self.setWindowTitle("Spell Properties")
        self.resize(720, 620)
        payload = model.payload

        tabs = QTabWidget(self)
        tabs.addTab(self._build_details_tab(payload), "Details")
        tabs.addTab(self._build_flags_tab(payload), "Casting Flags")
        tabs.addTab(self._build_structured_tab(payload), "Structured Properties")

        editor_panel = QWidget(self)
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(tabs)
        buttons = self.create_button_box(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        if self.model.source_entity_uid and self.on_clone is not None:
            clone_button = buttons.addButton(
                "Clone Again to Homebrew",
                QDialogButtonBox.ButtonRole.ActionRole,
            )
            clone_button.clicked.connect(
                lambda: self.on_clone(self.model.source_entity_uid)
            )
        editor_layout.addWidget(buttons)
        self.preview = QTextBrowser(self)
        self.preview.setOpenLinks(False)
        splitter = QSplitter(self)
        splitter.addWidget(editor_panel)
        splitter.addWidget(self.preview)
        splitter.setSizes((460, 540))
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        for widget in (
            self.name_edit,
            self.description_edit,
            self.higher_level_edit,
            self.school_combo,
            self.classes_combo,
            self.tags_edit,
        ):
            if hasattr(widget, "textChanged"):
                widget.textChanged.connect(self.update_preview)
        self.level_spin.valueChanged.connect(self.update_preview)
        self.ritual_check.stateChanged.connect(self.update_preview)
        self.concentration_check.stateChanged.connect(self.update_preview)
        self.update_preview()

    def _build_details_tab(self, payload):
        tab = QWidget()
        form = QFormLayout(tab)
        self.name_edit = QLineEdit(payload.get("name", self.model.name if hasattr(self.model, "name") else ""))
        self.description_edit = QTextEdit(payload.get("description", ""))
        self.higher_level_edit = QTextEdit(payload.get("higher_level", ""))
        self.level_spin = QSpinBox()
        self.level_spin.setRange(0, 9)
        self.level_spin.setValue(int(payload.get("level", 0)))
        self.school_combo = QComboBox()
        self.school_combo.setEditable(True)
        self.school_combo.addItems(self.SCHOOLS)
        self.school_combo.setCurrentText(str(payload.get("school", "")))
        self.classes_combo = CheckableComboBox(self.CLASSES, payload.get("classes", ()))
        self.tags_edit = QLineEdit(", ".join(payload.get("tags", ())))
        form.addRow("Name", self.name_edit)
        form.addRow("Description", self.description_edit)
        form.addRow("At Higher Levels", self.higher_level_edit)
        form.addRow("Level", self.level_spin)
        form.addRow("School", self.school_combo)
        form.addRow("Classes", self.classes_combo)
        form.addRow("Tags", self.tags_edit)
        return tab

    def _build_flags_tab(self, payload):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        form = QFormLayout()
        self.components_combo = CheckableComboBox(
            self.COMPONENTS, payload.get("components", ())
        )
        self.ritual_check = QCheckBox()
        self.ritual_check.setChecked(payload.get("ritual", False))
        self.concentration_check = QCheckBox()
        self.concentration_check.setChecked(payload.get("concentration", False))
        form.addRow("Components", self.components_combo)
        form.addRow("Ritual", self.ritual_check)
        form.addRow("Concentration", self.concentration_check)
        layout.addLayout(form)
        self.material_group = self._build_material_section(payload.get("material"))
        layout.addWidget(self.material_group)
        self.components_combo.model().itemChanged.connect(self._update_material_visibility)
        self.components_combo.model().itemChanged.connect(self.update_preview)
        self._update_material_visibility()
        return tab

    def _build_structured_tab(self, payload):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.casting_section = self._build_casting_section(payload.get("casting_time"))
        self.target_section = self._build_target_section(payload.get("target"))
        self.duration_section = self._build_duration_section(payload.get("duration"))
        self.effects_button = QPushButton(self._summary(payload.get("effects")))
        self.roll_table_button = QPushButton(self._summary(payload.get("roll_table")))
        self.grants_button = QPushButton(self._summary(payload.get("grants")))
        self.effects_button.clicked.connect(self._edit_effects)
        self.roll_table_button.clicked.connect(self._edit_roll_table)
        self.grants_button.clicked.connect(self._edit_grants)
        layout.addWidget(self.casting_section)
        layout.addWidget(self.target_section)
        layout.addWidget(self.duration_section)
        multi = QFormLayout()
        multi.addRow("Effects", self.effects_button)
        multi.addRow("Roll Table", self.roll_table_button)
        multi.addRow("Grants", self.grants_button)
        layout.addLayout(multi)
        layout.addStretch()
        return tab

    def _build_casting_section(self, value):
        group = QGroupBox("Casting Time")
        form = QFormLayout(group)
        value = value[0] if isinstance(value, list) and value else (value or {})
        self.casting_amount = QSpinBox()
        self.casting_amount.setRange(0, 9999)
        self.casting_amount.setValue(value.get("amount", 0))
        self.casting_unit = QComboBox()
        self.casting_unit.addItems(CastingTimeDialog.UNITS)
        self.casting_unit.setCurrentText(value.get("unit", "action"))
        form.addRow("Amount", self.casting_amount)
        form.addRow("Unit", self.casting_unit)
        self.casting_amount.valueChanged.connect(self.update_preview)
        self.casting_unit.currentTextChanged.connect(self.update_preview)
        return group

    def _build_target_section(self, value):
        group = QGroupBox("Target")
        form = QFormLayout(group)
        value = value or {}
        self.targeting_combo = QComboBox()
        self.targeting_combo.addItems(TargetDialog.TARGETING)
        self.targeting_combo.setCurrentText(value.get("targeting", "self"))
        self.target_description = QLineEdit(value.get("description", ""))
        self.target_range_amount = QSpinBox()
        self.target_range_amount.setRange(0, 999999)
        self.target_range_amount.setValue((value.get("range") or {}).get("amount", 0))
        self.target_range_unit = QLineEdit((value.get("range") or {}).get("unit", "feet"))
        self.target_range_amount_label = QLabel("Range amount")
        self.target_range_unit_label = QLabel("Range unit")
        form.addRow("Targeting", self.targeting_combo)
        form.addRow("Description", self.target_description)
        form.addRow(self.target_range_amount_label, self.target_range_amount)
        form.addRow(self.target_range_unit_label, self.target_range_unit)
        self.targeting_combo.currentTextChanged.connect(self._update_target_visibility)
        self.targeting_combo.currentTextChanged.connect(self.update_preview)
        self.target_description.textChanged.connect(self.update_preview)
        self.target_range_amount.valueChanged.connect(self.update_preview)
        self.target_range_unit.textChanged.connect(self.update_preview)
        self._update_target_visibility()
        return group

    def _build_duration_section(self, value):
        group = QGroupBox("Duration")
        form = QFormLayout(group)
        value = value or {}
        self.duration_amount = QSpinBox()
        self.duration_amount.setRange(0, 9999)
        self.duration_amount.setValue(value.get("amount", 0))
        self.duration_unit = QComboBox()
        self.duration_unit.addItems(DurationDialog.UNITS)
        self.duration_unit.setCurrentText(value.get("duration", "instantaneous"))
        form.addRow("Amount", self.duration_amount)
        form.addRow("Duration", self.duration_unit)
        self.duration_amount.valueChanged.connect(self.update_preview)
        self.duration_unit.currentTextChanged.connect(self.update_preview)
        return group

    def _build_material_section(self, value):
        group = QGroupBox("Material Component")
        form = QFormLayout(group)
        value = value or {}
        self.material_description = QLineEdit(value.get("description", ""))
        self.material_cost = QSpinBox()
        self.material_cost.setRange(0, 999999999)
        self.material_cost.setValue(value.get("cost", 0) or 0)
        self.material_consumed = QCheckBox()
        self.material_consumed.setChecked(value.get("consumed", False))
        form.addRow("Description", self.material_description)
        form.addRow("Cost", self.material_cost)
        form.addRow("Consumed", self.material_consumed)
        self.material_description.textChanged.connect(self.update_preview)
        self.material_cost.valueChanged.connect(self.update_preview)
        self.material_consumed.stateChanged.connect(self.update_preview)
        return group

    def _update_material_visibility(self):
        self.material_group.setVisible("material" in self.components_combo.values())

    def _update_target_visibility(self):
        visible = self.targeting_combo.currentText() == "range"
        self.target_range_amount.setVisible(visible)
        self.target_range_unit.setVisible(visible)
        self.target_range_amount_label.setVisible(visible)
        self.target_range_unit_label.setVisible(visible)

    @staticmethod
    def _summary(value):
        if not value:
            return "Not set"
        if isinstance(value, list):
            summaries = [effect_summary(item) for item in value]
            text = "; ".join(summaries[:2])
            if len(summaries) > 2:
                text += f"; +{len(summaries) - 2} more"
            return text
        if isinstance(value, dict):
            if "entries" in value:
                return f"{len(value['entries'])} outcomes"
            return effect_summary(value)
        return str(value)

    def _edit_effects(self):
        dialog = create_effects_dialog(self.model.payload.get("effects"), self)
        dialog.on_apply = lambda value: self._set_structured("effects", value, self.effects_button)
        dialog.setMinimumSize(520, 360)
        dialog.adjustSize()
        self._show_child_dialog(dialog)

    def _edit_roll_table(self):
        dialog = create_roll_table_dialog(self.model.payload.get("roll_table"), self)
        dialog.on_apply = lambda value: self._set_structured("roll_table", value, self.roll_table_button)
        dialog.setMinimumSize(520, 360)
        dialog.adjustSize()
        self._show_child_dialog(dialog)

    def _edit_grants(self):
        dialog = create_grants_dialog(self.model.payload.get("grants"), self)
        dialog.on_apply = lambda value: self._set_structured("grants", value, self.grants_button)
        dialog.setMinimumSize(520, 360)
        dialog.adjustSize()
        self._show_child_dialog(dialog)

    def _show_child_dialog(self, dialog):
        children = getattr(self, "_child_dialogs", None)
        if children is None:
            children = []
            self._child_dialogs = children
        children.append(dialog)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setMinimumSize(520, 360)
        dialog.adjustSize()
        dialog.finished.connect(
            lambda _result: children.remove(dialog)
            if dialog in children
            else None
        )
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _set_structured(self, name, value, button):
        self.model.payload[name] = value
        if button is not None:
            button.setText(self._summary(value))
        self.update_preview()

    def update_model(self):
        payload = dict(self.model.payload)
        payload["name"] = self.name_edit.text()
        payload["description"] = self.description_edit.toPlainText()
        higher_level = self.higher_level_edit.toPlainText()
        if higher_level:
            payload["higher_level"] = higher_level
        else:
            payload.pop("higher_level", None)
        payload["level"] = self.level_spin.value()
        school = self.school_combo.currentText()
        if school:
            payload["school"] = school
        else:
            payload.pop("school", None)
        classes = self.classes_combo.values()
        if classes:
            payload["classes"] = classes
        else:
            payload.pop("classes", None)
        tags = [value.strip() for value in self.tags_edit.text().split(",") if value.strip()]
        if tags:
            payload["tags"] = tags
        else:
            payload.pop("tags", None)
        payload["components"] = self.components_combo.values()
        payload["ritual"] = self.ritual_check.isChecked()
        payload["concentration"] = self.concentration_check.isChecked()
        casting_time = {"unit": self.casting_unit.currentText()}
        if self.casting_amount.value():
            casting_time["amount"] = self.casting_amount.value()
        payload["casting_time"] = casting_time
        target = dict(payload.get("target") or {})
        target["targeting"] = self.targeting_combo.currentText()
        description = self.target_description.text()
        if description:
            target["description"] = description
        else:
            target.pop("description", None)
        if self.targeting_combo.currentText() == "range":
            target["range"] = {
                "amount": self.target_range_amount.value(),
                "unit": self.target_range_unit.text() or "feet",
            }
        else:
            target.pop("range", None)
        payload["target"] = target
        duration = {"duration": self.duration_unit.currentText()}
        if self.duration_amount.value():
            duration["amount"] = self.duration_amount.value()
        payload["duration"] = duration
        if "material" in payload["components"]:
            material = {
                "description": self.material_description.text(),
                "consumed": self.material_consumed.isChecked(),
            }
            if self.material_cost.value():
                material["cost"] = self.material_cost.value()
            payload["material"] = material
        else:
            payload.pop("material", None)
        self.model.payload = payload
        self.model.name = payload["name"]
        return self.model

    def apply_model(self):
        return super().apply_model()

    def update_preview(self):
        self.update_model()
        entity = SimpleNamespace(
            uid="homebrew-spell-draft",
            entity_type="spell",
            name=self.model.name,
            payload=self.model.payload,
            source_namespace="homebrew",
            source_metadata={
                "draft_state": self.model.draft_state,
                "published": self.model.published,
                "version": self.model.version,
            },
        )
        try:
            self.preview.setHtml(render_entity_html(entity))
        except (TypeError, ValueError, KeyError) as error:
            self.preview.setHtml(
                f"<p>Preview unavailable: {error}</p>"
            )
