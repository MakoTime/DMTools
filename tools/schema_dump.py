from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urldefrag


SCHEMA_ROOT = Path(__file__).resolve().parent.parent / "schemas"
OUTPUT_ROOT = SCHEMA_ROOT / "bundled"


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_ref(ref: str, current_file: Path) -> tuple[Path, str]:
    file_ref, fragment = urldefrag(ref)

    if not file_ref:
        return current_file, fragment

    return (current_file.parent / file_ref).resolve(), fragment


def get_fragment(document: dict, fragment: str):
    if not fragment:
        return document

    if not fragment.startswith("/"):
        raise ValueError(f"Unsupported JSON pointer: #{fragment}")

    value = document

    for part in fragment[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[part]

    return value


def collect_refs(value, current_file: Path, definitions: dict):
    if isinstance(value, dict):
        ref = value.get("$ref")

        if ref:
            target_file, fragment = resolve_ref(ref, current_file)
            target_document = load_schema(target_file)
            target = get_fragment(target_document, fragment)

            definition_name = target_file.stem.replace(".schema", "")

            if definition_name not in definitions:
                definitions[definition_name] = None
                collect_refs(target, target_file, definitions)
                definitions[definition_name] = target

            value.clear()
            value["$ref"] = f"#/$defs/{definition_name}"
            return

        for child in value.values():
            collect_refs(child, current_file, definitions)

    elif isinstance(value, list):
        for child in value:
            collect_refs(child, current_file, definitions)


def dump_schema(schema_path: Path, output_path: Path) -> None:
    schema_path = schema_path.resolve()
    schema = load_schema(schema_path)

    definitions: dict[str, dict | None] = {}

    collect_refs(schema, schema_path, definitions)

    schema["$defs"] = {
        name: definition
        for name, definition in definitions.items()
        if definition is not None
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(schema, file, indent=4, ensure_ascii=False)
        file.write("\n")


def resolve_input(value: str) -> Path:
    path = Path(value)

    if path.exists():
        return path

    entity_path = SCHEMA_ROOT / f"{value}.schema.json"

    if entity_path.exists():
        return entity_path

    raise FileNotFoundError(f"Could not find schema or entity: {value}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python tools/schema_dump.py <schema | entity>")
        print()
        print("Examples:")
        print("  python tools/schema_dump.py Monster")
        print("  python tools/schema_dump.py schemas/entities/Monster.schema.json")
        raise SystemExit(1)

    schema_path = resolve_input(sys.argv[1])
    output_path = OUTPUT_ROOT / schema_path.name

    dump_schema(schema_path, output_path)

    print(f"Schema written to: {output_path}")


if __name__ == "__main__":
    main()