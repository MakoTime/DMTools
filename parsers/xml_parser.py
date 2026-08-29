from xml.etree import ElementTree as ET


def parse_xml(source):
    """
    Parse XML content from a file or string into a generic tree structure.
    Handles both file paths and in-memory XML strings.
    """
    if isinstance(source, str):
        root = ET.fromstring(source)
    else:
        root = ET.parse(source).getroot()

    def parse_element(element):
        text = element.text.strip() if element.text else None

        return {
            "tag": element.tag,
            "attributes": element.attrib.copy(),
            "text": text,
            "children": [
                parse_element(child)
                for child in element
            ],
        }

    return parse_element(root)

def find_children(element, tag):
    """
    Return all direct children with the given tag.
    """
    return [
        child
        for child in element["children"]
        if child["tag"] == tag
    ]


def find_child(element, tag):
    """
    Return the first direct child with the given tag.
    """
    for child in element["children"]:
        if child["tag"] == tag:
            return child

    return None


def get_text(element, tag):
    """
    Return the text of the first direct child with the given tag.
    """
    child = find_child(element, tag)

    if child is None:
        return None

    return child["text"]