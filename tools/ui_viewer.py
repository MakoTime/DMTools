"""Live-preview Qt Designer .ui files with the DMTools application theme."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QFileSystemWatcher, QIODevice, QTimer, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from application.file_window import ProjectPreview
from components.tree.view import TreeView
from tools.theme_builder import ThemeBuilderPanel


BASE_DIRECTORY = Path(__file__).resolve().parents[1]
TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "ui_templates"
ACTIVE_THEME_PATH = BASE_DIRECTORY / "views" / "app_theme.qss"


class UiViewer(QMainWindow):
    """Watch a Designer form on disk and refresh its live preview on save."""

    def __init__(self, initial_path: Path | None = None):
        super().__init__()
        self.setWindowTitle("DMTools UI Viewer")
        self.resize(1280, 820)
        self.current_path: Path | None = None
        self.last_source: bytes | None = None
        self.preview_widget: QWidget | None = None
        self.base_theme = ACTIVE_THEME_PATH.read_text(encoding="utf-8")
        self.last_saved_theme = self.base_theme

        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._schedule_reload)
        self.watcher.directoryChanged.connect(self._schedule_reload)
        self.reload_timer = QTimer(self)
        self.reload_timer.setSingleShot(True)
        self.reload_timer.setInterval(180)
        self.reload_timer.timeout.connect(self._reload_from_disk)
        self.theme_timer = QTimer(self)
        self.theme_timer.setSingleShot(True)
        self.theme_timer.setInterval(160)
        self.theme_timer.timeout.connect(self._apply_theme_draft)

        self._build_interface()
        self.theme_builder.stylesheetChanged.connect(self._on_theme_changed)
        self.theme_status.setText("App theme copy")
        QApplication.instance().setStyleSheet(self.base_theme)
        self._load_templates()
        if initial_path is not None:
            self.open_file(initial_path)
        elif self.template_picker.count():
            self._load_selected_template()

    def _build_interface(self) -> None:
        central = QWidget(self)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 16, 18, 14)
        root_layout.setSpacing(12)

        source_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to a .ui file; press Enter to preview")
        self.path_edit.returnPressed.connect(self._open_path_from_field)
        source_row.addWidget(self.path_edit, 1)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_for_file)
        source_row.addWidget(browse_button)

        open_button = QPushButton("Preview")
        open_button.setDefault(True)
        open_button.clicked.connect(self._open_path_from_field)
        source_row.addWidget(open_button)

        reload_button = QPushButton("Reload")
        reload_button.setToolTip("Reload the current .ui file from disk")
        reload_button.clicked.connect(self._reload_from_disk)
        source_row.addWidget(reload_button)

        self.template_picker = QComboBox()
        self.template_picker.setMinimumWidth(190)
        source_row.addWidget(self.template_picker)

        template_button = QPushButton("Preview template")
        template_button.clicked.connect(self._load_selected_template)
        source_row.addWidget(template_button)

        self.theme_button = QPushButton("Theme")
        self.theme_button.setCheckable(True)
        self.theme_button.setToolTip("Show the editable theme draft")
        self.theme_button.toggled.connect(self._toggle_theme_panel)
        source_row.addWidget(self.theme_button)
        root_layout.addLayout(source_row)

        heading_row = QHBoxLayout()
        heading = QLabel("LIVE PREVIEW")
        heading.setObjectName("uiSectionLabel")
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        self.preview_status = QLabel("Choose a .ui file or template")
        self.preview_status.setObjectName("uiPreviewStatus")
        heading_row.addWidget(self.preview_status)
        root_layout.addLayout(heading_row)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setChildrenCollapsible(False)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("uiPreviewFrame")
        self.preview_layout = QVBoxLayout(self.preview_frame)
        self.preview_layout.setContentsMargins(20, 20, 20, 20)
        self.workspace_splitter.addWidget(self.preview_frame)

        self.theme_panel = QWidget()
        self.theme_panel.setObjectName("uiThemePanel")
        theme_panel_layout = QVBoxLayout(self.theme_panel)
        theme_panel_layout.setContentsMargins(12, 8, 0, 0)
        theme_panel_layout.setSpacing(8)

        theme_header = QHBoxLayout()
        theme_heading = QLabel("THEME DRAFT")
        theme_heading.setObjectName("uiSectionLabel")
        theme_header.addWidget(theme_heading)
        theme_header.addStretch(1)
        self.theme_status = QLabel("App theme copy")
        self.theme_status.setObjectName("uiPreviewStatus")
        theme_header.addWidget(self.theme_status)
        theme_panel_layout.addLayout(theme_header)

        theme_actions = QHBoxLayout()
        reset_theme_button = QPushButton("Reset")
        reset_theme_button.setToolTip("Restore the active application theme")
        reset_theme_button.clicked.connect(self._reset_theme_draft)
        theme_actions.addWidget(reset_theme_button)
        theme_actions.addStretch(1)
        save_theme_button = QPushButton("Save theme as...")
        save_theme_button.clicked.connect(self._save_theme_as)
        theme_actions.addWidget(save_theme_button)
        theme_panel_layout.addLayout(theme_actions)

        self.theme_builder = ThemeBuilderPanel(self.base_theme)
        theme_panel_layout.addWidget(self.theme_builder, 1)
        self.workspace_splitter.addWidget(self.theme_panel)
        self.theme_panel.hide()
        self.workspace_splitter.setSizes([900, 420])

        root_layout.addWidget(self.workspace_splitter, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage("Watching the selected .ui file for changes")

    def _toggle_theme_panel(self, visible: bool) -> None:
        self.theme_panel.setVisible(visible)
        self.workspace_splitter.setSizes([760, 500] if visible else [1260, 0])

    def _on_theme_changed(self, stylesheet: str) -> None:
        changed = stylesheet != self.last_saved_theme
        self.theme_status.setText("Unsaved draft" if changed else "Saved draft")
        self.theme_timer.start()

    def _apply_theme_draft(self) -> None:
        QApplication.instance().setStyleSheet(self._compose_theme())

    def _compose_theme(self) -> str:
        return self.theme_builder.stylesheet

    def _reset_theme_draft(self) -> None:
        self.theme_timer.stop()
        self.theme_builder.reset_stylesheet(self.base_theme)
        self.theme_timer.stop()
        QApplication.instance().setStyleSheet(self.base_theme)
        changed = self.base_theme != self.last_saved_theme
        self.theme_status.setText("Unsaved draft" if changed else "App theme copy")

    def _save_theme_as(self) -> None:
        default_path = Path.home() / "dmtools-custom-theme.qss"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save theme copy",
            str(default_path),
            "Qt stylesheets (*.qss);;All files (*)",
        )
        if path:
            target = Path(path)
            if not target.suffix:
                target = target.with_suffix(".qss")
            self._write_theme_copy(target)

    def _write_theme_copy(self, path: Path) -> bool:
        target = path.expanduser().resolve()
        if target == ACTIVE_THEME_PATH.resolve():
            QMessageBox.warning(
                self,
                "Active theme is protected",
                "Save the draft to a different .qss file.",
            )
            return False
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            theme_text = self._compose_theme()
            target.write_text(theme_text, encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(self, "Theme save failed", str(error))
            return False

        self.last_saved_theme = theme_text
        self.theme_status.setText(f"Saved: {target.name}")
        self.statusBar().showMessage(f"Saved theme copy to {target}", 5000)
        return True

    def _load_templates(self) -> None:
        for path in sorted(TEMPLATE_DIRECTORY.glob("*.ui")):
            self.template_picker.addItem(path.stem.replace("_", " ").title(), str(path))

    def _open_path_from_field(self) -> None:
        value = self.path_edit.text().strip().strip('"')
        if value:
            self.open_file(Path(value).expanduser())

    def _browse_for_file(self) -> None:
        start = str(self.current_path or BASE_DIRECTORY)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Preview Qt Designer file",
            start,
            "Qt Designer files (*.ui);;All files (*)",
        )
        if path:
            self.open_file(Path(path))

    def _load_selected_template(self) -> None:
        template_path = self.template_picker.currentData()
        if template_path:
            self.open_file(Path(template_path))

    def open_file(self, path: Path) -> None:
        path = path.expanduser().resolve()
        if not path.is_file():
            self._set_status(f"File not found: {path}")
            return
        if path.suffix.lower() != ".ui":
            self._set_status("Choose a Qt Designer .ui file")
            return

        self.current_path = path
        self.path_edit.setText(str(path))
        self._replace_watches()
        self._reload_from_disk()

    def _replace_watches(self) -> None:
        watched_paths = self.watcher.files() + self.watcher.directories()
        if watched_paths:
            self.watcher.removePaths(watched_paths)
        if self.current_path is None:
            return

        paths_to_watch = [self.current_path.parent]
        existing_paths = [str(path) for path in paths_to_watch if path.exists()]
        if existing_paths:
            self.watcher.addPaths(existing_paths)

    def _schedule_reload(self, _path: str) -> None:
        self.reload_timer.start()

    def _reload_from_disk(self) -> None:
        if self.current_path is None:
            return
        self._replace_watches()
        try:
            source = self.current_path.read_bytes()
        except OSError:
            self._set_status("Waiting for the .ui file to become available")
            return

        if source == self.last_source and self.preview_widget is not None:
            self._set_status(f"Watching {self.current_path.name}")
            return
        if not self._load_preview(source):
            return

        self.last_source = source
        self._set_status(f"Updated from {self.current_path.name}")
        self.statusBar().showMessage(f"Watching {self.current_path}", 5000)

    def _load_preview(self, source: bytes) -> bool:
        loader = QUiLoader()
        loader.registerCustomWidget(TreeView)
        loader.registerCustomWidget(ProjectPreview)

        buffer = QBuffer(self)
        buffer.setData(QByteArray(source))
        if not buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            self._set_status("Could not read UI source")
            return False
        widget = loader.load(buffer)
        buffer.close()
        if widget is None:
            self._set_status(loader.errorString() or "Invalid .ui file")
            return False

        widget.setParent(self.preview_frame)
        widget.setWindowFlags(Qt.WindowType.Widget)
        self.preview_layout.addWidget(widget)
        widget.show()

        old_widget = self.preview_widget
        self.preview_widget = widget
        if old_widget is not None:
            self.preview_layout.removeWidget(old_widget)
            old_widget.deleteLater()
        return True

    def _set_status(self, message: str) -> None:
        self.preview_status.setText(message)
        self.statusBar().showMessage(message)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    application = QApplication.instance() or QApplication([sys.argv[0]])
    theme_path = BASE_DIRECTORY / "views" / "app_theme.qss"
    application.setStyleSheet(theme_path.read_text(encoding="utf-8"))

    initial_path = Path(arguments[0]) if arguments else None
    viewer = UiViewer(initial_path)
    viewer.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())