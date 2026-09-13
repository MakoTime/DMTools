"""Compare derived entity presentation structures without comparing protected prose."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re
from typing import Any


@dataclass(frozen=True)
class PresentationDifference:
    path: str
    severity: str
    expected: Any
    actual: Any


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.structure: list[tuple[str, str]] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._stack.append(tag)
        if tag in {"h1", "h2", "h3", "h4", "table", "thead", "tbody", "tr", "th", "td", "strong", "a"}:
            self.structure.append(("open", tag))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "table", "thead", "tbody", "tr", "th", "td", "strong", "a"}:
            self.structure.append(("close", tag))
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.structure.append(("text", text))


def normalize_markdown(value: str) -> list[tuple[str, str]]:
    result = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        if stripped.startswith("#"):
            result.append(("heading", stripped.lstrip("#").strip()))
        elif stripped.startswith("|"):
            result.append(("table", re.sub(r"\s+", " ", stripped)))
        elif "[" in stripped and "](" in stripped:
            result.append(("link", stripped))
        elif stripped.startswith("**"):
            result.append(("bold", stripped))
    return result


def normalize_html(value: str) -> list[tuple[str, str]]:
    parser = _StructureParser()
    parser.feed(value)
    return parser.structure


def normalize_compact(value: Any) -> list[tuple[str, str]]:
    if not isinstance(value, dict):
        return [("value", type(value).__name__)]
    return [("field", key) for key in value]


def compare_presentations(expected: Any, actual: Any, format: str) -> list[PresentationDifference]:
    """Return deterministic structural differences for markdown, html, or compact data."""
    normalizers = {
        "markdown": normalize_markdown,
        "html": normalize_html,
        "compact": normalize_compact,
    }
    try:
        normalizer = normalizers[format]
    except KeyError as error:
        raise ValueError(f"Unsupported presentation format: {format}") from error
    expected_structure = normalizer(expected)
    actual_structure = normalizer(actual)
    differences = []
    for index in range(max(len(expected_structure), len(actual_structure))):
        expected_item = expected_structure[index] if index < len(expected_structure) else None
        actual_item = actual_structure[index] if index < len(actual_structure) else None
        if expected_item != actual_item:
            differences.append(
                PresentationDifference(
                    path=f"structure[{index}]",
                    severity="error" if expected_item and actual_item else "warning",
                    expected=expected_item,
                    actual=actual_item,
                )
            )
    return differences
