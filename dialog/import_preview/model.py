from dataclasses import dataclass

from application.imports import ImportPreview
from dialog.base.editor import EditorModel


@dataclass
class ImportPreviewModel(EditorModel):
    """Read-only import summary awaiting user confirmation."""

    preview: ImportPreview
    destination: str = "compendium"
    duplicate_policy: str = "replace"
    skip_invalid: bool = False

    @property
    def summary(self):
        lines = [f"Valid records: {len(self.preview.records)}"]
        lines.extend(
            f"{status.title()}: {count}"
            for status, count in self.preview.result_counts.items()
        )
        for issue in self.preview.issues[:20]:
            lines.append(
                f"{issue.source_location}: {issue.display_name or 'Unknown'} - {issue.error}"
            )
        if len(self.preview.issues) > 20:
            lines.append(f"...and {len(self.preview.issues) - 20} more issue(s)")
        return "\n".join(lines)

    def validate(self):
        if self.preview.cancelled or not self.preview.records:
            raise ValueError("There are no valid records to import.")
        if not self.preview.can_commit and not self.skip_invalid:
            raise ValueError(
                "Select 'Skip invalid records' to import the valid records."
            )
        if self.destination != "compendium":
            raise ValueError("Imports must target the Compendium namespace.")
