"""Compare canonical XML and 5eSRD API records for the parity audit.

Examples:
    python -m tools.api_xml_parity --xml 5eFile.xml --api-json audit/api_cases.json
    python -m tools.api_xml_parity --xml 5eFile.xml --live monsters:aboleth

API fixture records use ``{"collection": ..., "payload": {...}}`` entries. The
fixture payload is passed through the same SRDAdaptor and import validation path
as live API imports.
"""

from __future__ import annotations

import argparse
import json
from io import BytesIO
from xml.etree import ElementTree
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api.adaptor import COLLECTION_TYPES, SRDAdaptor
from api.client import SRDClient
from application.imports.registry import ENTITY_REGISTRY
from application.imports.service import EntityImportService
from parsers.dispatcher import dispatch_root
from parsers.xml_parser import parse_xml


SHARED_CORE_FIELDS: dict[str, tuple[str, ...]] = {
    "monster": ("name", "size", "creature_type", "alignment", "ability_scores", "movement", "features", "actions", "reactions", "legendary_actions", "challenge_rating"),
    "spell": ("name", "level", "school", "classes", "casting_time", "target", "components", "material", "duration", "ritual", "concentration", "effects"),
    "class": ("name", "hit_dice", "saving_throws", "armor_proficiencies", "weapon_proficiencies", "tool_proficiencies", "skill_choices", "spellcasting", "features", "ability_score_increase", "required_stats"),
    "race": ("name", "subtype", "size", "movement", "ability_score_increases", "languages", "skill_proficiencies", "features", "senses", "spell_grants"),
    "background": ("name", "description", "skill_proficiencies", "tool_proficiencies", "languages", "features"),
    "feat": ("name", "description", "prerequisite", "ability_score_increases", "weapon_proficiencies", "features"),
    "item": ("name", "category", "weight", "cost", "weapon", "armor", "magic_item", "features", "description"),
    "subclass": ("name", "class", "description", "features", "spells", "tags"),
}


@dataclass(frozen=True)
class ComparisonCase:
    collection: str
    name: str
    xml_source: str
    api_source: str
    api_name: str | None = None
    api_paths: dict[str, str] | None = None


def _value(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def classify(xml_value: Any, api_value: Any, *, api_path: str | None = None) -> str:
    if xml_value == api_value:
        return "equal"
    if xml_value is not None and api_value is None:
        if api_path:
            return "hydration-mismatch"
        return "missing"
    if xml_value is None and api_value is not None:
        return "source-only"
    if type(xml_value) is not type(api_value):
        return "shape-mismatch"
    if isinstance(xml_value, str) and xml_value.casefold() == api_value.casefold():
        return "normalization-mismatch"
    return "value-mismatch"


def _validated_xml(path: Path, cases: list[ComparisonCase]) -> dict[str, list[dict[str, Any]]]:
    names = {case.name.casefold() for case in cases}
    subclass_names = {
        case.name.casefold() for case in cases if case.collection == "subclasses"
    }
    selected = []
    stack = []
    for event, element in ElementTree.iterparse(path, events=("start", "end")):
        if event == "start":
            stack.append(element)
            continue
        if len(stack) == 2:
            name = element.findtext("name")
            serialized = ElementTree.tostring(element, encoding="unicode")
            is_requested = name and name.casefold() in names
            has_requested_subclass = (
                element.tag == "class"
                and any(subclass_name in serialized.casefold() for subclass_name in subclass_names)
            )
            if is_requested or has_requested_subclass:
                selected.append(serialized)
            element.clear()
        stack.pop()
    if not selected:
        raise ValueError(f"No requested XML records found in {path}")
    document = ("<compendium>" + "".join(selected) + "</compendium>").encode()
    parsed = parse_xml(BytesIO(document))
    results = dispatch_root(parsed)
    preview = EntityImportService().preview_api(
        [
            {
                "entity_type": result.get("tag"),
                "display_name": result.get("name"),
                "payload": result.get("data", {}),
                "source_identity": f"{path}:{result.get('tag')}:{result.get('name')}",
            }
            for result in results
        ]
    )
    if preview.issues:
        raise ValueError(f"XML validation failed: {preview.issues}")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in preview.records:
        grouped.setdefault(record.entity_type, []).append(record.payload)
    return grouped


def _validated_api(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    adapted = []
    adaptor = SRDAdaptor()
    for record in records:
        collection = record["collection"]
        adapted.append(adaptor.record(collection, record["payload"], parent=record.get("parent")))
    preview = EntityImportService().preview_api(adapted)
    if preview.issues:
        raise ValueError(f"API validation failed: {preview.issues}")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in preview.records:
        grouped.setdefault(record.entity_type, []).append(record.payload)
    return grouped


def compare(xml_payload: dict[str, Any], api_payload: dict[str, Any], entity_type: str, *, xml_source: str, api_source: str, api_paths: dict[str, str] | None = None) -> list[dict[str, Any]]:
    definition = ENTITY_REGISTRY[entity_type]
    xml_payload = definition.validate_payload(xml_payload)
    api_payload = definition.validate_payload(api_payload)
    report = []
    for field in SHARED_CORE_FIELDS[entity_type]:
        xml_value = _value(xml_payload, field.removeprefix("class."))
        api_value = _value(api_payload, field.removeprefix("class."))
        api_path = (api_paths or {}).get(field)
        report.append({
            "entity_type": entity_type,
            "name": xml_payload.get("name"),
            "canonical_field": field,
            "xml_value": xml_value,
            "api_value": api_value,
            "xml_source": xml_source,
            "api_source": api_source,
            "xml_field": f"payload.{field}",
            "api_field": api_path or f"payload.{field}",
            "model": definition.model.__name__,
            "schema": definition.schema,
            "classification": classify(xml_value, api_value, api_path=api_path),
        })
    return report


def _find(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for payload in records:
        if str(payload.get("name", "")).casefold() == name.casefold():
            return payload
    raise ValueError(f"No record named {name!r}")


def run(xml_path: Path, api_records: list[dict[str, Any]], cases: list[ComparisonCase]) -> list[dict[str, Any]]:
    xml_records = _validated_xml(xml_path, cases)
    api_grouped = _validated_api(api_records)
    report = []
    for case in cases:
        entity_type = COLLECTION_TYPES[case.collection]
        api_name = case.api_name or case.name
        report.extend(compare(
            _find(xml_records.get(entity_type, []), case.name),
            _find(api_grouped.get(entity_type, []), api_name),
            entity_type,
            xml_source=case.xml_source,
            api_source=case.api_source,
            api_paths=case.api_paths,
        ))
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--api-json", type=Path)
    parser.add_argument("--live", action="append", metavar="COLLECTION:NAME")
    parser.add_argument("--case", action="append", metavar="COLLECTION:NAME", help="Compare a named record; defaults to every API fixture record")
    return parser


def main() -> int:
    args = _parser().parse_args()
    api_records: list[dict[str, Any]] = []
    if args.api_json:
        api_records.extend(json.loads(args.api_json.read_text(encoding="utf-8")))
    if args.live:
        client = SRDClient()
        for selector in args.live:
            collection, name = selector.split(":", 1)
            payload = next(item for item in client.fetch_collection(collection) if item.get("name", "").casefold() == name.casefold())
            api_records.append({"collection": collection, "payload": payload})
    if not api_records:
        raise SystemExit("Provide --api-json or --live")
    cases = []
    requested = args.case or [f"{item['collection']}:{item['payload'].get('name')}" for item in api_records]
    for selector in requested:
        collection, name = selector.split(":", 1)
        cases.append(ComparisonCase(collection, name, str(args.xml), "api"))
    report = run(args.xml, api_records, cases)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(item["classification"] in {"equal", "source-only"} for item in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
