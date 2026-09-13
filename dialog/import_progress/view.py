from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from .model import ImportProgressModel


class ImportProgressView(QDialog):
    """Show feedback while an entity import preview runs on a worker thread."""

    def __init__(self, model: ImportProgressModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Importing Entities")
        self.setModal(True)
        self.setMinimumWidth(460)

        self.source_label = QLabel(model.source_name)
        self.source_label.setWordWrap(True)
        self.status_label = QLabel(model.status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.button_box)

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(50)
        self.progress_timer.timeout.connect(self._sync_progress)
        self.model.task_runner.task_finished.connect(self._task_finished)
        self.button_box.rejected.connect(self._request_cancel)
        self._started = False
        self._running = False

    def exec(self):
        if not self._started:
            self._started = True
            self._running = True
            self._set_status(
                f"Reading and validating {self.model.source_format.upper()} entities..."
            )
            self.model.start()
            self.progress_timer.start()
        return super().exec()

    def _set_status(self, status):
        self.model.status = status
        self.status_label.setText(status)

    def _sync_progress(self):
        status, current, total = self.model.snapshot()
        self.model.update_progress(current, total)
        if not total:
            self.progress_bar.setRange(0, 0)
            self._set_status(status)
            return
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(current)
        self.status_label.setText(f"{status}: {current} of {total}")

    def _task_finished(self, task):
        if not self.model.finish(task):
            return
        self._running = False
        self.progress_timer.stop()
        self._sync_progress()
        if self.model.error:
            self._set_status(f"Import failed: {self.model.error}")
        if (
            self.model.error
            or self.model.cancelling
            or self.model.preview is None
            or self.model.preview.cancelled
        ):
            self.reject()
        else:
            self.accept()

    def _request_cancel(self):
        if not self._running:
            self.reject()
            return
        self.model.cancel()
        self.status_label.setText(self.model.status)
        self.cancel_button.setEnabled(False)

    def closeEvent(self, event):
        if self._running:
            self._request_cancel()
            event.ignore()
            return
        super().closeEvent(event)