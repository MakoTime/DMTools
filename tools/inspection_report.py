"""Generate a small HTML/Markdown inspection report from a canonical entity DB."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from html import escape
import json
from pathlib import Path
import re
from typing import Any

from application.entity_database import EntityDatabaseStore, EntityQueryRow
from application.entity_rendering import render_entity_html, render_entity_markdown


SAMPLE_NAMES: dict[str, tuple[str, ...]] = {
    "class": ("Bard", "Wizard"),
    "subclass": ("College of Lore", "School of Evocation"),
    "monster": ("Acolyte", "Archmage", "Goblin"),
    "spell": ("Fireball", "Cure Wounds", "Time Stop"),
    "race": ("Dwarf", "Elf", "Human"),
    "item": ("Backpack", "Longsword", "Necklace of Fireballs"),
    "background": ("Acolyte", "Soldier"),
    "feat": ("Alert", "Fey Touched", "Lucky"),
    "ability": ("Action Surge", "Arcane Recovery"),
}


def _find_sample(store: EntityDatabaseStore, entity_type: str, names: Iterable[str]):
    for name in names:
        matches = store.query(
            entity_type,
            field="name",
            operator="eq",
            value=name,
            limit=1,
        )
        if matches:
            return matches[0]

    matches = store.query(entity_type, limit=1)
    return matches[0] if matches else None


def select_samples(store: EntityDatabaseStore) -> tuple[EntityQueryRow, ...]:
    """Select one deterministic, useful record for each supported entity type."""
    samples = []
    for entity_type, names in SAMPLE_NAMES.items():
        record = _find_sample(store, entity_type, names)
        if record is not None:
            samples.append(record)
    return tuple(samples)


def _safe_stem(record: EntityQueryRow) -> str:
    value = f"{record.entity_type}-{record.uid}"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "entity"


def review_record(record: EntityQueryRow) -> list[dict[str, Any]]:
    """Return actionable presentation issues for one rendered record."""
    markdown = render_entity_markdown(record)
    issues: list[dict[str, Any]] = []

    if re.search(r"\{['\"]\w+['\"]:\s", markdown):
        issues.append({
            "code": "raw-mapping",
            "entity_type": record.entity_type,
            "name": record.name,
            "message": "Rendered output exposes a Python mapping representation.",
        })
    if re.search(r"\w(?:As|Source:)", markdown):
        issues.append({
            "code": "adjacent-metadata",
            "entity_type": record.entity_type,
            "name": record.name,
            "message": "Feature text and metadata are adjacent without a separator.",
        })
    storage_tokens = sorted(set(re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", markdown)))
    if storage_tokens:
        issues.append({
            "code": "storage-label",
            "entity_type": record.entity_type,
            "name": record.name,
            "message": "Rendered output exposes storage-oriented identifiers.",
            "values": storage_tokens,
        })
    if record.entity_type == "class" and record.payload.get("spellcasting"):
        progression = record.source_metadata.get("presentation_progression", {})
        cantrips = progression.get("cantrips_known", {}) if isinstance(progression, dict) else {}
        if not cantrips:
            issues.append({
                "code": "missing-cantrip-progression",
                "entity_type": record.entity_type,
                "name": record.name,
                "message": "Spellcasting class has no cantrip progression metadata.",
            })
    return issues


def _write_review(output_dir: Path, samples: tuple[EntityQueryRow, ...]) -> list[dict[str, Any]]:
    issues = [issue for record in samples for issue in review_record(record)]
    (output_dir / "review.json").write_text(
        json.dumps(issues, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = ["# Inspection Review", ""]
    if not issues:
        lines.append("No presentation issues detected in the selected samples.")
    else:
        lines.extend([
            f"{len(issues)} issue(s) detected in the selected samples.",
            "",
        ])
        for issue in issues:
            values = f" Values: {', '.join(issue['values'])}." if issue.get("values") else ""
            lines.append(
                f"- **{issue['code']}**: {issue['name']} ({issue['entity_type']}). "
                f"{issue['message']}{values}"
            )
    (output_dir / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return issues


def write_report(database_path: Path, output_dir: Path) -> tuple[EntityQueryRow, ...]:
    """Render representative records into one self-contained inspection folder."""
    store = EntityDatabaseStore(database_path).initialize()
    samples = select_samples(store)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for record in samples:
        stem = _safe_stem(record)
        markdown_path = output_dir / f"{stem}.md"
        html_path = output_dir / f"{stem}.html"
        markdown_path.write_text(render_entity_markdown(record), encoding="utf-8")
        html_path.write_text(render_entity_html(record), encoding="utf-8")
        entries.append((record, html_path.name, markdown_path.name))
    issues = _write_review(output_dir, samples)

    rows = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>DMTools entity inspection report</title>",
        "<style>body{font:16px system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ccc;text-align:left;padding:.5rem}"
        "a{color:#145da0}</style></head><body>",
        "<h1>DMTools entity inspection report</h1>",
        f"<p>Database: {escape(str(database_path))}</p>",
        f'<p><a href="review.html">Review issues ({len(issues)})</a></p>',
        "<table><thead><tr><th>Type</th><th>Name</th><th>HTML</th><th>Markdown</th></tr></thead><tbody>",
    ]
    for record, html_name, markdown_name in entries:
        rows.append(
            "<tr>"
            f"<td>{escape(record.entity_type)}</td>"
            f"<td>{escape(record.name)}</td>"
            f'<td><a href="{escape(html_name)}">Open HTML</a></td>'
            f'<td><a href="{escape(markdown_name)}">Open Markdown</a></td>'
            "</tr>"
        )
    rows.extend(["</tbody></table>", "</body></html>"])
    (output_dir / "index.html").write_text("\n".join(rows), encoding="utf-8")
    review_html = "<html><body><pre>" + escape(
        (output_dir / "review.md").read_text(encoding="utf-8")
    ) + "</pre></body></html>"
    (output_dir / "review.html").write_text(review_html, encoding="utf-8")
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="Canonical entity SQLite database")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("inspection-report"),
        help="Output directory (default: inspection-report)",
    )
    args = parser.parse_args()
    samples = write_report(args.database, args.output)
    print(f"Wrote {len(samples)} entity inspections to {args.output.resolve()}")
    for record in samples:
        print(f"- {record.entity_type}: {record.name}")


if __name__ == "__main__":
    main()
