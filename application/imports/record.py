from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ImportedEntityRecord:
    """One normalized, validated entity ready for project persistence."""

    entity_type: str
    uid: str
    source_identity: str
    display_name: str
    payload: dict[str, Any]
    source_metadata: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "valid"
    provenance: str = ""


@dataclass(frozen=True)
class ImportIssue:
    """A source record that could not be included in an import batch."""

    index: int
    entity_type: str | None
    display_name: str | None
    status: str
    error: str
    source_location: str
    blocking: bool = True


@dataclass(frozen=True)
class ImportPreview:
    """Dry-run result used to decide whether one batch can be committed."""

    records: tuple[ImportedEntityRecord, ...]
    issues: tuple[ImportIssue, ...]
    source: str
    cancelled: bool = False
    created_count: int = 0
    updated_count: int = 0

    @property
    def can_commit(self) -> bool:
        return (
            not self.cancelled
            and bool(self.records)
            and not any(issue.blocking for issue in self.issues)
        )

    @property
    def counts(self) -> dict[str, int]:
        counts = {"valid": len(self.records)}
        for issue in self.issues:
            counts[issue.status] = counts.get(issue.status, 0) + 1
        if self.cancelled:
            counts["cancelled"] = 1
        return counts

    @property
    def result_counts(self) -> dict[str, int]:
        counts = {
            "created": self.created_count,
            "updated": self.updated_count,
            "skipped": 0,
            "duplicate": 0,
            "invalid": 0,
            "unsupported": 0,
        }
        for issue in self.issues:
            if issue.status in {"skipped", "duplicate", "unsupported"}:
                counts[issue.status] += 1
            else:
                counts["invalid"] += 1
        return counts