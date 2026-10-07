from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHeaderView,
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from application.progression_table import (
    CONFIG_KEY,
    GENERATED_COLUMNS,
    RECHARGE_TYPES,
    custom_progression_rows,
    validate_formula,
)
from dialog.base.popup_editor import PopupEditorView


class _LevelTableItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return int(self.text()) < int(other.text())
        except ValueError:
            return self.text() < other.text()


class ProgressionEditorView(PopupEditorView):
    """Preview-first editor for fixed and user-defined class table columns."""

    def __init__(self, model, parent=None, *, on_apply=None):
        super().__init__(model, parent=parent, on_apply=on_apply)
        self.setWindowTitle("Edit class progression table")
        self.resize(1200, 720)
        self._updating = False
        self._selected_key = None
        self._formula_error = ""

        self.preview = QTableWidget(self)
        self.preview.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectColumns)
        self.preview.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        preview_header = self.preview.horizontalHeader()
        preview_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        preview_header.setMinimumSectionSize(70)
        preview_header.setStretchLastSection(False)
        self.preview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.preview.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.preview.verticalHeader().setVisible(False)
        self.preview.itemSelectionChanged.connect(self._select_preview_column)

        self.add_button = QPushButton("Add column", self)
        self.add_button.clicked.connect(self._add_column)
        self.remove_button = QPushButton("Remove column", self)
        self.remove_button.clicked.connect(self._remove_column)
        self.left_button = QPushButton("Move left", self)
        self.left_button.clicked.connect(lambda: self._move_column(-1))
        self.right_button = QPushButton("Move right", self)
        self.right_button.clicked.connect(lambda: self._move_column(1))
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addWidget(self.left_button)
        toolbar.addWidget(self.right_button)
        toolbar.addStretch(1)

        self.display_name = QLineEdit(self)
        self.display_name.editingFinished.connect(self._update_selected)
        self.method = QComboBox(self)
        self.method.addItems(("table", "formula"))
        self.method.currentTextChanged.connect(self._method_changed)
        self.show_value = QCheckBox("Show value column", self)
        self.show_value.toggled.connect(self._mini_columns_changed)
        self.show_recharge = QCheckBox("Show recharge column", self)
        self.show_recharge.toggled.connect(self._mini_columns_changed)
        self.merge_recharge = QCheckBox("Merge recharge into value", self)
        self.merge_recharge.toggled.connect(self._mini_columns_changed)

        self.formula_edit = QLineEdit(self)
        self.formula_edit.setObjectName("formulaEdit")
        self.formula_edit.setPlaceholderText("2 * [level] + [Wisdom]")
        self.formula_edit.textChanged.connect(self._formula_changed)
        self.add_variable_button = QPushButton("Add variable", self)
        variable_menu = QMenu(self.add_variable_button)
        for label, token in (
            ("Level [level]", "[level]"),
            ("Proficiency Bonus [proficiency_bonus]", "[proficiency_bonus]"),
            ("Ability Modifier [ability_modifier]", "[ability_modifier]"),
            ("Strength [STR]", "[STR]"),
            ("Dexterity [DEX]", "[DEX]"),
            ("Constitution [CON]", "[CON]"),
            ("Intelligence [INT]", "[INT]"),
            ("Wisdom [WIS]", "[WIS]"),
            ("Charisma [CHA]", "[CHA]"),
        ):
            action = variable_menu.addAction(label)
            action.triggered.connect(lambda checked=False, value=token: self._add_formula_variable(value))
        self.add_variable_button.setMenu(variable_menu)
        formula_row = QVBoxLayout()
        formula_row.setContentsMargins(16, 0, 0, 0)
        formula_row.addWidget(self.formula_edit)
        formula_row.addWidget(self.add_variable_button)
        self.formula_label = QLabel("Formula", self)
        self.formula_container = QWidget(self)
        self.formula_container.setLayout(formula_row)

        self.recharge_enabled = QCheckBox("Enable recharge", self)
        self.recharge_enabled.toggled.connect(self._rebuild_value_table)
        self.values = QTableWidget(self)
        value_header = self.values.horizontalHeader()
        value_header.setStretchLastSection(True)
        value_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        value_header.setMinimumSectionSize(0)
        self.values.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.values.verticalHeader().setVisible(False)
        self.values.itemChanged.connect(self._update_selected)
        self.validation_label = QLabel(self)
        self.validation_label.setObjectName("errorLabel")
        self.validation_label.setWordWrap(True)
        self.value_add = QPushButton("Add level", self)
        self.value_add.clicked.connect(self._add_level)
        self.value_remove = QPushButton("Remove level", self)
        self.value_remove.clicked.connect(self._remove_level)
        value_buttons = QVBoxLayout()
        value_buttons.setContentsMargins(16, 0, 0, 0)
        value_buttons.addWidget(self.value_add)
        value_buttons.addWidget(self.value_remove)

        form = QFormLayout()
        form.addRow("Display name", self.display_name)
        form.addRow("Value method", self.method)
        mini_columns = QVBoxLayout()
        mini_columns.setContentsMargins(16, 0, 0, 0)
        mini_columns.addWidget(self.show_value)
        mini_columns.addWidget(self.show_recharge)
        mini_columns.addWidget(self.merge_recharge)
        form.addRow("Output table", mini_columns)
        form.addRow(self.formula_label, self.formula_container)
        form.addRow("Resource", self.recharge_enabled)
        editor = QVBoxLayout()
        editor.addLayout(form)
        editor.addWidget(QLabel("Level values", self))
        editor.addWidget(self.values, 1)
        editor.addWidget(self.validation_label)
        editor.addLayout(value_buttons)
        editor_widget = QWidget(self)
        editor_widget.setLayout(editor)
        editor_widget.setMaximumWidth(390)
        editor_widget.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        content = QHBoxLayout()
        content.addWidget(editor_widget)
        content.addWidget(self.preview, 1)
        layout.addLayout(content, 1)
        layout.addWidget(self.create_button_box())
        self._refresh_preview()

    def update_model(self):
        self._update_selected()
        return self.model

    def _refresh_preview(self):
        self._updating = True
        payload = dict(self.model._payload)
        payload[CONFIG_KEY] = self.model.configuration
        rows = custom_progression_rows(payload)
        if rows is None:
            self._updating = False
            return
        headers = list(rows[0])
        labels = {column["key"]: column["label"] for column in self.model.editor_columns}
        for column in self.model.editor_columns:
            labels[f"{column['key']}_recharge"] = f"{column['label']} Recharge"
        self.preview.setColumnCount(len(headers))
        self.preview.setHorizontalHeaderLabels([labels.get(key, key) for key in headers])
        widths = {"level": 80, "proficiency_bonus": 150, "features": 320}
        for column_index, key in enumerate(headers):
            self.preview.setColumnWidth(column_index, widths.get(key, 160))
        self.preview.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(headers):
                self.preview.setItem(row_index, column_index, QTableWidgetItem(str(row.get(key, ""))))
        self._updating = False
        if self._selected_key in headers:
            self.preview.selectColumn(headers.index(self._selected_key))
        elif headers:
            self.preview.selectColumn(0)

    def _select_preview_column(self):
        if self._updating or not self.preview.selectedIndexes():
            return
        column_index = self.preview.selectedIndexes()[0].column()
        key = list(self._preview_keys())[column_index]
        self._update_selected()
        if key.endswith("_recharge"):
            key = key.removesuffix("_recharge")
        self._selected_key = key
        self._load_editor(key)

    def _preview_keys(self):
        if self.preview.columnCount() == 0:
            return ()
        payload = dict(self.model._payload)
        payload[CONFIG_KEY] = self.model.configuration
        rows = custom_progression_rows(payload) or []
        return tuple(rows[0]) if rows else ()

    def _load_editor(self, key):
        column = next((column for column in self.model.editor_columns if column["key"] == key), None)
        if column is None:
            return
        generated = column.get("source") == "generated"
        self._updating = True
        self.display_name.setText(column["label"])
        self.method.setCurrentText(column.get("method", "table"))
        mini_columns = {item["key"]: item for item in column.get("mini_columns", ())}
        self.show_value.setChecked(mini_columns.get("value", {}).get("visible", True))
        self.show_recharge.setChecked(mini_columns.get("recharge", {}).get("visible", False))
        self.merge_recharge.setChecked(mini_columns.get("recharge", {}).get("merge", False))
        self.recharge_enabled.setChecked(bool(column.get("recharge_values")))
        self._load_values(column)
        self._load_formula_controls(column.get("formula", ""))
        self._updating = False
        for widget in (self.display_name, self.method, self.show_value, self.show_recharge, self.merge_recharge, self.recharge_enabled, self.values, self.remove_button, self.value_add, self.value_remove):
            widget.setEnabled(not generated)
        self.formula_edit.setEnabled(not generated)
        self.add_variable_button.setEnabled(not generated)
        self.add_variable_button.setEnabled(not generated)
        self._method_changed(self.method.currentText())

    def _load_formula_controls(self, formula):
        self.formula_edit.setText(str(formula or ""))
        self._formula_error = ""

    def _load_values(self, column):
        recharge = column.get("recharge_values", {})
        recharge_enabled = bool(column.get("recharge_values")) or any(
            item.get("key") == "recharge" for item in column.get("mini_columns", ())
        )
        level_columns = [{"key": "value", "label": "Value"}]
        if recharge_enabled:
            level_columns.append({"key": "recharge", "label": "Recharge"})
        self.values.setColumnCount(len(level_columns) + 1)
        headers = ["Level"] + [item["label"] for item in level_columns]
        self.values.setHorizontalHeaderLabels(headers)
        self.values.setRowCount(0)
        values = column.get("values", {})
        levels = sorted({int(level) for level in set(values) | set(recharge) if str(level).isdigit()})
        for level in levels:
            row = self.values.rowCount()
            self.values.insertRow(row)
            self.values.setItem(row, 0, _LevelTableItem(str(level)))
            for column_index, item in enumerate(level_columns):
                if item["key"] == "value":
                    self.values.setItem(row, column_index + 1, QTableWidgetItem(str(values.get(str(level), ""))))
                elif item["key"] == "recharge":
                    combo = QComboBox(self.values)
                    combo.addItem("")
                    combo.addItems(RECHARGE_TYPES)
                    combo.setCurrentText(recharge.get(str(level), ""))
                    combo.currentTextChanged.connect(self._update_selected)
                    self.values.setCellWidget(row, column_index + 1, combo)
                self.values.sortItems(0, Qt.SortOrder.AscendingOrder)
                self._validate_level_rows(column)

    def _update_selected(self):
        if self._updating or not self._selected_key:
            return
        if self._selected_key in {column["key"] for column in GENERATED_COLUMNS}:
            return
        self.values.sortItems(0, Qt.SortOrder.AscendingOrder)
        column = next(column for column in self.model.editor_columns if column["key"] == self._selected_key)
        values = dict(column.get("values", {}))
        recharge = dict(column.get("recharge_values", {}))
        mini_columns = []
        if self.show_value.isChecked():
            mini_columns.append({"key": "value", "label": "Value", "visible": True, "merge": False})
        if self.show_recharge.isChecked():
            mini_columns.append({
                "key": "recharge",
                "label": "Recharge",
                "visible": True,
                "merge": self.merge_recharge.isChecked(),
            })
        level_column_indexes = {"value": 1}
        if self.values.columnCount() > 2:
            level_column_indexes["recharge"] = 2
        for row in range(self.values.rowCount()):
            level_item = self.values.item(row, 0)
            if level_item is None or not level_item.text().strip():
                continue
            level = level_item.text().strip()
            value_item = self.values.item(row, level_column_indexes["value"])
            if value_item is not None:
                values[level] = value_item.text()
            recharge_index = level_column_indexes.get("recharge")
            if recharge_index is not None:
                combo = self.values.cellWidget(row, recharge_index)
                if combo is not None and combo.currentText():
                    recharge[level] = combo.currentText()
        self.model.update_column(
            self._selected_key,
            label=self.display_name.text(),
            method=self.method.currentText(),
            values=values,
            recharge_values=recharge,
            mini_columns=mini_columns,
        )
        self._validate_level_rows(column)
        self._refresh_preview()

    def _method_changed(self, method):
        is_formula = method == "formula"
        self.formula_container.setVisible(is_formula)
        self.formula_label.setVisible(is_formula)
        self.values.setVisible(True)
        self._formula_changed()

    def _formula_changed(self, _text=None):
        if self._updating:
            return
        formula = self.formula_edit.text().strip()
        self._formula_error = ""
        formula_invalid = False
        if self.method.currentText() == "formula":
            try:
                validate_formula(formula)
            except ValueError as error:
                self._formula_error = str(error)
                formula_invalid = True
        self.formula_edit.setProperty("formulaInvalid", formula_invalid)
        style = self.formula_edit.style()
        style.unpolish(self.formula_edit)
        style.polish(self.formula_edit)
        if self._selected_key and self.method.currentText() == "formula":
            column = next(
                column for column in self.model.editor_columns
                if column["key"] == self._selected_key
            )
            self._validate_level_rows(column)
            self.model.update_column(self._selected_key, formula=formula)
            if not self._formula_error:
                self._refresh_preview()

    def _add_formula_variable(self, token):
        self.formula_edit.insert(token)

    def _add_column(self):
        self._update_selected()
        self.model.add_column("New column", values={"1": ""})
        self._refresh_preview()
        self._selected_key = self.model.configuration["columns"][-1]["key"]
        self._load_editor(self._selected_key)

    def _remove_column(self):
        if self._selected_key:
            self.model.remove_column(self._selected_key)
            self._selected_key = None
            self._refresh_preview()

    def _move_column(self, direction):
        if self._selected_key:
            self._update_selected()
            self.model.move_column(self._selected_key, "left" if direction < 0 else "right")
            self._refresh_preview()

    def _rebuild_value_table(self, enabled):
        if self._updating or not self._selected_key:
            return
        column = next(column for column in self.model.editor_columns if column["key"] == self._selected_key)
        if enabled:
            recharge = dict(column.get("recharge_values", {}))
            if column.get("method") == "table":
                recharge.setdefault("1", RECHARGE_TYPES[0])
            column["recharge_values"] = recharge
            column["mini_columns"] = [
                {"key": "value", "label": "Value", "visible": True, "merge": False},
                {"key": "recharge", "label": "Recharge", "visible": True, "merge": False},
            ]
        else:
            column["recharge_values"] = {}
            column["mini_columns"] = [
                {"key": "value", "label": "Value", "visible": True, "merge": False},
            ]
        self._load_values(column)
        self._update_selected()

    def _mini_columns_changed(self):
        if self._updating or not self._selected_key:
            return
        self._update_selected()
        column = next(column for column in self.model.editor_columns if column["key"] == self._selected_key)
        self._load_values(column)

    def _add_level(self):
        row = self.values.rowCount()
        self.values.insertRow(row)
        level = str(row + 1)
        self.values.setItem(row, 0, _LevelTableItem(level))
        for column in range(1, self.values.columnCount()):
            if self.values.horizontalHeaderItem(column).text() == "Recharge":
                combo = QComboBox(self.values)
                combo.addItem("")
                combo.addItems(RECHARGE_TYPES)
                self.values.setCellWidget(row, column, combo)
            else:
                self.values.setItem(row, column, QTableWidgetItem(""))

    def _remove_level(self):
        row = self.values.currentRow()
        if row >= 0:
            level = self.values.item(row, 0)
            if level and level.text() == "1":
                return
            self.values.removeRow(row)
            self._update_selected()

    def _validate_level_rows(self, column):
        levels = []
        invalid = []
        for row in range(self.values.rowCount()):
            item = self.values.item(row, 0)
            text = item.text().strip() if item else ""
            valid = text.isdigit() and 1 <= int(text) <= 20
            if valid and int(text) in levels:
                valid = False
            if valid:
                levels.append(int(text))
            else:
                invalid.append(row)
            if item:
                item.setBackground(Qt.GlobalColor.white if valid else Qt.GlobalColor.red)
        messages = []
        if invalid:
            messages.append("Levels must be unique integers from 1 through 20.")
        if column.get("method") == "table" and 1 not in levels:
            messages.append("Table columns require a level 1 value.")
        if self._formula_error:
            messages.append(self._formula_error)
        self.validation_label.setText(" ".join(messages))
