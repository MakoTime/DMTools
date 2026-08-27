import sqlite3
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)
from PySide6.QtCore import QSignalBlocker

from application.sql_import import mysql_dump_to_sqlite


class DatabaseView(QDialog):
    def __init__(self, model, parent=None, project_directory=None, is_new=False):
        super().__init__(parent)

        self.setWindowTitle("Database Definition")
        self.resize(900, 650)

        self.name_edit = QLineEdit(model.name)
        self.path_edit = QLineEdit(model.database_path)
        self.query_name_edit = QLineEdit()
        self.query_edit = QTextEdit()
        self.query_edit.setPlaceholderText("SELECT * FROM table_name")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_database)
        path_layout = QVBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)

        self.model = model
        self.project_directory = Path(project_directory) if project_directory else None
        self.is_new = is_new
        self.external_database_path = None
        self.query_list = QListWidget()
        with QSignalBlocker(self.query_list):
            for query in model.queries:
                self.query_list.addItem(query.name)
        if model.queries:
            self.query_list.setCurrentRow(0)
            self.query_name_edit.setText(model.queries[0].name)
            self.query_edit.setPlainText(model.queries[0].sql)
        self.query_list.currentRowChanged.connect(self._select_query)

        add_query_button = QPushButton("Add Query")
        add_query_button.clicked.connect(self._add_query)
        remove_query_button = QPushButton("Remove Query")
        remove_query_button.clicked.connect(self._remove_query)
        query_buttons = QVBoxLayout()
        query_buttons.addWidget(add_query_button)
        query_buttons.addWidget(remove_query_button)

        self.table = QTableView()
        self.table.setModel(model.database)
        self.table.setSortingEnabled(True)

        self.table.horizontalHeader().setStretchLastSection(True)

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("SQLite file", path_layout)

        query_layout = QVBoxLayout()
        query_layout.addWidget(self.query_list)
        query_layout.addLayout(query_buttons)
        form.addRow("Queries", query_layout)
        form.addRow("Query name", self.query_name_edit)
        form.addRow("SQL", self.query_edit)

        self.test_button = QPushButton("Test Query")
        self.test_button.clicked.connect(self._test_query)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b42318;")
        self.error_label.setWordWrap(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.test_button)
        layout.addWidget(self.table)
        layout.addWidget(self.error_label)
        layout.addWidget(self.buttons)

    def _browse_database(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Browse Existing SQLite Database",
            filter="Database files (*.sqlite *.db *.sql);;All files (*)",
        )
        if path:
            self.external_database_path = Path(path)
            self.path_edit.setText(path)

    def update_model(self):
        self.model.name = self.name_edit.text().strip()
        self.model.database_path = self.path_edit.text().strip()
        self._save_current_query()
        self.model.database.database_path = self.model.database_path
        self.model.database.query = self.model.query
        return self.model

    def _accept(self):
        self.error_label.clear()
        model = self.update_model()
        if not model.name:
            self._show_error("Enter a database name.")
            return
        if not model.database_path and not self.external_database_path:
            self._show_error("Choose or enter a database source file.")
            return
        try:
            if self.is_new:
                if self.project_directory is None:
                    raise ValueError("A project must be open before creating a database")
                database_directory = self.project_directory / "data"
                database_directory.mkdir(parents=True, exist_ok=True)
                source_path = self.external_database_path or Path(model.database_path)
                database_name = (
                    f"{source_path.stem}.sqlite"
                    if source_path.suffix.lower() == ".sql"
                    else source_path.name
                )
                database_path = database_directory / database_name
                if source_path.suffix.lower() == ".sql":
                    script = source_path.read_text(encoding="utf-8")
                    with sqlite3.connect(database_path) as connection:
                        connection.executescript(mysql_dump_to_sqlite(script))
                elif self.external_database_path is not None:
                    shutil.copyfile(self.external_database_path, database_path)
                else:
                    database_path.touch(exist_ok=True)
                model.database_path = str(database_path)
                self.path_edit.setText(str(database_path))
            else:
                database_path = Path(model.database_path)
            database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(database_path):
                pass
        except (OSError, UnicodeError, sqlite3.Error, ValueError) as error:
            self._show_error(f"Unable to import database: {error}")
            return
        self.accept()

    def _show_error(self, message):
        self.error_label.setText(message)

    def _save_current_query(self):
        row = self.query_list.currentRow()
        if row < 0 or row >= len(self.model.queries):
            return
        self.model.queries[row].name = self.query_name_edit.text().strip() or "Query"
        self.model.queries[row].sql = self.query_edit.toPlainText().strip()
        self.query_list.item(row).setText(self.model.queries[row].name)
        self.model.query = self.model.queries[row].sql

    def _select_query(self, row):
        self._save_current_query()
        if 0 <= row < len(self.model.queries):
            query = self.model.queries[row]
            self.query_name_edit.setText(query.name)
            self.query_edit.setPlainText(query.sql)

    def _add_query(self):
        self._save_current_query()
        self.model.add_query()
        self.query_list.addItem(self.model.queries[-1].name)
        self.query_list.setCurrentRow(self.query_list.count() - 1)

    def _remove_query(self):
        row = self.query_list.currentRow()
        self.model.remove_query(row)
        if row >= 0:
            self.query_list.takeItem(row)
        if self.query_list.count():
            self.query_list.setCurrentRow(min(row, self.query_list.count() - 1))

    def _test_query(self):
        model = self.update_model()
        if not model.database.load():
            self.table.setToolTip(model.database.error or "Unable to run query")
