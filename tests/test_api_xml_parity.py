from tools.api_xml_parity import ComparisonCase, classify, compare, run


def test_parity_report_validates_models_and_classifies_shared_values():
    xml_payload = {
        "name": "Backpack",
        "category": "adventuring_gear",
        "weight": 5,
        "cost": {"amount": 2, "currency": "gp"},
    }
    api_payload = {**xml_payload, "description": "A leather pack."}

    report = compare(
        xml_payload,
        api_payload,
        "item",
        xml_source="fixture.xml",
        api_source="fixture.json",
    )

    fields = {item["canonical_field"]: item for item in report}
    assert fields["name"]["classification"] == "equal"
    assert fields["description"]["classification"] == "source-only"
    assert fields["category"]["model"] == "Item"
    assert fields["category"]["schema"] == "Item.schema.json"


def test_classify_distinguishes_shape_and_normalization_differences():
    assert classify("Medium", "medium") == "normalization-mismatch"
    assert classify({"amount": 2}, 2) == "shape-mismatch"
    assert classify("present in XML", None) == "missing"
    assert classify("hydrated feature", None, api_path="class_levels[].features[]") == "hydration-mismatch"


def test_run_uses_real_xml_dispatch_and_api_import_validation(tmp_path):
    xml_path = tmp_path / "items.xml"
    xml_path.write_text(
        "<compendium><item><name>Backpack</name><type>G</type>"
        "<weight>5</weight><value>2</value></item></compendium>",
        encoding="utf-8",
    )
    report = run(
        xml_path,
        [{
            "collection": "equipment",
            "payload": {
                "name": "Backpack",
                "equipment_category": {"name": "Adventuring Gear"},
                "weight": 5,
                "cost": {"quantity": 2, "unit": "gp"},
                "desc": [],
            },
        }],
        [ComparisonCase("equipment", "Backpack", str(xml_path), "fixture.json")],
    )

    assert {item["classification"] for item in report} == {"equal"}
    assert all(item["xml_field"].startswith("payload.") for item in report)
    assert all(item["api_field"].startswith("payload.") for item in report)