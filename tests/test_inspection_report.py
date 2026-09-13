from types import SimpleNamespace

from tools.inspection_report import review_record


def test_review_record_reports_actionable_presentation_issues():
    record = SimpleNamespace(
        uid="compendium:class:bard",
        entity_type="class",
        name="Bard",
        source_namespace="compendium",
        payload={
            "name": "Bard",
            "spellcasting": {"ability": "charisma", "progression": "full"},
            "features": [{
                "name": "Starting Bard",
                "description": "Starting BardAs a 1st-level Bard.",
                "level": 1,
                "source": {"text": "Player's Handbook p. 51"},
            }],
            "tool_proficiencies": ["three_musical_instruments_of_your_choice"],
        },
        source_metadata={},
    )

    issues = review_record(record)
    issue_codes = {issue["code"] for issue in issues}

    assert issue_codes == {"adjacent-metadata", "missing-cantrip-progression"}


def test_review_record_ignores_separated_source_labels_and_nested_mappings():
    record = SimpleNamespace(
        uid="monster-1",
        entity_type="monster",
        name="Acolyte",
        source_namespace="compendium",
        payload={
            "name": "Acolyte",
            "features": [{
                "name": "Spellcasting",
                "description": "A spell feature.",
                "source": {"text": "Player's Handbook p. 58"},
            }],
            "actions": [{
                "name": "Club",
                "description": "Melee Weapon Attack.",
                "attack": {"type": "melee_weapon", "bonus": 2},
            }],
        },
        source_metadata={},
    )

    codes = {issue["code"] for issue in review_record(record)}

    assert codes == set()
