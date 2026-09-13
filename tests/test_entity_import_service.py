import pytest

from application.imports import EntityImportService


VALID_ITEM_XML = """
<compendium>
    <item>
        <name>Backpack</name><type>G</type><weight>5</weight><value>2</value>
    </item>
</compendium>
"""


def test_xml_preview_normalizes_records_and_preserves_failures():
    service = EntityImportService()
    preview = service.preview_xml(
        """
        <compendium>
            <spell><name>Broken Spell</name><level>not-a-level</level></spell>
            <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
            <unknown><name>Future Entity</name></unknown>
        </compendium>
        """,
        source_name="sample.xml",
    )

    assert [record.display_name for record in preview.records] == ["Backpack"]
    assert preview.records[0].entity_type == "item"
    assert preview.records[0].validation_status == "valid"
    assert preview.records[0].provenance == "sample.xml"
    assert [issue.status for issue in preview.issues] == ["failed", "unsupported"]
    assert preview.issues[0].source_location == "sample.xml record 1"
    assert preview.can_commit is False


def test_json_preview_accepts_canonical_records_and_raw_entities():
    service = EntityImportService()
    item = service.preview_xml(VALID_ITEM_XML, source_name="source.xml").records[0]

    canonical = service.preview_json(
        {
            "records": [
                {
                    "entity_type": "item",
                    "source_identity": "book:item:backpack",
                    "display_name": "Backpack",
                    "payload": item.payload,
                    "source_metadata": {"book": "Rules"},
                }
            ]
        },
        source_name="entities.json",
    )
    raw = service.preview_json(
        {"type": "item", **item.payload},
        source_name="raw.json",
    )

    assert canonical.can_commit is True
    assert canonical.records[0].source_metadata == {"book": "Rules"}
    assert raw.can_commit is True
    assert raw.records[0].display_name == "Backpack"


def test_json_preview_rejects_unknown_and_malformed_records():
    preview = EntityImportService().preview_json(
        [
            {"entity_type": "future", "name": "Unknown"},
            "not an object",
        ],
        source_name="invalid.json",
    )

    assert preview.records == ()
    assert len(preview.issues) == 2
    assert all(issue.status == "failed" for issue in preview.issues)
    assert "Unsupported entity type" in preview.issues[0].error
    assert "must be an object" in preview.issues[1].error


def test_import_uid_is_stable_for_repeated_source_identity():
    service = EntityImportService()

    first = service.preview_xml(VALID_ITEM_XML, source_name="rules.xml").records[0]
    second = service.preview_xml(VALID_ITEM_XML, source_name="rules.xml").records[0]

    assert first.source_identity == second.source_identity
    assert first.uid == second.uid


def test_duplicate_policies_reject_skip_and_replace():
    service = EntityImportService()
    item = service.preview_xml(VALID_ITEM_XML, source_name="source.xml").records[0]
    records = [
        {
            "entity_type": "item",
            "source_identity": "same-item",
            "payload": item.payload,
        },
        {
            "entity_type": "item",
            "source_identity": "same-item",
            "payload": {**item.payload, "name": "Replacement Backpack"},
        },
    ]

    rejected = service.preview_json(records, duplicate_policy="reject")
    skipped = service.preview_json(records, duplicate_policy="skip")
    replaced = service.preview_json(records, duplicate_policy="replace")

    assert rejected.can_commit is False
    assert rejected.issues[0].status == "duplicate"
    assert skipped.can_commit is True
    assert skipped.issues[0].status == "skipped"
    assert replaced.can_commit is True
    assert replaced.records[0].display_name == "Replacement Backpack"


def test_import_result_counts_distinguish_all_outcomes():
    service = EntityImportService()
    item = service.preview_xml(VALID_ITEM_XML, source_name="source.xml").records[0]
    updated = service.preview_json(
        {"entity_type": "item", "source_identity": "existing", "payload": item.payload},
        duplicate_policy="replace",
        existing_source_identities={"existing"},
    )
    invalid = service.preview_json(
        [
            {"entity_type": "future", "name": "Unknown"},
            "not an object",
        ]
    )
    skipped = service.preview_json(
        {"entity_type": "item", "source_identity": "existing", "payload": item.payload},
        duplicate_policy="skip",
        existing_source_identities={"existing"},
    )

    assert updated.result_counts == {
        "created": 0,
        "updated": 1,
        "skipped": 0,
        "duplicate": 0,
        "invalid": 0,
        "unsupported": 0,
    }
    assert invalid.result_counts["invalid"] == 2
    assert skipped.result_counts["skipped"] == 1


def test_cancellation_discards_prepared_records_and_reports_progress():
    calls = []
    cancel_checks = iter((False, True))
    service = EntityImportService()
    item = service.preview_xml(VALID_ITEM_XML, source_name="source.xml").records[0]

    preview = service.preview_json(
        [
            {"entity_type": "item", "payload": item.payload},
            {"entity_type": "item", "payload": item.payload},
        ],
        is_cancelled=lambda: next(cancel_checks),
        progress_callback=lambda current, total: calls.append((current, total)),
    )

    assert preview.cancelled is True
    assert preview.records == ()
    assert preview.can_commit is False
    assert calls == [(0, 2)]


def test_commit_publishes_valid_batch_once_and_blocks_invalid_preview():
    service = EntityImportService()
    valid = service.preview_xml(VALID_ITEM_XML, source_name="source.xml")
    invalid = service.preview_json({"entity_type": "unknown", "name": "Future"})
    committed = []

    result = service.commit(valid, lambda records: committed.append(records) or "done")

    assert result == "done"
    assert committed == [valid.records]
    with pytest.raises(ValueError, match="blocking issues"):
        service.commit(invalid, lambda records: committed.append(records))
    assert committed == [valid.records]


def test_commit_can_explicitly_skip_invalid_records_in_a_mixed_batch():
    service = EntityImportService()
    item = service.preview_xml(VALID_ITEM_XML).records[0]
    preview = service.preview_json(
        [
            {"entity_type": "item", "payload": item.payload},
            {"entity_type": "unknown", "name": "Future"},
        ]
    )
    committed = []

    assert preview.can_commit is False
    assert len(preview.records) == 1
    assert preview.result_counts["invalid"] == 1
    with pytest.raises(ValueError, match="blocking issues"):
        service.commit(preview, committed.append)

    service.commit(preview, committed.append, skip_invalid=True)

    assert committed == [preview.records]


def test_import_reports_file_phases_before_record_validation():
    statuses = []
    progress = []

    EntityImportService().preview_xml(
        VALID_ITEM_XML,
        status_callback=statuses.append,
        progress_callback=lambda current, total: progress.append((current, total)),
    )

    assert statuses == [
        "Reading and parsing XML structure",
        "Parsing source entities",
        "Validating normalized records",
    ]
    assert progress == [(0, 1), (1, 1), (0, 1), (1, 1)]