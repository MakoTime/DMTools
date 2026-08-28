from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_registry(schema_root: Path) -> Registry:
    registry = Registry()

    for path in schema_root.rglob("*.schema.json"):
        schema = load_json(path)
        schema_id = schema.get("$id")

        if schema_id:
            registry = registry.with_resource(
                schema_id,
                Resource.from_contents(schema, default_specification=DRAFT7),
            )

    return registry


def validate(
    schema_path: Path,
    data: Path | dict,
    schema_root: Path,
) -> bool:
    schema = load_json(schema_path)
    if isinstance(data, Path):
        data = load_json(data)

    registry = build_registry(schema_root)

    validator = Draft7Validator(
        schema,
        registry=registry,
    )

    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: list(error.absolute_path),
    )
    msgs = []
    for error in errors:
        location = ".".join(
            str(part)
            for part in error.absolute_path
        )

        if not location:
            location = "<root>"

        print(f"  {location}: {error.message}")
        msgs.append(f"  {location}: {error.message}")
        
    if msgs:
        raise ValueError("Validation errors:\n" + "\n".join(msgs))

    return True


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python validate.py "
            "<schema-root> <schema.json> <data.json>"
        )
        return 1

    schema_root = Path(sys.argv[1]).resolve()
    schema_path = Path(sys.argv[2]).resolve()
    data_path = Path(sys.argv[3]).resolve()

    if not schema_root.is_dir():
        print(f"Schema directory not found: {schema_root}")
        return 1

    if not schema_path.is_file():
        print(f"Schema not found: {schema_path}")
        return 1

    if not data_path.is_file():
        print(f"Data file not found: {data_path}")
        return 1

    try:
        valid = validate(
            schema_path,
            data_path,
            schema_root,
        )
    except (OSError, json.JSONDecodeError) as error:
        print(f"Validation failed: {error}")
        return 1

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())