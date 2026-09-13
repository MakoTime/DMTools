from tools.presentation_comparator import compare_presentations


def test_markdown_comparison_compares_structural_tokens():
    expected = "# Wizard\n\n**Spellcasting**\n\n| Level | Slots |\n| --- | --- |\n\n[Shield](dmtools://entity/shield)"
    actual = "# Wizard\n\n**Spellcasting**\n\n| Level | Features |\n| --- | --- |\n\n[Shield](dmtools://entity/shield)"

    differences = compare_presentations(expected, actual, "markdown")

    assert differences[0].path == "structure[2]"
    assert differences[0].severity == "error"


def test_html_comparison_preserves_table_and_link_structure():
    expected = "<h1>Wizard</h1><table><tr><th>Level</th></tr></table><a href='dmtools://entity/shield'>Shield</a>"
    actual = "<h1>Wizard</h1><table><tr><td>Level</td></tr></table><a href='dmtools://entity/shield'>Shield</a>"

    differences = compare_presentations(expected, actual, "html")

    assert any(d.expected == ("open", "th") for d in differences)


def test_compact_comparison_reports_stable_field_paths():
    differences = compare_presentations(
        {"name": "Wizard", "source": "PHB"},
        {"source": "PHB", "name": "Wizard"},
        "compact",
    )

    assert [difference.path for difference in differences] == ["structure[0]", "structure[1]"]
