from time import monotonic

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
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
        self.details_toggle = QCheckBox("Show details")
        self.details_label = QLabel()
        self.details_log = QPlainTextEdit()
        self.details_log.setReadOnly(True)
        self.details_log.setMaximumBlockCount(8)
        self.details_log.setMaximumHeight(100)
        self.details_log.setVisible(False)
        self.details_panel = QWidget()
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_log)
        self.details_panel.setVisible(False)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_toggle)
        layout.addWidget(self.details_panel)
        layout.addWidget(self.button_box)

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(50)
        self.progress_timer.timeout.connect(self._sync_progress)
        self.model.task_runner.task_finished.connect(self._task_finished)
        self.button_box.rejected.connect(self._request_cancel)
        self.details_toggle.toggled.connect(self._set_details_visible)
        self._started = False
        self._running = False
        self.layout().activate()
        self._collapsed_height = self.sizeHint().height()

    def _set_details_visible(self, visible):
        self.details_panel.setVisible(visible)
        self.layout().activate()
        if visible:
            self.adjustSize()
        else:
            self.resize(self.width(), self._collapsed_height)

    def exec(self):
        if not self._started:
            self._started = True
            self._running = True
            status = self.model.operation_name or (
                f"Reading and validating {self.model.source_format.upper()} entities..."
            )
            self._set_status(status)
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
            self._sync_details()
            return
        if hasattr(self.model, "overall_snapshot"):
            phase_index, phase_count, current, total = self.model.overall_snapshot()
            fraction = current / total if total else 0.0
            overall_fraction = (phase_index + fraction) / phase_count
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(round(overall_fraction * 1000))
            self.status_label.setText(f"{status}: {current} of {total}")
        else:
            self.progress_bar.setRange(0, max(total, 1))
            self.progress_bar.setValue(current)
            self.status_label.setText(f"{status}: {current} of {total}")
        self._sync_details()

    def _sync_details(self):
        if not hasattr(self.model, "details_snapshot"):
            return
        (
            status,
            current,
            total,
            started_at,
            phase_started_at,
            activity,
        ) = self.model.details_snapshot()
        if started_at is None:
            return
        elapsed = max(monotonic() - started_at, 0.0)
        phase_elapsed = max(monotonic() - (phase_started_at or started_at), 0.0)
        rate = current / phase_elapsed if current and phase_elapsed else 0.0
        remaining = (total - current) / rate if rate and total else None
        overall_fraction = current / total if total else 0.0
        if hasattr(self.model, "overall_snapshot"):
            phase_index, phase_count, current, total = self.model.overall_snapshot()
            fraction = current / total if total else 0.0
            overall_fraction = (phase_index + fraction) / phase_count
            remaining = (
                elapsed * (1 - overall_fraction) / overall_fraction
                if overall_fraction > 0
                else None
            )
        remaining_text = self._format_duration(remaining)
        rate_text = f"{rate:.1f} records/s" if rate else "Calculating..."
        self.details_label.setText(
            "<b>Phase:</b> "
            f"{status}<br>"
            f"<b>Progress:</b> {current} of {total or '?'}<br>"
            f"<b>Overall:</b> {overall_fraction:.0%}<br>"
            f"<b>Elapsed:</b> {self._format_duration(elapsed)} &nbsp; "
            f"<b>Rate:</b> {rate_text} &nbsp; "
            f"<b>Remaining:</b> {remaining_text}"
        )
        self.details_log.setPlainText("\n".join(activity))
        self.details_log.setVisible(bool(activity))

    @staticmethod
    def _format_duration(seconds):
        if seconds is None:
            return "Calculating..."
        seconds = int(max(seconds, 0))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes:02d}m"
        if minutes:
            return f"{minutes}m {seconds:02d}s"
        return f"{seconds}s"

    def _task_finished(self, task):
        if not self.model.finish(task):
            return
        self._running = False
        self.progress_timer.stop()
        self._sync_progress()
        if self.model.error:
            self._set_status(f"Import failed: {self.model.error}")
        failed_preview = (
            not self.model.is_operation
            and (
                self.model.preview is None
                or self.model.preview.cancelled
            )
        )
        if self.model.error or self.model.cancelling or failed_preview:
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