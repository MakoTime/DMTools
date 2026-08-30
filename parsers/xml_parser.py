from __future__ import annotations

from pathlib import Path
from typing import IO
from xml.etree import ElementTree as ET


XmlSource = str | Path | IO[str]


def parse_xml(source: XmlSource) -> dict:
    """
    Parse XML content into a normalized dictionary representation.

    `source` may be:
        - an XML string
        - a filesystem path
        - an open text file
    """
    if isinstance(source, Path):
        root = ET.parse(source).getroot()
    elif isinstance(source, str):
        if "<" in source:
            root = ET.fromstring(source)
        else:
            root = ET.parse(source).getroot()
    else:
        root = ET.parse(source).getroot()

    return _parse_element(root)


def _parse_element(element: ET.Element) -> dict:
    """
    Convert an XML element into the normalized intermediate representation.
    """
    return {
        "tag": element.tag,
        "attributes": dict(element.attrib),
        "text": _clean_text(element.text),
        "children": [_parse_element(child) for child in element],
    }


def _clean_text(text: str | None) -> str | None:
    """
    Remove insignificant XML formatting whitespace.

    Empty or whitespace-only elements are represented as None.
    """
    if text is None:
        return None

    text = text.strip()

    return text or None


def find_child(element: dict, tag: str) -> dict | None:
    """
    Return the first direct child with the given tag.

    Returns None if no matching child exists.
    """
    for child in element["children"]:
        if child["tag"] == tag:
            return child

    return None


def find_children(element: dict, tag: str) -> list[dict]:
    """
    Return all direct children with the given tag.
    """
    return [
        child
        for child in element["children"]
        if child["tag"] == tag
    ]


def get_text(element: dict, tag: str) -> str | None:
    """
    Return the text of the first direct child with the given tag.

    Returns None if the child does not exist or has no text.
    """
    child = find_child(element, tag)

    if child is None:
        return None

    return child["text"]
