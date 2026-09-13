import json
from pathlib import Path
from types import SimpleNamespace

from application.entity_rendering import render_entity_html, render_entity_markdown


SNAPSHOT_PATH = Path(__file__).with_name("fixtures_entity_rendering.json")


def test_entity_rendering_snapshots_cover_all_supported_types():
    snapshots = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert set(snapshots) == {
        "item", "spell", "race", "class", "subclass", "monster",
        "feat", "background", "ability",
    }

    for entity_type, snapshot in snapshots.items():
        entity = SimpleNamespace(
            uid=f"snapshot-{entity_type}",
            name="Snapshot Entity",
            entity_type=entity_type,
            source_namespace="compendium",
            payload={"name": "Snapshot Entity", snapshot["field"]: "value"},
            source_metadata={},
        )
        markdown = render_entity_markdown(entity)
        html = render_entity_html(entity)
        assert f"dmtools-entity-uid: snapshot-{entity_type}" in markdown
        assert f"**{snapshot['field']}:** value" in markdown
        assert 'class="dmtools-inspection"' in html
        assert f'data-entity-uid="snapshot-{entity_type}"' in html
        assert "Snapshot Entity" in html
