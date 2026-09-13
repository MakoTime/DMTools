from dataclasses import dataclass
from threading import Event, Lock

from projectfoundry import TaskStatus


@dataclass
class ImportProgressModel:
    """Track temporary state for one background import preview task."""

    task_runner: object
    service: object
    source: object
    source_format: str
    duplicate_policy: str
    existing_source_identities: tuple
    source_name: str
    status: str = "Preparing import..."
    current: int = 0
    total: int = 0
    preview: object | None = None
    error: str | None = None
    cancelling: bool = False

    def __post_init__(self):
        self.task = None
        self._cancelled = Event()
        self._progress_lock = Lock()

    def start(self):
        if self.task is not None:
            return self.task
        self.task = self.task_runner.enqueue(
            f"Import {self.source_name}",
            self._run_preview,
        )
        return self.task

    def _run_preview(self, set_progress):
        preview_method = getattr(self.service, f"preview_{self.source_format}")
        return preview_method(
            self.source,
            duplicate_policy=self.duplicate_policy,
            existing_source_identities=self.existing_source_identities,
            is_cancelled=self._cancelled.is_set,
            progress_callback=lambda current, total: self._record_progress(
                current, total, set_progress
            ),
            status_callback=self._record_status,
        )

    def _record_status(self, status):
        with self._progress_lock:
            self.status = status
            self.current = 0
            self.total = 0

    def _record_progress(self, current, total, set_progress):
        with self._progress_lock:
            self.current = current
            self.total = total
        set_progress(current / total if total else 0.0)

    def snapshot(self):
        with self._progress_lock:
            return self.status, self.current, self.total

    def finish(self, task):
        if task is not self.task:
            return False
        if task.status is TaskStatus.COMPLETED:
            self.preview = task.result
        elif task.status is TaskStatus.FAILED:
            self.error = task.error or "Import failed"
        return True

    def update_progress(self, current, total):
        self.current = current
        self.total = total

    def cancel(self):
        if self.cancelling:
            return
        self.cancelling = True
        self.status = "Cancelling import..."
        self._cancelled.set()
        if self.task is not None:
            self.task_runner.cancel(self.task)