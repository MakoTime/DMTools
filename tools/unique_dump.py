from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from parsers.xml_parser import parse_xml


EXCLUDED_FIELDS = {"name", "text"}


def get_unique_fields(data):
    fields = defaultdict(set)

    def walk(node, section, path):
        for child in node.get("children", []):
            tag = child["tag"]

            if tag in EXCLUDED_FIELDS:
                continue

            child_path = path + (tag,)
            fields[section].add(child_path)

            walk(child, section, child_path)

    if isinstance(data, dict):
        data = [data]

    for root in data:
        if root.get("tag") == "compendium":
            sections = root.get("children", [])
        else:
            sections = [root]

        for section in sections:
            walk(section, section["tag"], ())

    return {
        section: sorted(
            " → ".join(path)
            for path in paths
        )
        for section, paths in fields.items()
    }


def get_unique_values(data):
    values = defaultdict(set)

    def walk(node, section, path):
        tag = node.get("tag")

        if tag in EXCLUDED_FIELDS:
            return

        text = node.get("text")

        if text is not None and text != "":
            values[section].add(
                (" → ".join(path), text)
            )

        for child in node.get("children", []):
            child_tag = child["tag"]

            if child_tag in EXCLUDED_FIELDS:
                continue

            child_path = path + (child_tag,)
            walk(child, section, child_path)

    if isinstance(data, dict):
        data = [data]

    for root in data:
        if root.get("tag") == "compendium":
            sections = root.get("children", [])
        else:
            sections = [root]

        for section in sections:
            walk(section, section["tag"], ())

    result = defaultdict(set)

    for section, path_values in values.items():
        for path, value in path_values:
            result[section].add((path, value))

    return {
        section: {
            path: sorted(
                value
                for value_path, value in path_values
                if value_path == path
            )
            for path in sorted(
                {path for path, _ in path_values}
            )
        }
        for section, path_values in result.items()
    }


def main(xml_path):
    data = parse_xml(xml_path)

    fields = get_unique_fields(data)
    values = get_unique_values(data)

    output_path = Path(__file__).with_name("unique_fields.json")

    output = {
        "fields": fields,
        "values": values,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main(
        r"C:\Users\benve\Documents\Programming\DMTools\5eFile.xml"
    )