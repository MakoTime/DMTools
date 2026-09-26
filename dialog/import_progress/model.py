from dataclasses import dataclass
import inspect
from threading import Event, Lock
from time import monotonic

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
    existing_entities: tuple
    source_name: str
    work: object | None = None
    operation_name: str | None = None
    status: str = "Preparing import..."
    current: int = 0
    total: int = 0
    preview: object | None = None
    error: str | None = None
    cancelling: bool = False

    def __post_init__(self):
        self.task = None
        self.result = None
        self._cancelled = Event()
        self._progress_lock = Lock()
        self._started_at = None
        self._phase_started_at = None
        self._activity = []
        self._phase_index = 0
        self._phase_count = 1 if self.work is not None else 3

    def start(self):
        if self.task is not None:
            return self.task
        now = monotonic()
        with self._progress_lock:
            self._started_at = now
            self._phase_started_at = now
        work = self._run_operation if self.is_operation else self._run_preview
        self.task = self.task_runner.enqueue(
            self.model_task_name,
            work,
        )
        return self.task

    @property
    def is_operation(self):
        return self.work is not None

    @property
    def model_task_name(self):
        if self.is_operation:
            return self.operation_name or self.source_name
        return f"Import {self.source_name}"

    def _run_preview(self, set_progress):
        preview_method = getattr(self.service, f"preview_{self.source_format}")
        return preview_method(
            self.source,
            duplicate_policy=self.duplicate_policy,
            existing_source_identities=self.existing_source_identities,
            existing_entities=self.existing_entities,
            is_cancelled=self._cancelled.is_set,
            progress_callback=lambda current, total: self._record_progress(
                current, total, set_progress
            ),
            status_callback=self._record_status,
        )

    def _run_operation(self, set_progress):
        parameters = inspect.signature(self.work).parameters.values()
        positional = tuple(
            parameter
            for parameter in parameters
            if parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        )
        if len(positional) >= 3:
            return self.work(
                lambda current, total: self._record_progress(
                    current, total, set_progress
                ),
                self._cancelled.is_set,
                self._record_status,
            )
        if len(positional) >= 2:
            return self.work(
                lambda current, total: self._record_progress(
                    current, total, set_progress
                ),
                self._cancelled.is_set,
            )
        return self.work(set_progress)

    def _record_status(self, status):
        now = monotonic()
        if self.is_operation:
            phase_index = 0
        elif status in {"Validating normalized records", "Normalizing JSON entities"}:
            phase_index = 1
        elif status == "Resolving entity references":
            phase_index = 2
        else:
            phase_index = 0
        with self._progress_lock:
            self.status = status
            self.current = 0
            self.total = 0
            self._phase_started_at = now
            self._phase_index = phase_index
            if not self._activity or self._activity[-1] != status:
                self._activity.append(status)
                self._activity = self._activity[-8:]

    def _record_progress(self, current, total, set_progress):
        with self._progress_lock:
            self.current = current
            self.total = total
        set_progress(current / total if total else 0.0)

    def snapshot(self):
        with self._progress_lock:
            return self.status, self.current, self.total

    def details_snapshot(self):
        with self._progress_lock:
            return (
                self.status,
                self.current,
                self.total,
                self._started_at,
                self._phase_started_at,
                tuple(self._activity),
            )

    def overall_snapshot(self):
        with self._progress_lock:
            return self._phase_index, self._phase_count, self.current, self.total

    def finish(self, task):
        if task is not self.task:
            return False
        if task.status is TaskStatus.COMPLETED:
            if self.is_operation:
                self.result = task.result
            else:
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