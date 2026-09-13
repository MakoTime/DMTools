from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
)

from application.entity_references import EntityNavigationController
from dialog.base.widget_editor import WidgetEditorView
from dialog.entity_reference import EntityReferenceDelegate
from dialog.entity_query_results.model import EntityQueryResultsModel
from tools.widgets import MultiSelectComboBox
from tools.widgets.pagination import PaginationControls

from .model import EntitySearchModel


class EntitySearchView(WidgetEditorView):
    """Build category-aware parameters and preview matching entities."""

    def __init__(
        self,
        model: EntitySearchModel,
        *,
        project_controller=None,
        on_open=None,
        origin_uid=None,
        parent=None,
        on_close=None,
    ):
        super().__init__(model, parent=parent, on_close=on_close)
        self.navigation = (
            EntityNavigationController(project_controller, on_open=on_open)
            if project_controller is not None
            else None
        )
        self.origin_uid = origin_uid
        self.setWindowTitle(f"Search {model.entity_type.replace('_', ' ').title()}s")
        self.resize(900, 600)

        self.field_combo = QComboBox()
        for field_name in model.fields:
            self.field_combo.addItem(model.field_label(field_name), field_name)
        self.operator_combo = QComboBox()
        self.value_edit = QLineEdit()
        self.value_edit.setClearButtonEnabled(True)
        self.value_combo = MultiSelectComboBox()
        self.boolean_check = QCheckBox("Yes")
        self.value_stack = QStackedWidget()
        self.value_stack.addWidget(self.value_edit)
        self.value_stack.addWidget(self.value_combo)
        self.value_stack.addWidget(self.boolean_check)
        self.field_combo.currentIndexChanged.connect(self._refresh_operators)
        self.value_edit.returnPressed.connect(self.add_parameter)
        self._refresh_operators()

        add_button = QPushButton("Add Parameter")
        add_button.clicked.connect(self.add_parameter)
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_parameter)
        self.parameter_list = QListWidget()

        editor = QFormLayout()
        editor.addRow("Field", self.field_combo)
        editor.addRow("Match", self.operator_combo)
        editor.addRow("Value", self.value_stack)
        parameter_buttons = QHBoxLayout()
        parameter_buttons.addWidget(add_button)
        parameter_buttons.addWidget(remove_button)

        parameters = QGroupBox("Parameters")
        parameter_layout = QVBoxLayout(parameters)
        parameter_layout.addLayout(editor)
        parameter_layout.addLayout(parameter_buttons)
        parameter_layout.addWidget(self.parameter_list, 1)

        self.results_table = QTableView()
        self.results_table.setModel(EntityQueryResultsModel())
        self.results_table.setSortingEnabled(True)
        self.results_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.doubleClicked.connect(self.open_selected_entity)
        self.reference_delegate = EntityReferenceDelegate(
            EntityQueryResultsModel.EntityReferenceRole, self.results_table
        )
        self.reference_delegate.referenceActivated.connect(self._open_reference)
        self.results_table.setItemDelegateForColumn(0, self.reference_delegate)
        self.pagination = PaginationControls(self.results_table.model(), self)
        open_button = QPushButton("Open Selected")
        open_button.clicked.connect(self.open_selected_entity)
        results = QGroupBox("Results")
        results_layout = QVBoxLayout(results)
        results_layout.addWidget(self.results_table)
        results_layout.addWidget(self.pagination)
        results_layout.addWidget(open_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(parameters)
        splitter.addWidget(results)
        splitter.setSizes((320, 580))
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        button_box = QHBoxLayout()
        search_button = QPushButton("Run Search")
        search_button.clicked.connect(self.run_search)
        button_box.addWidget(search_button)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.status_label)
        layout.addLayout(button_box)

        self.run_search()

    def _refresh_operators(self):
        field_name = self.field_combo.currentData()
        selected = self.operator_combo.currentData()
        self.operator_combo.clear()
        for operator in self.model.operators_for(field_name):
            self.operator_combo.addItem(self.model.OPERATOR_LABELS[operator], operator)
        index = self.operator_combo.findData(selected)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        value_type = self.model.value_type_for(field_name)
        choices = self.model.choices_for(field_name)
        if value_type == "boolean":
            self.boolean_check.setChecked(True)
            self.value_stack.setCurrentWidget(self.boolean_check)
        elif choices:
            self.value_stack.setCurrentWidget(self.value_combo)
        else:
            self.value_stack.setCurrentWidget(self.value_edit)
        self.value_combo.clear()
        self.value_combo.set_options(
            (choice.replace("_", " ").title(), choice) for choice in choices
        )

    def add_parameter(self):
        try:
            criterion = self.model.add_criterion(
                self.field_combo.currentData(),
                self.operator_combo.currentData(),
                self._current_value(),
            )
        except ValueError as error:
            self._show_error(error)
            return None
        self.parameter_list.addItem(self._criterion_text(criterion))
        self.value_edit.clear()
        self.run_search()
        return criterion

    def _current_value(self):
        field_name = self.field_combo.currentData()
        if self.model.value_type_for(field_name) == "boolean":
            return self.boolean_check.isChecked()
        if self.model.choices_for(field_name):
            return self.value_combo.checked_values()
        return self.value_edit.text()

    def remove_parameter(self):
        row = self.parameter_list.currentRow()
        if self.model.remove_criterion(row) is None:
            return None
        self.parameter_list.takeItem(row)
        self.run_search()
        return row

    def run_search(self):
        old_model = self.results_table.model()
        if isinstance(old_model, EntityQueryResultsModel):
            old_model.release_rows()
        try:
            rows = self.model.execute()
        except ValueError as error:
            self._show_error(error)
            return None
        result_model = EntityQueryResultsModel(rows, self.results_table)
        self.results_table.setModel(result_model)
        self.pagination.set_model(result_model)
        self.status_label.setStyleSheet("")
        self.status_label.setText(f"{len(rows)} result(s)")
        return rows

    def closeEvent(self, event):
        results_model = self.results_table.model()
        if isinstance(results_model, EntityQueryResultsModel):
            results_model.release_rows()
        self.model.release_results()
        self.notify_closed("window")
        super().closeEvent(event)

    def open_selected_entity(self):
        rows = self.results_table.selectionModel().selectedRows()
        if not rows or self.navigation is None:
            return None
        reference = self.results_table.model().data(
            rows[0], EntityQueryResultsModel.EntityReferenceRole
        )
        return self._open_reference(reference)

    def _open_reference(self, reference):
        if self.navigation is None:
            return None
        return self.navigation.open(reference, origin_uid=self.origin_uid)

    def apply_model(self):
        try:
            return self.model.apply()
        except ValueError as error:
            self._show_error(error)
            return None

    def _show_error(self, error):
        self.status_label.setStyleSheet("color: #b42318;")
        self.status_label.setText(str(error))

    def _criterion_text(self, criterion):
        field_label = self.model.field_label(criterion.field)
        value = criterion.value
        if isinstance(value, tuple):
            value = ", ".join(str(item).replace("_", " ").title() for item in value)
        return (
            f"{field_label} {self.model.OPERATOR_LABELS[criterion.operator]} "
            f"{value}"
        )
