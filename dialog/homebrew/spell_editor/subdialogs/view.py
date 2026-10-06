from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)


class SpellChildDialog(QDialog):
    def __init__(self, title, parent=None, on_apply=None, editor_model=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        self.buttons.rejected.connect(self.reject)
        self.buttons.clicked.connect(self._clicked)
        self.on_apply = on_apply
        self.editor_model = editor_model

    def show_child(self, dialog):
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

    def _clicked(self, button):
        if self.buttons.buttonRole(button) == QDialogButtonBox.ButtonRole.AcceptRole:
            self.apply_values()
            if self.editor_model is not None:
                self.editor_model.value = self.value
                self.value = self.editor_model.apply()
            if self.on_apply is not None:
                self.on_apply(self.value)
            self.accept()

    def apply_values(self):
        raise NotImplementedError


class CastingTimeDialog(SpellChildDialog):
    UNITS = ("action", "bonus_action", "reaction", "round", "minute", "hour")

    def __init__(self, value, parent=None, editor_model=None):
        super().__init__("Casting Time", parent, editor_model=editor_model)
        self.rows = []
        self.list = QListWidget()
        for entry in value if isinstance(value, list) else [value or {}]:
            self._add_row(entry)
        add = QPushButton("Add Casting Time")
        add.clicked.connect(lambda: self._add_row({}))
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(add)
        layout.addWidget(self.buttons)

    def _add_row(self, value):
        widget = QGroupBox()
        form = QFormLayout(widget)
        amount = QSpinBox()
        amount.setRange(0, 9999)
        amount.setValue(value.get("amount", 0))
        unit = QComboBox()
        unit.addItems(self.UNITS)
        unit.setCurrentText(value.get("unit", "action"))
        form.addRow("Amount", amount)
        form.addRow("Unit", unit)
        item = QListWidgetItem(self.list)
        item.setSizeHint(widget.sizeHint())
        self.list.setItemWidget(item, widget)
        self.rows.append((item, amount, unit))

    def apply_values(self):
        self.value = []
        for _, amount, unit in self.rows:
            entry = {"unit": unit.currentText()}
            if amount.value():
                entry["amount"] = amount.value()
            self.value.append(entry)
        if len(self.value) == 1:
            self.value = self.value[0]


class DurationDialog(SpellChildDialog):
    UNITS = (
        "instantaneous", "until_dispelled", "until_saved", "round",
        "next_round", "minute", "hour", "day", "week", "month", "year",
    )

    def __init__(self, value, parent=None, editor_model=None):
        super().__init__("Duration", parent, editor_model=editor_model)
        value = value or {}
        self.amount = QSpinBox()
        self.amount.setRange(0, 9999)
        self.amount.setValue(value.get("amount", 0))
        self.unit = QComboBox()
        self.unit.addItems(self.UNITS)
        self.unit.setCurrentText(value.get("duration", "instantaneous"))
        form = QFormLayout()
        form.addRow("Amount", self.amount)
        form.addRow("Duration", self.unit)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def apply_values(self):
        self.value = {"duration": self.unit.currentText()}
        if self.amount.value():
            self.value["amount"] = self.amount.value()


class MaterialDialog(SpellChildDialog):
    def __init__(self, value, parent=None, editor_model=None):
        super().__init__("Material Component", parent, editor_model=editor_model)
        value = value or {}
        self.description = QLineEdit(value.get("description", ""))
        from PySide6.QtWidgets import QDoubleSpinBox

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 999999999)
        self.cost.setValue(value.get("cost", 0) or 0)
        self.consumed = QCheckBox("Consumed")
        self.consumed.setChecked(value.get("consumed", False))
        form = QFormLayout()
        form.addRow("Description", self.description)
        form.addRow("Cost", self.cost)
        form.addRow(self.consumed)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def apply_values(self):
        self.value = {"description": self.description.text()}
        if self.cost.value():
            self.value["cost"] = self.cost.value()
        if self.consumed.isChecked():
            self.value["consumed"] = True


class TargetDialog(SpellChildDialog):
    TARGETING = ("self", "touch", "range", "special", "sight", "unlimited")

    def __init__(self, value, parent=None, editor_model=None):
        super().__init__("Target", parent, editor_model=editor_model)
        value = value or {}
        self.targeting = QComboBox()
        self.targeting.addItems(self.TARGETING)
        self.targeting.setCurrentText(value.get("targeting", "self"))
        self.description = QLineEdit(value.get("description", ""))
        self.range_amount = QSpinBox()
        self.range_amount.setRange(0, 999999)
        self.range_amount.setValue((value.get("range") or {}).get("amount", 0))
        self.range_unit = QLineEdit((value.get("range") or {}).get("unit", "feet"))
        self.count_min = QSpinBox()
        self.count_min.setRange(0, 9999)
        self.count_min.setValue((value.get("count") or {}).get("minimum", 0))
        self.count_max = QSpinBox()
        self.count_max.setRange(0, 9999)
        self.count_max.setValue((value.get("count") or {}).get("maximum", 0))
        form = QFormLayout()
        form.addRow("Targeting", self.targeting)
        form.addRow("Description", self.description)
        form.addRow("Range amount", self.range_amount)
        form.addRow("Range unit", self.range_unit)
        form.addRow("Minimum targets", self.count_min)
        form.addRow("Maximum targets", self.count_max)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Range and count are used only when applicable to the targeting mode."))
        layout.addWidget(self.buttons)

    def apply_values(self):
        self.value = {"targeting": self.targeting.currentText()}
        if self.description.text():
            self.value["description"] = self.description.text()
        if self.targeting.currentText() == "range":
            self.value["range"] = {
                "amount": self.range_amount.value(),
                "unit": self.range_unit.text() or "feet",
            }
        if self.count_min.value() or self.count_max.value():
            count = {}
            if self.count_min.value():
                count["minimum"] = self.count_min.value()
            if self.count_max.value():
                count["maximum"] = self.count_max.value()
            self.value["count"] = count


class GrantsDialog(SpellChildDialog):
    TYPES = ("advantage", "disadvantage", "resistance", "vulnerability",
             "immunity", "sense", "movement")

    def __init__(self, values, parent=None, editor_model=None):
        super().__init__("Spell Grants", parent, editor_model=editor_model)
        self.values = deepcopy(values or [])
        self.list = QListWidget()
        self._refresh()
        add = QPushButton("Add Grant")
        edit = QPushButton("Edit Grant")
        remove = QPushButton("Remove Grant")
        add.clicked.connect(self._add)
        edit.clicked.connect(self._edit)
        remove.clicked.connect(self._remove)
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(edit)
        buttons.addWidget(remove)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(buttons)
        layout.addWidget(self.buttons)

    def _refresh(self):
        self.list.clear()
        for value in self.values:
            self.list.addItem(value.get("type", "Grant"))

    def _add(self):
        from .factory import create_grant_dialog

        dialog = create_grant_dialog(parent=self)
        dialog.on_apply = lambda value: (self.values.append(value), self._refresh())
        self.show_child(dialog)

    def _edit(self):
        row = self.list.currentRow()
        if row < 0:
            return
        from .factory import create_grant_dialog

        dialog = create_grant_dialog(self.values[row], self)
        dialog.on_apply = lambda value: (self.values.__setitem__(row, value), self._refresh())
        self.show_child(dialog)

    def _remove(self):
        row = self.list.currentRow()
        if row >= 0:
            self.values.pop(row)
            self._refresh()

    def apply_values(self):
        self.value = self.values


class GrantDialog(SpellChildDialog):
    TYPES = GrantsDialog.TYPES
    DAMAGE_TYPES = (
        "acid", "bludgeoning", "cold", "fire", "force", "lightning",
        "necrotic", "piercing", "poison", "psychic", "radiant",
        "slashing", "thunder",
    )

    def __init__(self, value=None, parent=None, editor_model=None):
        super().__init__("Spell Grant", parent, editor_model=editor_model)
        value = value or {}
        self.type = QComboBox()
        self.type.addItems(self.TYPES)
        self.type.setCurrentText(value.get("type", self.TYPES[0]))
        self.ability_check = QLineEdit(value.get("ability_check", ""))
        self.skill = QLineEdit(value.get("skill", ""))
        self.saving_throw = QLineEdit(value.get("saving_throw", ""))
        self.condition = QLineEdit(value.get("condition", ""))
        self.damage_type = QComboBox()
        self.damage_type.addItems(self.DAMAGE_TYPES)
        self.damage_type.setCurrentText(value.get("damage_type", ""))
        self.sense = QLineEdit(value.get("sense", ""))
        self.distance = QSpinBox()
        self.distance.setRange(0, 999999)
        self.distance.setValue(value.get("distance", 0) or 0)
        self.movement_type = QLineEdit(value.get("movement_type", ""))
        self.description = QLineEdit(value.get("description", ""))
        form = QFormLayout()
        form.addRow("Type", self.type)
        self._fields = {
            "ability_check": (QLabel("Ability check"), self.ability_check),
            "skill": (QLabel("Skill"), self.skill),
            "saving_throw": (QLabel("Saving throw"), self.saving_throw),
            "condition": (QLabel("Condition"), self.condition),
            "damage_type": (QLabel("Damage type"), self.damage_type),
            "sense": (QLabel("Sense"), self.sense),
            "distance": (QLabel("Distance"), self.distance),
            "movement_type": (QLabel("Movement type"), self.movement_type),
        }
        for label, widget in self._fields.values():
            form.addRow(label, widget)
        form.addRow("Description", self.description)
        self.type.currentTextChanged.connect(self._update_fields)
        self._update_fields()
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def _update_fields(self):
        kind = self.type.currentText()
        visible = {
            "ability_check": kind in {"advantage", "disadvantage"},
            "skill": kind in {"advantage", "disadvantage"},
            "saving_throw": kind in {"advantage", "disadvantage"},
            "condition": kind in {"advantage", "disadvantage"},
            "damage_type": kind in {"resistance", "vulnerability", "immunity"},
            "sense": kind == "sense",
            "distance": kind in {"sense", "movement"},
            "movement_type": kind == "movement",
        }
        for name, (label, widget) in self._fields.items():
            label.setVisible(visible[name])
            widget.setVisible(visible[name])

    def apply_values(self):
        self.value = {"type": self.type.currentText()}
        for name, widget in (
            ("ability_check", self.ability_check),
            ("skill", self.skill),
            ("saving_throw", self.saving_throw),
            ("condition", self.condition),
            ("damage_type", self.damage_type),
            ("sense", self.sense),
            ("movement_type", self.movement_type),
            ("description", self.description),
        ):
            if isinstance(widget, QComboBox):
                if widget.currentText():
                    self.value[name] = widget.currentText()
            elif widget.text():
                self.value[name] = widget.text()
        if self.distance.value():
            self.value["distance"] = self.distance.value()


class EffectDialog(SpellChildDialog):
    TYPES = (
        "damage", "healing", "max_hit_points", "temporary_hit_points",
        "ability_score", "exhaustion", "attack_hit", "attack_save",
        "condition", "grants", "description",
    )
    DAMAGE_TYPES = GrantDialog.DAMAGE_TYPES
    CONDITIONS = (
        "blinded", "charmed", "deafened", "exhaustion", "frightened",
        "grappled", "incapacitated", "invisible", "paralyzed", "petrified",
        "poisoned", "prone", "restrained", "stunned", "unconscious",
    )
    ABILITIES = (
        "strength", "dexterity", "constitution", "intelligence",
        "wisdom", "charisma",
    )
    ATTACK_TYPES = ("melee_weapon", "ranged_weapon", "melee_spell", "ranged_spell")
    DICE = ("3", "4", "6", "8", "10", "12", "20", "100")

    def __init__(self, value=None, parent=None, editor_model=None):
        super().__init__("Spell Effect", parent, editor_model=editor_model)
        value = value or {}
        self.type = QComboBox()
        self.type.addItems(self.TYPES)
        self.type.setCurrentText(next(iter(value), "description"))
        self.description = QLineEdit(value.get("description", ""))
        self.condition = QComboBox()
        self.condition.setEditable(True)
        self.condition.addItems(self.CONDITIONS)
        self.condition.setCurrentText(value.get("condition", ""))
        self.damage_type = QComboBox()
        self.damage_type.addItems(self.DAMAGE_TYPES)
        self.damage_type.setCurrentText((value.get("damage") or {}).get("type", ""))
        roll = (value.get("damage") or {}).get("roll", value.get("healing", {}))
        self.roll_mode = QComboBox()
        self.roll_mode.addItems(("dice", "modifier"))
        self.roll_dice = QComboBox()
        self.roll_dice.setEditable(True)
        self.roll_dice.addItems(self.DICE)
        self.roll_count = QSpinBox()
        self.roll_count.setRange(1, 999)
        self.roll_count.setValue(roll.get("count", 1) if isinstance(roll, dict) else 1)
        self.roll_modifier = QSpinBox()
        self.roll_modifier.setRange(-9999, 9999)
        self.roll_modifier.setValue(roll.get("modifier", 0) if isinstance(roll, dict) else 0)
        if isinstance(roll, dict) and "modifier" in roll:
            self.roll_mode.setCurrentText("modifier")
        self.ability = QComboBox()
        self.ability.setEditable(True)
        self.ability.addItems(self.ABILITIES)
        ability_value = value.get("ability_score", value.get("ability", ""))
        if isinstance(ability_value, dict):
            ability_value = ability_value.get("ability", "")
        self.ability.setCurrentText(str(ability_value))
        self.attack_type = QComboBox()
        self.attack_type.setEditable(True)
        self.attack_type.addItems(self.ATTACK_TYPES)
        self.attack_type.setCurrentText((value.get("attack_hit") or {}).get("type", ""))
        self.attack_hit_effects = deepcopy(
            (value.get("attack_hit") or {}).get("effects", [])
        )
        self.attack_save_success = deepcopy(
            (value.get("attack_save") or {}).get("success", [])
        )
        self.attack_save_failure = deepcopy(
            (value.get("attack_save") or {}).get("failure", [])
        )
        self.effect_grants = deepcopy(value.get("grants", []))
        self.attack_hit_effects_button = QPushButton(self._nested_summary(self.attack_hit_effects))
        self.attack_save_success_button = QPushButton(self._nested_summary(self.attack_save_success))
        self.attack_save_failure_button = QPushButton(self._nested_summary(self.attack_save_failure))
        self.grants_button = QPushButton(self._nested_summary(self.effect_grants))
        self.attack_hit_effects_button.clicked.connect(self._edit_attack_hit_effects)
        self.attack_save_success_button.clicked.connect(self._edit_attack_save_success)
        self.attack_save_failure_button.clicked.connect(self._edit_attack_save_failure)
        self.grants_button.clicked.connect(self._edit_effect_grants)
        form = QFormLayout()
        form.addRow("Effect type", self.type)
        self._fields = {
            "description": (QLabel("Description"), self.description),
            "condition": (QLabel("Condition"), self.condition),
            "damage_type": (QLabel("Damage type"), self.damage_type),
            "roll_mode": (QLabel("Roll mode"), self.roll_mode),
            "roll_dice": (QLabel("Dice"), self.roll_dice),
            "roll_count": (QLabel("Count"), self.roll_count),
            "roll_modifier": (QLabel("Modifier"), self.roll_modifier),
            "ability": (QLabel("Ability"), self.ability),
            "attack_type": (QLabel("Attack type"), self.attack_type),
        }
        for label, widget in self._fields.values():
            form.addRow(label, widget)
        form.addRow("Attack hit effects", self.attack_hit_effects_button)
        form.addRow("Save success effects", self.attack_save_success_button)
        form.addRow("Save failure effects", self.attack_save_failure_button)
        form.addRow("Grants", self.grants_button)
        self.type.currentTextChanged.connect(self._update_fields)
        self.roll_mode.currentTextChanged.connect(self._update_roll_fields)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Complex attack and roll details can be expanded in the dedicated editors."))
        layout.addWidget(self.buttons)
        self._update_fields()

    def _update_fields(self):
        kind = self.type.currentText()
        visible = {
            "description": kind == "description",
            "condition": kind == "condition",
            "damage_type": kind == "damage",
            "roll_mode": kind in {
                "damage", "healing", "max_hit_points",
                "temporary_hit_points", "exhaustion",
            },
            "roll_dice": False,
            "roll_count": False,
            "roll_modifier": False,
            "ability": kind in {"ability_score", "attack_save"},
            "attack_type": kind == "attack_hit",
        }
        for name, (label, widget) in self._fields.items():
            label.setVisible(visible[name])
            widget.setVisible(visible[name])
        self.attack_hit_effects_button.setVisible(kind == "attack_hit")
        self.attack_save_success_button.setVisible(kind == "attack_save")
        self.attack_save_failure_button.setVisible(kind == "attack_save")
        self.grants_button.setVisible(kind == "grants")
        self._update_roll_fields()

    @staticmethod
    def _nested_summary(values):
        return "Not set" if not values else f"{len(values)} effect(s)"

    def _edit_effect_list(self, values, button, setter):
        from .factory import create_effects_dialog

        dialog = create_effects_dialog(values, self)
        dialog.on_apply = lambda updated: (
            setter(updated),
            button.setText(self._nested_summary(updated)),
        )
        self.show_child(dialog)

    def _edit_attack_hit_effects(self):
        self._edit_effect_list(
            self.attack_hit_effects,
            self.attack_hit_effects_button,
            lambda value: setattr(self, "attack_hit_effects", value),
        )

    def _edit_attack_save_success(self):
        self._edit_effect_list(
            self.attack_save_success,
            self.attack_save_success_button,
            lambda value: setattr(self, "attack_save_success", value),
        )

    def _edit_attack_save_failure(self):
        self._edit_effect_list(
            self.attack_save_failure,
            self.attack_save_failure_button,
            lambda value: setattr(self, "attack_save_failure", value),
        )

    def _edit_effect_grants(self):
        from .factory import create_grants_dialog

        dialog = create_grants_dialog(self.effect_grants, self)
        dialog.on_apply = lambda value: (
            setattr(self, "effect_grants", value),
            self.grants_button.setText(self._nested_summary(value)),
        )
        self.show_child(dialog)

    def _update_roll_fields(self):
        active = not self._fields["roll_mode"][1].isHidden()
        dice_mode = active and self.roll_mode.currentText() == "dice"
        self._fields["roll_dice"][0].setVisible(dice_mode)
        self._fields["roll_dice"][1].setVisible(dice_mode)
        self._fields["roll_count"][0].setVisible(dice_mode)
        self._fields["roll_count"][1].setVisible(dice_mode)
        self._fields["roll_modifier"][0].setVisible(active and not dice_mode)
        self._fields["roll_modifier"][1].setVisible(active and not dice_mode)

    def _roll_value(self):
        if self.roll_mode.currentText() == "modifier":
            return {"modifier": self.roll_modifier.value()}
        return {
            "count": self.roll_count.value(),
            "dice": int(self.roll_dice.currentText()),
        }

    def apply_values(self):
        kind = self.type.currentText()
        self.value = {}
        if kind == "description":
            self.value["description"] = self.description.text()
        elif kind == "condition":
            self.value["condition"] = self.condition.text()
        elif kind == "damage":
            self.value["damage"] = {
                "type": self.damage_type.currentText(),
                "roll": self._roll_value(),
            }
        elif kind in {"healing", "max_hit_points", "temporary_hit_points", "exhaustion"}:
            self.value[kind] = self._roll_value()
        elif kind == "ability_score":
            self.value["ability_score"] = {"ability": self.ability.currentText()}
        elif kind == "attack_hit":
            self.value[kind] = {"type": self.attack_type.currentText()}
            if self.attack_hit_effects:
                self.value[kind]["effects"] = self.attack_hit_effects
        elif kind == "attack_save":
            self.value[kind] = {"ability": self.ability.currentText()}
            if self.attack_save_success:
                self.value[kind]["success"] = self.attack_save_success
            if self.attack_save_failure:
                self.value[kind]["failure"] = self.attack_save_failure
        elif kind == "grants":
            self.value["grants"] = self.effect_grants


class EffectsDialog(SpellChildDialog):
    def __init__(self, values, parent=None, editor_model=None):
        super().__init__("Spell Effects", parent, editor_model=editor_model)
        self.values = deepcopy(values or [])
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(("Effect", "Summary"))
        self.tree.header().setStretchLastSection(True)
        self._refresh()
        add = QPushButton("Add Effect")
        edit = QPushButton("Edit Effect")
        remove = QPushButton("Remove Effect")
        add.clicked.connect(self._add)
        edit.clicked.connect(self._edit)
        remove.clicked.connect(self._remove)
        row = QHBoxLayout()
        row.addWidget(add)
        row.addWidget(edit)
        row.addWidget(remove)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addLayout(row)
        layout.addWidget(self.buttons)

    def _refresh(self):
        self.tree.clear()
        for row, value in enumerate(self.values):
            self._add_effect_node(None, value, (row,))
        self.tree.expandAll()

    def _add_effect_node(self, parent, value, path):
        effect_type = next(iter(value), "Effect")
        summary = value.get("description") or value.get("condition") or "Configured"
        item = QTreeWidgetItem(parent or self.tree, (effect_type, str(summary)))
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        if "attack_hit" in value:
            nested = value["attack_hit"].get("effects", [])
            for index, child in enumerate(nested):
                self._add_effect_node(item, child, path + ("attack_hit", "effects", index))
        if "attack_save" in value:
            for result in ("success", "failure"):
                for index, child in enumerate(value["attack_save"].get(result, [])):
                    self._add_effect_node(
                        item, child, path + ("attack_save", result, index)
                    )

    def _value_at_path(self, path):
        value = self.values
        for part in path:
            value = value[part]
        return value

    def _set_value_at_path(self, path, value):
        parent = self.values
        for part in path[:-1]:
            parent = parent[part]
        parent[path[-1]] = value

    def _remove_at_path(self, path):
        parent = self.values
        for part in path[:-1]:
            parent = parent[part]
        del parent[path[-1]]

    def _add(self):
        from .factory import create_effect_dialog

        dialog = create_effect_dialog(parent=self)
        dialog.on_apply = lambda value: (self.values.append(value), self._refresh())
        self.show_child(dialog)

    def _edit(self):
        item = self.tree.currentItem()
        if item is None:
            return
        path = tuple(item.data(0, Qt.ItemDataRole.UserRole))
        value = self._value_at_path(path)
        if not isinstance(value, dict) or "type" in value:
            return
        from .factory import create_effect_dialog

        dialog = create_effect_dialog(value, self)
        dialog.on_apply = lambda value: (self._set_value_at_path(path, value), self._refresh())
        self.show_child(dialog)

    def _remove(self):
        item = self.tree.currentItem()
        if item is not None:
            path = tuple(item.data(0, Qt.ItemDataRole.UserRole))
            self._remove_at_path(path)
            self._refresh()

    def apply_values(self):
        self.value = self.values


class RollTableEntryDialog(SpellChildDialog):
    def __init__(self, value=None, parent=None, editor_model=None):
        super().__init__("Roll Table Outcome", parent, editor_model=editor_model)
        value = value or {}
        self.roll = QSpinBox()
        self.roll.setRange(1, 9999)
        self.roll.setValue(value.get("roll", 1))
        self.result = QLineEdit(value.get("result", ""))
        self.effects = deepcopy(value.get("effects", []))
        effects_button = QPushButton(self._effects_text())
        effects_button.clicked.connect(
            lambda: self._edit_effects(effects_button)
        )
        form = QFormLayout()
        form.addRow("Roll", self.roll)
        form.addRow("Result", self.result)
        form.addRow("Effects", effects_button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def _effects_text(self):
        return "Not set" if not self.effects else f"{len(self.effects)} effect(s)"

    def _edit_effects(self, button):
        from .factory import create_effects_dialog

        dialog = create_effects_dialog(self.effects, self)
        dialog.on_apply = lambda value: (
            setattr(self, "effects", value),
            button.setText(self._effects_text()),
        )
        self.show_child(dialog)
        dialog.raise_()

    def apply_values(self):
        self.value = {
            "roll": self.roll.value(),
            "result": self.result.text(),
        }
        if self.effects:
            self.value["effects"] = self.effects


class RollTableDialog(SpellChildDialog):
    DICE = ("3", "4", "6", "8", "10", "12", "20", "100")

    def __init__(self, value, parent=None, editor_model=None):
        super().__init__("Spell Roll Table", parent, editor_model=editor_model)
        value = value or {}
        self.dice = QComboBox()
        self.dice.setEditable(True)
        self.dice.addItems(self.DICE)
        self.dice.setCurrentText(str(value.get("dice", "20")))
        self.count = QSpinBox()
        self.count.setRange(1, 999)
        self.count.setValue(value.get("count", 1))
        self.entries = deepcopy(value.get("entries", []))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(("Roll", "Result", "Effects"))
        self.table.horizontalHeader().setStretchLastSection(True)
        self._refresh_entries()
        add = QPushButton("Add Outcome")
        edit = QPushButton("Edit Outcome")
        remove = QPushButton("Remove Outcome")
        add.clicked.connect(self._add_entry)
        edit.clicked.connect(self._edit_entry)
        remove.clicked.connect(self._remove_entry)
        form = QFormLayout()
        form.addRow("Dice", self.dice)
        form.addRow("Count", self.count)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        actions.addWidget(add)
        actions.addWidget(edit)
        actions.addWidget(remove)
        layout.addLayout(actions)
        layout.addWidget(self.buttons)

    def _refresh_entries(self):
        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            self.table.setItem(row, 0, QTableWidgetItem(str(entry.get("roll", 1))))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("result", "")))
            effects = entry.get("effects", [])
            self.table.setItem(
                row, 2, QTableWidgetItem("None" if not effects else f"{len(effects)} effect(s)")
            )

    def _add_entry(self):
        from .factory import create_roll_table_entry_dialog

        dialog = create_roll_table_entry_dialog(parent=self)
        dialog.on_apply = lambda value: (self.entries.append(value), self._refresh_entries())
        self.show_child(dialog)

    def _edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            return
        from .factory import create_roll_table_entry_dialog

        dialog = create_roll_table_entry_dialog(self.entries[row], self)
        dialog.on_apply = lambda value: (
            self.entries.__setitem__(row, value),
            self._refresh_entries(),
        )
        self.exec_child(dialog)

    def _remove_entry(self):
        row = self.table.currentRow()
        if row >= 0:
            self.entries.pop(row)
            self._refresh_entries()

    def apply_values(self):
        self.value = {
            "dice": int(self.dice.currentText()),
            "count": self.count.value(),
            "entries": self.entries,
        }
