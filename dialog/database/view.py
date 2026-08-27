from copy import deepcopy

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMessageBox,
    QMenu,
    QPushButton,
    QSplitter,
    QTableView,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dialog.base.widget_editor import WidgetEditorView
from dialog.database.model import (
    DataFrameModel,
    DatabaseWorkspaceModel,
    FilterCondition,
    LookupStep,
)
from objects.query_object import QueryObject
from tools.widgets import SplitButton


class DatabaseWorkspaceView(WidgetEditorView):
    """Browse tables, run saved queries, and edit direct table results."""

    FILTER_OPERATORS = (
        "Equals",
        "Not equals",
        "Greater than",
        "Less than",
        "Greater than or equal",
        "Less than or equal",
        "Contains",
        "Starts with",
        "Ends with",
        "Equals (case-insensitive)",
        "Is empty",
        "Is not empty",
    )
    LOGICAL_OPERATORS = ("AND", "OR", "NOT", "XOR", "NAND", "NOR")
    FILTER_ROW_ROLE = Qt.ItemDataRole.UserRole
    FILTER_SQL_TEMPLATES = {
        "Equals": "{identifier} = {value}",
        "Not equals": "{identifier} != {value}",
        "Greater than": "{identifier} > {value}",
        "Less than": "{identifier} < {value}",
        "Greater than or equal": "{identifier} >= {value}",
        "Less than or equal": "{identifier} <= {value}",
        "Contains": "CAST({identifier} AS TEXT) LIKE {value}",
        "Starts with": "CAST({identifier} AS TEXT) LIKE {value}",
        "Ends with": "CAST({identifier} AS TEXT) LIKE {value}",
        "Equals (case-insensitive)": (
            "LOWER(CAST({identifier} AS TEXT)) = LOWER({value})"
        ),
        "Is empty": "({identifier} IS NULL OR CAST({identifier} AS TEXT) = '')",
        "Is not empty": "({identifier} IS NOT NULL AND CAST({identifier} AS TEXT) != '')",
    }

    def __init__(self, database_object, parent=None):
        editor_model = (
            database_object
            if isinstance(database_object, DatabaseWorkspaceModel)
            else DatabaseWorkspaceModel(database_object=database_object)
        )
        super().__init__(editor_model, parent=parent)
        self.database_object = editor_model.database_object
        self.result_model = None
        self._original_frame = None

        self.table_list = QListWidget()
        self.table_list.currentTextChanged.connect(self._load_table)
        self.lookup = editor_model.lookup
        self.lookup_enabled = QCheckBox("Use lookup")
        self.lookup_table = QComboBox()
        self.lookup_column = QComboBox()
        self.lookup_operator = QComboBox()
        self.lookup_operator.addItems(self.FILTER_OPERATORS)
        self.lookup_value = QLineEdit()
        self.lookup_value.setPlaceholderText("Value")
        self.lookup_return_column = QComboBox()
        self.bridge_table = QComboBox()
        self.bridge_lookup_column = QComboBox()
        self.bridge_output_column = QComboBox()
        self.output_table = QComboBox()
        self.output_column = QComboBox()
        self.lookup_table.currentTextChanged.connect(self._load_lookup_columns)
        self.bridge_table.currentTextChanged.connect(self._load_bridge_columns)
        self.output_table.currentTextChanged.connect(self._load_output_columns)
        self._lookup_steps_active = False
        self.lookup_steps_table = QTableWidget(0, 4)
        self.lookup_steps_table.setHorizontalHeaderLabels(
            ("Table", "Operator", "Input", "Output")
        )
        self.lookup_steps_table.horizontalHeader().setStretchLastSection(True)
        self._add_lookup_step_row()
        self.filter_column = QComboBox()
        self.filter_operator = QComboBox()
        self.filter_operator.addItems(self.FILTER_OPERATORS)
        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("Value")
        self._relationship = "AND"
        self.relationship_button = SplitButton("AND")
        relationship_menu = QMenu(self.relationship_button)
        relationship_group = QActionGroup(relationship_menu)
        relationship_group.setExclusive(True)
        for relationship in self.LOGICAL_OPERATORS:
            action = relationship_menu.addAction(relationship)
            action.setCheckable(True)
            action.setChecked(relationship == "AND")
            action.setData(relationship)
            relationship_group.addAction(action)
        relationship_group.triggered.connect(self._set_relationship)
        self.relationship_button.setMenu(relationship_menu)
        self.relationship_button.clicked.connect(self._queue_relationship)
        self.filter_list = QListWidget()
        self._filters = editor_model.filters
        self._pending_relationship = None
        self._pending_opening_groups = 0
        self._pending_closing_groups = 0
        self._pending_negated = False
        build_query_button = QPushButton("Build Query")
        build_query_button.clicked.connect(self.build_query)
        add_filter_button = QPushButton("Add Filter")
        add_filter_button.clicked.connect(self.add_filter)
        clear_filter_button = QPushButton("Clear Filters")
        clear_filter_button.clicked.connect(self.clear_filters)
        self.query_list = QComboBox()
        self.query_list.currentIndexChanged.connect(self._load_saved_query)
        self.sql_edit = QTextEdit()
        self.sql_edit.setPlaceholderText("SELECT * FROM table_name")
        self.result_table = QTableView()
        self.result_table.setSortingEnabled(True)
        self.status = QLabel()

        run_button = QPushButton("Run Query")
        run_button.clicked.connect(self.run_query)
        save_query_button = QPushButton("Save Query")
        save_query_button.clicked.connect(self.save_query)
        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        delete_row_button = QPushButton("Delete Row")
        delete_row_button.clicked.connect(self.delete_row)
        commit_button = QPushButton("Commit Changes")
        commit_button.clicked.connect(self.commit_changes)
        revert_button = QPushButton("Revert")
        revert_button.clicked.connect(self.revert_changes)

        query_buttons = QHBoxLayout()
        query_buttons.addWidget(run_button)
        query_buttons.addWidget(save_query_button)
        edit_buttons = QHBoxLayout()
        edit_buttons.addWidget(add_row_button)
        edit_buttons.addWidget(delete_row_button)
        edit_buttons.addWidget(commit_button)
        edit_buttons.addWidget(revert_button)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Tables"))
        left_layout.addWidget(self.table_list)
        left_layout.addWidget(QLabel("Saved query"))
        left_layout.addWidget(self.query_list)
        left_layout.addWidget(QLabel("SQL"))
        left_layout.addWidget(self.sql_edit)
        left_layout.addLayout(query_buttons)

        lookup_panel = QWidget()
        lookup_layout = QVBoxLayout(lookup_panel)
        lookup_box = QGroupBox("Multi-table lookup")
        lookup_form = QGridLayout(lookup_box)
        lookup_form.addWidget(self.lookup_steps_table, 0, 0, 1, 2)
        add_lookup_step_button = QPushButton("Add lookup step")
        add_lookup_step_button.clicked.connect(self._add_lookup_step_row)
        remove_lookup_step_button = QPushButton("Remove last step")
        remove_lookup_step_button.clicked.connect(self._remove_lookup_step_row)
        use_lookup_output_button = QPushButton("Use last output in Filter")
        use_lookup_output_button.clicked.connect(self._use_last_lookup_output)
        lookup_buttons = QHBoxLayout()
        lookup_buttons.addWidget(add_lookup_step_button)
        lookup_buttons.addWidget(remove_lookup_step_button)
        lookup_buttons.addWidget(use_lookup_output_button)
        lookup_form.addLayout(lookup_buttons, 1, 0, 1, 2)
        lookup_layout.addWidget(lookup_box)
        lookup_layout.addStretch()

        builder_panel = QWidget()
        builder_layout = QVBoxLayout(builder_panel)
        filter_box = QGroupBox("Filter")
        filter_layout = QGridLayout(filter_box)
        filter_layout.addWidget(QLabel("Column"), 0, 0)
        filter_layout.addWidget(self.filter_column, 0, 1)
        filter_layout.addWidget(QLabel("Operator"), 1, 0)
        filter_layout.addWidget(self.filter_operator, 1, 1)
        filter_layout.addWidget(QLabel("Value"), 2, 0)
        filter_layout.addWidget(self.filter_value, 2, 1)
        logic_layout = QVBoxLayout()
        open_group_button = QPushButton("Open group (")
        open_group_button.clicked.connect(lambda: self._change_selected_group("open"))
        close_group_button = QPushButton("Close group )")
        close_group_button.clicked.connect(lambda: self._change_selected_group("close"))
        negate_button = QPushButton("Toggle NOT")
        negate_button.clicked.connect(self._toggle_selected_negation)
        remove_filter_button = QPushButton("Remove filter")
        remove_filter_button.clicked.connect(self.remove_selected_filter)
        move_up_button = QPushButton("Move up")
        move_up_button.clicked.connect(lambda: self._move_selected_filter(-1))
        move_down_button = QPushButton("Move down")
        move_down_button.clicked.connect(lambda: self._move_selected_filter(1))
        logic_layout.addWidget(self.relationship_button)
        for button in (
            open_group_button,
            close_group_button,
            negate_button,
            remove_filter_button,
            move_up_button,
            move_down_button,
        ):
            logic_layout.addWidget(button)
        filter_layout.addLayout(logic_layout, 0, 2, 7, 1)
        filter_buttons = QHBoxLayout()
        filter_buttons.addWidget(add_filter_button)
        filter_buttons.addWidget(clear_filter_button)
        filter_layout.addLayout(filter_buttons, 5, 0, 1, 2)
        filter_layout.addWidget(self.filter_list, 6, 0, 1, 2)
        builder_layout.addWidget(filter_box)
        builder_layout.addWidget(build_query_button)

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(left_panel)
        top_splitter.addWidget(lookup_panel)
        top_splitter.addWidget(builder_panel)
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 1)

        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.addWidget(top_splitter)
        content_splitter.addWidget(self.result_table)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.addWidget(content_splitter, 1)
        layout.addLayout(edit_buttons)
        layout.addWidget(self.status)

        self.refresh_schema()

    def refresh_schema(self):
        self.table_list.clear()
        try:
            tables = self.database_object.service.list_tables()
        except Exception as error:
            self.status.setText(f"Unable to open database: {error}")
            return
        self.table_list.addItems(tables)
        for combo in (self.lookup_table, self.bridge_table, self.output_table):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(tables)
            combo.blockSignals(False)
        if self.lookup.output_table in tables:
            self.output_table.setCurrentText(self.lookup.output_table)
        elif tables:
            self.output_table.setCurrentText(tables[0])
        self._load_lookup_columns(self.lookup_table.currentText())
        self._load_bridge_columns(self.bridge_table.currentText())
        self._load_output_columns(self.output_table.currentText())
        self.query_list.clear()
        for query in self.database_object.query_objects:
            self.query_list.addItem(query.name, query)
        for query in self.database_object.queries:
            self.query_list.addItem(query["name"], query)
        for row in range(self.lookup_steps_table.rowCount()):
            self._populate_lookup_step_row(row)

    def _load_saved_query(self, index):
        if index >= 0:
            query = self.query_list.itemData(index)
            if isinstance(query, QueryObject):
                self._load_query_object(query)
            else:
                self.sql_edit.setPlainText(query.get("sql", ""))

    def _add_lookup_step_row(self):
        row = self.lookup_steps_table.rowCount()
        if row > 0:
            self._lookup_steps_active = True
        self.lookup_steps_table.insertRow(row)
        table_combo = QComboBox()
        operator_combo = QComboBox()
        operator_combo.addItems(self.FILTER_OPERATORS)
        self.lookup_steps_table.setCellWidget(row, 0, table_combo)
        self.lookup_steps_table.setCellWidget(row, 1, operator_combo)
        if row == 0:
            input_widget = QLineEdit()
            input_widget.setPlaceholderText("Value")
        else:
            input_widget = QComboBox()
        output_combo = QComboBox()
        self.lookup_steps_table.setCellWidget(row, 2, input_widget)
        self.lookup_steps_table.setCellWidget(row, 3, output_combo)
        table_combo.currentTextChanged.connect(self._lookup_row_table_changed)
        self._populate_lookup_step_row(row)

    def _remove_lookup_step_row(self):
        if self.lookup_steps_table.rowCount() > 1:
            self.lookup_steps_table.removeRow(self.lookup_steps_table.rowCount() - 1)

    def _populate_lookup_step_row(self, row, step=None):
        tables = self.database_object.service.list_tables()
        table_combo = self.lookup_steps_table.cellWidget(row, 0)
        operator_combo = self.lookup_steps_table.cellWidget(row, 1)
        table_combo.blockSignals(True)
        table_combo.clear()
        table_combo.addItems(tables)
        table_combo.blockSignals(False)
        if step is not None:
            table_combo.setCurrentText(step.table)
            operator_combo.setCurrentText(step.operator)
        self._populate_lookup_columns(row, step)

    def _populate_lookup_columns(self, row, step=None):
        table_combo = self.lookup_steps_table.cellWidget(row, 0)
        table_name = table_combo.currentText()
        columns = self._table_columns(table_name)
        input_widget = self.lookup_steps_table.cellWidget(row, 2)
        output_combo = self.lookup_steps_table.cellWidget(row, 3)
        if isinstance(input_widget, QComboBox):
            self._set_combo_values(
                input_widget,
                columns,
                step.input_value if step is not None else "",
            )
        self._set_combo_values(
            output_combo,
            columns,
            step.output if step is not None else "",
        )
    def _lookup_row_table_changed(self, table_name):
        for row in range(self.lookup_steps_table.rowCount()):
            if self.lookup_steps_table.cellWidget(row, 0) is self.sender():
                self._populate_lookup_columns(row)
                break

    def _lookup_steps(self):
        steps = []
        for row in range(self.lookup_steps_table.rowCount()):
            input_widget = self.lookup_steps_table.cellWidget(row, 2)
            steps.append(
                LookupStep(
                    table=self.lookup_steps_table.cellWidget(row, 0).currentText(),
                    operator=self.lookup_steps_table.cellWidget(row, 1).currentText(),
                    input_value=(
                        input_widget.text()
                        if isinstance(input_widget, QLineEdit)
                        else input_widget.currentText()
                    ),
                    output=self.lookup_steps_table.cellWidget(row, 3).currentText(),
                )
            )
        return steps

    def _use_last_lookup_output(self):
        steps = self._lookup_steps()
        if not steps or not steps[-1].table or not steps[-1].output:
            self.status.setText("Complete the last lookup step first.")
            return
        self._lookup_steps_active = True
        self.output_table.setCurrentText(steps[-1].table)
        self._set_combo_values(
            self.filter_column,
            self._table_columns(steps[-1].table),
            steps[-1].output,
        )

    def _load_query_object(self, query):
        self.sql_edit.setPlainText(query.sql)
        self._filters[:] = deepcopy(query.filters)
        self.lookup = deepcopy(query.lookup)
        self.model.lookup = self.lookup
        self.lookup_enabled.setChecked(self.lookup.enabled)
        self.lookup_table.setCurrentText(self.lookup.lookup_table)
        self.lookup_column.setCurrentText(self.lookup.lookup_column)
        self.lookup_operator.setCurrentText(self.lookup.lookup_operator)
        self.lookup_value.setText(self.lookup.lookup_value)
        self.lookup_return_column.setCurrentText(self.lookup.lookup_return_column)
        self.bridge_table.setCurrentText(self.lookup.bridge_table)
        self.bridge_lookup_column.setCurrentText(self.lookup.bridge_lookup_column)
        self.bridge_output_column.setCurrentText(self.lookup.bridge_output_column)
        self.output_table.setCurrentText(self.lookup.output_table)
        self.output_column.setCurrentText(self.lookup.output_column)
        self._refresh_filter_list()
        if query.table_name:
            self.table_list.setCurrentText(query.table_name)
        if query.lookup.steps:
            self._lookup_steps_active = True
            self.lookup_steps_table.setRowCount(0)
            for step in query.lookup.steps:
                self._add_lookup_step_row()
                self._populate_lookup_step_row(
                    self.lookup_steps_table.rowCount() - 1, step
                )

    def _load_table(self, table_name):
        if table_name:
            self.filter_column.clear()
            try:
                columns = [row[1] for row in self.database_object.service.table_schema(table_name)]
            except Exception as error:
                self.status.setText(f"Unable to read table columns: {error}")
                return
            self.filter_column.addItems(columns)
            self.output_table.setCurrentText(table_name)
            self.sql_edit.setPlainText(f'SELECT * FROM "{table_name}"')
            self.run_query()

    def _table_columns(self, table_name):
        if not table_name:
            return []
        return [row[1] for row in self.database_object.service.table_schema(table_name)]

    @staticmethod
    def _set_combo_values(combo, values, selected=""):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        if selected in values:
            combo.setCurrentText(selected)
        combo.blockSignals(False)

    def _load_lookup_columns(self, table_name):
        columns = self._table_columns(table_name)
        self._set_combo_values(self.lookup_column, columns, self.lookup.lookup_column)
        self._set_combo_values(
            self.lookup_return_column, columns, self.lookup.lookup_return_column
        )

    def _load_bridge_columns(self, table_name):
        columns = self._table_columns(table_name)
        self._set_combo_values(
            self.bridge_lookup_column, columns, self.lookup.bridge_lookup_column
        )
        self._set_combo_values(
            self.bridge_output_column, columns, self.lookup.bridge_output_column
        )

    def _load_output_columns(self, table_name):
        columns = self._table_columns(table_name)
        self._set_combo_values(self.output_column, columns, self.lookup.output_column)
        self._set_combo_values(self.filter_column, columns, self.filter_column.currentText())

    def add_filter(self):
        column = self.filter_column.currentText()
        value = self.filter_value.text().strip()
        condition = FilterCondition(
            column=column,
            operator=self.filter_operator.currentText(),
            value=value,
            relationship=(
                self._pending_relationship
                or (self._relationship if self._filters else "AND")
            ),
            opening_groups=self._pending_opening_groups,
            closing_groups=self._pending_closing_groups,
            negated=self._pending_negated,
        )
        self._filters.append(condition)
        self._clear_pending_expression()
        self._refresh_filter_list()
        self.filter_value.clear()

    def clear_filters(self):
        self._filters.clear()
        self._clear_pending_expression()
        self.filter_list.clear()

    def _set_relationship(self, action):
        self._relationship = action.data()
        self.relationship_button.setText(self._relationship)

    def set_relationship(self, relationship):
        for action in self.relationship_button.menu().actions():
            if action.data() == relationship:
                self._set_relationship(action)
                return
        raise ValueError(f"Unknown relationship: {relationship}")

    def _refresh_filter_list(self):
        selected_filter = self._selected_filter_row()
        self.filter_list.clear()
        for index, condition in enumerate(self._filters):
            for _ in range(condition.opening_groups):
                self._add_filter_expression_row("(", index, "group")
            if index:
                self._add_filter_expression_row(condition.relationship, index, "relationship")
            if condition.negated:
                self._add_filter_expression_row("NOT", index, "negation")
            self._add_filter_expression_row(
                f"{condition.column} {condition.operator} {condition.value}",
                index,
                "condition",
            )
            for _ in range(condition.closing_groups):
                self._add_filter_expression_row(")", index, "group")
        if self._pending_relationship is not None:
            self._add_filter_expression_row(
                self._pending_relationship, -1, "pending_relationship"
            )
        for _ in range(self._pending_opening_groups):
            self._add_filter_expression_row("(", -1, "pending_group")
        if self._pending_negated:
            self._add_filter_expression_row("NOT", -1, "pending_negation")
        for _ in range(self._pending_closing_groups):
            self._add_filter_expression_row(")", -1, "pending_group")
        for row in range(self.filter_list.count()):
            if self.filter_list.item(row).data(self.FILTER_ROW_ROLE) == (
                selected_filter,
                "condition",
            ):
                self.filter_list.setCurrentRow(row)
                break

    def _add_filter_expression_row(self, text, filter_index, row_type):
        item = QListWidgetItem(text)
        self.filter_list.addItem(item)
        item.setData(self.FILTER_ROW_ROLE, (filter_index, row_type))

    def _change_selected_group(self, group):
        row = self._selected_filter_row()
        if row < 0:
            if group == "open":
                self._pending_opening_groups = 1 - self._pending_opening_groups
            else:
                self._pending_closing_groups = 1 - self._pending_closing_groups
            self._refresh_filter_list()
            return
        condition = self._filters[row]
        attribute = "opening_groups" if group == "open" else "closing_groups"
        current = getattr(condition, attribute)
        setattr(condition, attribute, max(0, current - 1) if current else 1)
        self._refresh_filter_list()

    def _toggle_selected_negation(self):
        row = self._selected_filter_row()
        if row < 0:
            self._pending_negated = not self._pending_negated
            self._refresh_filter_list()
            return
        self._filters[row].negated = not self._filters[row].negated
        self._refresh_filter_list()

    def _queue_relationship(self):
        self._pending_relationship = self._relationship
        self._refresh_filter_list()

    def _clear_pending_expression(self):
        self._pending_relationship = None
        self._pending_opening_groups = 0
        self._pending_closing_groups = 0
        self._pending_negated = False

    def remove_selected_filter(self):
        row = self._selected_filter_row()
        if row < 0:
            return
        self._filters.pop(row)
        self._refresh_filter_list()

    def _selected_filter_row(self):
        item = self.filter_list.currentItem()
        if item is None:
            return -1
        filter_index, _ = item.data(self.FILTER_ROW_ROLE)
        return filter_index

    def _move_selected_filter(self, offset):
        row = self._selected_filter_row()
        target = row + offset
        if row < 0 or not 0 <= target < len(self._filters):
            return
        self._filters[row], self._filters[target] = (
            self._filters[target],
            self._filters[row],
        )
        self._refresh_filter_list()
        self.filter_list.setCurrentRow(target)

    @staticmethod
    def _quote_identifier(value):
        return f'"{value.replace(chr(34), chr(34) * 2)}"'

    @staticmethod
    def _quote_value(value):
        if value.upper() == "NULL":
            return "NULL"
        try:
            float(value)
        except ValueError:
            return "'" + value.replace("'", "''") + "'"
        return value

    def _filter_sql(self, column, operator, value):
        identifier = self._quote_identifier(column)
        value_patterns = {
            "Contains": f"%{value}%",
            "Starts with": f"{value}%",
            "Ends with": f"%{value}",
        }
        template = self.FILTER_SQL_TEMPLATES.get(operator)
        if template is None:
            raise ValueError(f"Unknown filter operator: {operator}")
        value_sql = self._quote_value(value_patterns.get(operator, value))
        return template.format(identifier=identifier, value=value_sql)

    def build_query(self):
        self._capture_lookup_state()
        if self._lookup_steps_active and self.lookup.steps:
            if not self._validate_lookup_steps():
                return
            table_name = self._quote_identifier(self.lookup.steps[-1].table)
        elif self.lookup.enabled:
            if not self._validate_lookup():
                return
            table_name = self._quote_identifier(self.lookup.output_table)
        else:
            table_item = self.table_list.currentItem()
            if table_item is None:
                self.status.setText("Select a table first.")
                return
            table_name = self._quote_identifier(table_item.text())
        if not self._validate_filters():
            return
        sql = f'SELECT * FROM {table_name}'
        if self._lookup_steps_active and self.lookup.steps:
            lookup_query = self._lookup_steps_sql(self.lookup.steps[:-1])
            final_step = self.lookup.steps[-1]
            sql += (
                f" WHERE {self._quote_identifier(final_step.input_value)} "
                f"IN ({lookup_query})"
            )
        elif self.lookup.enabled:
            lookup = self.lookup
            lookup_filter = self._filter_sql(
                lookup.lookup_column, lookup.lookup_operator, lookup.lookup_value
            )
            lookup_query = (
                f"SELECT {self._quote_identifier(lookup.lookup_return_column)} "
                f"FROM {self._quote_identifier(lookup.lookup_table)} "
                f"WHERE {lookup_filter}"
            )
            bridge_query = (
                f"SELECT {self._quote_identifier(lookup.bridge_output_column)} "
                f"FROM {self._quote_identifier(lookup.bridge_table)} "
                f"WHERE {self._quote_identifier(lookup.bridge_lookup_column)} "
                f"IN ({lookup_query})"
            )
            sql += (
                f" WHERE {self._quote_identifier(lookup.output_column)} "
                f"IN ({bridge_query})"
            )
        if self._filters:
            expression = None
            for index, condition in enumerate(self._filters):
                condition_sql = self._filter_sql(
                    condition.column, condition.operator, condition.value
                )
                if condition.negated:
                    condition_sql = f"NOT ({condition_sql})"
                condition_sql = (
                    "(" * condition.opening_groups
                    + condition_sql
                    + ")" * condition.closing_groups
                )
                if expression is None:
                    expression = condition_sql
                else:
                    expression = self._combine_conditions(
                        expression, condition_sql, condition.relationship
                    )
            sql += f" {'AND' if self._lookup_steps_active and self.lookup.steps or self.lookup.enabled else 'WHERE'} {expression}"
        self.sql_edit.setPlainText(sql)
        self.run_query()

    def _capture_lookup_state(self):
        lookup = self.lookup
        lookup.steps = self._lookup_steps() if self._lookup_steps_active else []
        lookup.enabled = self.lookup_enabled.isChecked()
        lookup.lookup_table = self.lookup_table.currentText()
        lookup.lookup_column = self.lookup_column.currentText()
        lookup.lookup_operator = self.lookup_operator.currentText()
        lookup.lookup_value = self.lookup_value.text().strip()
        lookup.lookup_return_column = self.lookup_return_column.currentText()
        lookup.bridge_table = self.bridge_table.currentText()
        lookup.bridge_lookup_column = self.bridge_lookup_column.currentText()
        lookup.bridge_output_column = self.bridge_output_column.currentText()
        lookup.output_table = self.output_table.currentText()
        lookup.output_column = self.output_column.currentText()

    def _lookup_steps_sql(self, steps):
        first = steps[0]
        columns = self._table_columns(first.table)
        filter_column = next(
            (column for column in columns if column != first.output), ""
        )
        query = (
            f"SELECT {self._quote_identifier(first.output)} "
            f"FROM {self._quote_identifier(first.table)} "
            f"WHERE {self._filter_sql(filter_column, first.operator, first.input_value)}"
        )
        for step in steps[1:]:
            query = (
                f"SELECT {self._quote_identifier(step.output)} "
                f"FROM {self._quote_identifier(step.table)} "
                f"WHERE {self._quote_identifier(step.input_value)} IN ({query})"
            )
        return query

    def _validate_lookup_steps(self):
        steps = self.lookup.steps
        for index, step in enumerate(steps):
            if not step.table:
                self.status.setText(f"Lookup row {index + 1} needs a table.")
                return False
            if not step.output:
                self.status.setText(f"Lookup row {index + 1} needs an output column.")
                return False
            if not step.input_value:
                self.status.setText(f"Lookup row {index + 1} needs an input.")
                return False
            if index and step.input_value not in self._table_columns(step.table):
                self.status.setText(
                    f"Lookup row {index + 1} input must be a column of its table."
                )
                return False
        first_columns = self._table_columns(steps[0].table)
        if not any(column != steps[0].output for column in first_columns):
            self.status.setText("The first lookup table needs an input column.")
            return False
        return True

    def _validate_lookup(self):
        lookup = self.lookup
        required = (
            (lookup.lookup_table, "Select a lookup table."),
            (lookup.lookup_column, "Select a lookup filter column."),
            (lookup.lookup_return_column, "Select a lookup return column."),
            (lookup.bridge_table, "Select a bridge table."),
            (lookup.bridge_lookup_column, "Select a bridge lookup column."),
            (lookup.bridge_output_column, "Select a bridge output column."),
            (lookup.output_table, "Select an output table."),
            (lookup.output_column, "Select an output match column."),
        )
        for value, message in required:
            if not value:
                self.status.setText(message)
                return False
        if (
            not lookup.lookup_value
            and lookup.lookup_operator not in ("Is empty", "Is not empty")
        ):
            self.status.setText("Enter a lookup filter value.")
            return False
        return True

    def _validate_filters(self):
        if self._pending_relationship is not None or self._pending_opening_groups:
            self.status.setText("Complete the pending filter expression first.")
            return False
        if self._pending_closing_groups or self._pending_negated:
            self.status.setText("Complete the pending filter expression first.")
            return False
        if not self._filters:
            return True
        depth = 0
        for index, condition in enumerate(self._filters):
            if not condition.column:
                self.status.setText(f"Filter {index + 1} needs a column.")
                return False
            if (
                not condition.value
                and condition.operator not in ("Is empty", "Is not empty")
            ):
                self.status.setText(f"Filter {index + 1} needs a value.")
                return False
            depth += condition.opening_groups
            depth -= condition.closing_groups
            if depth < 0:
                self.status.setText("Filter groups close before they open.")
                return False
        if depth:
            self.status.setText("Filter groups are not balanced.")
            return False
        return True

    @staticmethod
    def _combine_conditions(left, right, logical_operator):
        if logical_operator == "AND":
            return f"({left}) AND ({right})"
        if logical_operator == "OR":
            return f"({left}) OR ({right})"
        if logical_operator == "NOT":
            return f"({left}) AND NOT ({right})"
        if logical_operator == "XOR":
            return f"(({left}) AND NOT ({right})) OR (NOT ({left}) AND ({right}))"
        if logical_operator == "NAND":
            return f"NOT (({left}) AND ({right}))"
        if logical_operator == "NOR":
            return f"NOT (({left}) OR ({right}))"
        raise ValueError(f"Unknown logical operator: {logical_operator}")

    def run_query(self):
        try:
            frame = self.database_object.service.query(self.sql_edit.toPlainText())
        except Exception as error:
            self.status.setText(str(error))
            return False
        self._original_frame = frame.copy()
        self.result_model = DataFrameModel(frame, self)
        self.result_table.setModel(self.result_model)
        self.status.setText(f"{len(frame)} row(s), {len(frame.columns)} column(s)")
        return True

    def save_query(self):
        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            return
        self._capture_lookup_state()
        table_item = self.table_list.currentItem()
        table_name = self.lookup.output_table if self.lookup.enabled else (
            table_item.text() if table_item is not None else ""
        )
        name = f"Query {len(self.database_object.query_objects) + 1:03d}"
        query = QueryObject(
            name=name,
            database_guid=self.database_object.guid,
            sql=sql,
            table_name=table_name,
            filters=deepcopy(self._filters),
            lookup=deepcopy(self.lookup),
        )
        self.database_object.add_query_object(query)
        self.refresh_schema()
        self.query_list.setCurrentIndex(self.query_list.count() - 1)

    def add_row(self):
        if self.result_model is None:
            return
        frame = self.result_model.frame
        self.result_model.beginInsertRows(QModelIndex(), len(frame), len(frame))
        self.result_model.frame.loc[len(frame)] = [None] * len(frame.columns)
        self.result_model.endInsertRows()

    def delete_row(self):
        if self.result_model is None:
            return
        index = self.result_table.currentIndex()
        if index.isValid():
            self.result_model.beginRemoveRows(QModelIndex(), index.row(), index.row())
            self.result_model.frame = self.result_model.frame.drop(
                self.result_model.frame.index[index.row()]
            ).reset_index(drop=True)
            self.result_model.endRemoveRows()

    def commit_changes(self):
        if self.result_model is None:
            return
        if self.table_list.currentItem() is None:
            QMessageBox.information(self, "Read-only query", "Select a table before committing changes.")
            return
        table_name = self.table_list.currentItem().text()
        schema = self.database_object.service.table_schema(table_name)
        primary_keys = [row[1] for row in schema if row[5]]
        if len(primary_keys) != 1 or primary_keys[0] not in self.result_model.frame.columns:
            QMessageBox.warning(self, "Primary key required", "Direct editing requires one primary-key column.")
            return
        key = primary_keys[0]
        current_keys = set()
        for _, row in self.result_model.frame.iterrows():
            values = row.to_dict()
            if row[key] is None:
                values.pop(key)
                self.database_object.service.insert_row(table_name, values)
            else:
                current_keys.add(row[key])
                values.pop(key)
                self.database_object.service.update_row(table_name, key, row[key], values)
        if self._original_frame is not None:
            for original_key in self._original_frame[key]:
                if original_key not in current_keys:
                    self.database_object.service.delete_row(
                        table_name, key, original_key
                    )
        self.database_object._changed()
        self.run_query()

    def revert_changes(self):
        if self._original_frame is not None:
            self.result_model = DataFrameModel(self._original_frame, self)
            self.result_table.setModel(self.result_model)
