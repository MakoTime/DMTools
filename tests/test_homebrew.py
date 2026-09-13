import pytest
from projectfoundry import ArtifactStore
from PySide6.QtWidgets import QApplication

from application.homebrew import HomebrewDraft
from application.imports import EntityImportService
from application.project_controller import ProjectController
from dialog.homebrew import (
    create_homebrew_dialog,
    create_homebrew_editor_model,
    create_homebrew_mdi_view,
)


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def qt_app():
    return QApplication.instance() or QApplication([])


def controller_with_item(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    record = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    controller.commit_imported_entities((record,))
    return controller, record


def test_invalid_homebrew_draft_rolls_back_without_storage(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    draft = HomebrewDraft(entity_type="item", name="", payload={})

    with pytest.raises(ValueError, match="name is required"):
        controller.create_homebrew_entity(draft)

    assert not controller.project.blocks.contains("dmtools-homebrew-entity-database")
    assert not (tmp_path / "data" / "homebrew.sqlite").exists()


def test_compendium_copy_creates_separate_homebrew_entity_and_node(tmp_path):
    controller, source_record = controller_with_item(tmp_path)

    copied = controller.copy_entity_to_homebrew(source_record.uid)

    assert copied.uid != source_record.uid
    assert copied.source_namespace == "homebrew"
    assert copied.payload == source_record.payload
    assert controller.resolve_entity(source_record.uid).source_namespace == "compendium"
    store = controller.entity_database_store("homebrew")
    with store.connect() as connection:
        metadata = connection.execute(
            "SELECT source_metadata FROM entities WHERE uid = ?", (copied.uid,)
        ).fetchone()[0]
    assert source_record.uid in metadata
    node = controller.project.nodes.get(f"dmtools-homebrew-entity-{copied.uid}")
    assert node.parent_uid == "dmtools-homebrew-item-category"


def test_homebrew_copy_rejects_homebrew_source(tmp_path):
    controller, source_record = controller_with_item(tmp_path)
    copied = controller.copy_entity_to_homebrew(source_record.uid)

    with pytest.raises(ValueError, match="Only Compendium"):
        controller.copy_entity_to_homebrew(copied.uid)


def test_homebrew_metadata_validation_and_reopen(tmp_path):
    controller, source_record = controller_with_item(tmp_path)
    source = controller.resolve_entity(source_record.uid)
    draft = HomebrewDraft.from_entity(source)
    draft.name = "Expedition Pack"
    draft.version = 2
    draft.draft_state = "published"
    draft.published = True

    created = controller.create_homebrew_entity(draft)

    reopened = controller.entity_database_store("homebrew")
    restored = reopened.get(created.uid)
    assert restored.name == "Expedition Pack"
    assert restored.payload["name"] == "Expedition Pack"

    draft.version = 0
    with pytest.raises(ValueError, match="version must be at least 1"):
        draft.apply()


def test_adaptive_editor_model_selection_and_cancel_isolation():
    qt_app()
    draft = HomebrewDraft(
        entity_type="item",
        name="Field Kit",
        payload={"name": "Field Kit", "type": "G", "weight": 1, "value": 3},
    )

    model = create_homebrew_editor_model("Item", draft)
    dialog = create_homebrew_dialog("item", draft)
    dialog.name_edit.setText("Changed")
    dialog.reject_editor()

    assert model.entity_type == "item"
    assert dialog.model.name == "Field Kit"
    assert draft.name == "Field Kit"
    with pytest.raises(ValueError, match="does not match"):
        create_homebrew_editor_model("spell", draft)


def test_adaptive_editor_surfaces_registry_validation():
    qt_app()
    dialog = create_homebrew_dialog("item")
    dialog.name_edit.setText("Invalid Item")
    dialog.payload_edit.setPlainText("{")

    assert dialog.apply_changes() is None
    assert "name" in dialog.error_label.text()
    assert dialog.error_label.text()


def test_adaptive_editor_builds_schema_controls_for_scalar_fields():
    qt_app()
    dialog = create_homebrew_dialog("item")

    assert "category" in dialog.field_widgets
    assert dialog.field_widgets["category"].findText("wand") >= 0
    assert "weight" in dialog.field_widgets
    dialog.name_edit.setText("Wand")
    dialog.field_widgets["category"].setCurrentText("wand")
    dialog.field_widgets["weight"].setValue(2)
    dialog.payload_edit.setPlainText("{}")

    result = dialog.apply_changes()

    assert result is not None
    assert result.payload["category"] == "wand"
    assert result.payload["weight"] == 2


def test_adaptive_editor_builds_repeatable_controls_for_scalar_lists():
    qt_app()
    dialog = create_homebrew_dialog("spell")

    assert "components" in dialog.field_widgets
    components = dialog.field_widgets["components"][0]
    components.addItem("verbal")
    dialog.name_edit.setText("Signal")
    dialog.payload_edit.setPlainText(
        '{"description": "A signal", "level": 0, '
        '"casting_time": {"unit": "action"}, '
        '"duration": {"duration": "instantaneous"}}'
    )

    result = dialog.apply_changes()

    assert result is not None
    assert result.payload["components"] == ["verbal"]


def test_adaptive_editor_builds_repeatable_controls_for_structured_lists():
    qt_app()
    dialog = create_homebrew_dialog("item")

    assert "features" in dialog.field_widgets
    features, detail = dialog.field_widgets["features"]
    features.addItem("{}")
    features.setCurrentRow(0)
    detail.setPlainText('{"name": "Arcane Edge", "description": "A feature"}')
    dialog.name_edit.setText("Wand")
    dialog.payload_edit.setPlainText("{}")

    result = dialog.apply_changes()

    assert result is not None
    assert result.payload["features"][0]["name"] == "Arcane Edge"


def test_modeless_homebrew_editor_keeps_draft_temporary_until_valid_accept():
    qt_app()
    payload = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0].payload
    draft = HomebrewDraft(
        entity_type="item",
        name="Field Kit",
        payload={**payload, "name": "Field Kit"},
    )
    accepted = []
    view = create_homebrew_mdi_view("item", draft, on_accept=accepted.append)

    view.name_edit.setText("")
    assert view.apply_changes() is None
    assert accepted == []
    assert draft.name == "Field Kit"

    view.name_edit.setText("Travel Kit")
    assert view.apply_changes() is not None
    assert accepted[0].name == "Travel Kit"
    assert accepted[0] is view.model


def test_modeless_homebrew_editor_cancel_releases_owner_callback():
    qt_app()
    draft = HomebrewDraft(
        entity_type="item",
        name="Field Kit",
        payload={"name": "Field Kit", "type": "G", "weight": 1, "value": 3},
    )
    closed = []
    view = create_homebrew_mdi_view("item", draft, parent=None)
    view._on_close = lambda model, reason: closed.append((model, reason))

    view.close()

    assert closed[0][1] == "window"
    assert closed[0][0].name == draft.name
    assert view.on_accept is None
    assert view.model is None


def test_homebrew_edit_duplicate_and_delete_are_project_routed(tmp_path):
    controller, source_record = controller_with_item(tmp_path)
    created = controller.copy_entity_to_homebrew(source_record.uid)
    edit = HomebrewDraft.for_edit(created)
    edit.name = "Trail Pack"
    edit.version += 1

    updated = controller.update_homebrew_entity(created.uid, edit)
    duplicate = controller.duplicate_homebrew_entity(updated.uid)

    assert updated.uid == created.uid
    assert updated.name == "Trail Pack"
    assert updated.source_metadata["version"] == 2
    assert duplicate.uid != updated.uid
    assert duplicate.name == "Trail Pack Copy"
    assert duplicate.source_metadata["source_entity_uid"] == updated.uid
    assert controller.project.nodes.get(
        f"dmtools-homebrew-entity-{updated.uid}"
    ).name == "Trail Pack"

    controller.delete_homebrew_entity(updated.uid)

    with pytest.raises(ValueError, match="Unknown active-project entity UID"):
        controller.resolve_entity(updated.uid)
    assert controller.resolve_entity(duplicate.uid).name == "Trail Pack Copy"
    assert not controller.project.nodes.contains(
        f"dmtools-homebrew-entity-{updated.uid}"
    )


def test_invalid_homebrew_edit_preserves_last_valid_entity(tmp_path):
    controller, source_record = controller_with_item(tmp_path)
    created = controller.copy_entity_to_homebrew(source_record.uid)
    draft = HomebrewDraft.for_edit(created)
    draft.name = ""

    with pytest.raises(ValueError, match="name is required"):
        controller.update_homebrew_entity(created.uid, draft)

    restored = controller.resolve_entity(created.uid)
    assert restored.name == created.name
    assert restored.payload == created.payload


def test_homebrew_workflow_round_trips_without_mutating_compendium_source(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    project_file = controller.create_project(tmp_path / "campaign")
    source_record = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    controller.commit_imported_entities((source_record,))
    source_before = controller.resolve_entity(source_record.uid)

    homebrew = controller.copy_entity_to_homebrew(source_record.uid)
    invalid = HomebrewDraft.for_edit(homebrew)
    invalid.name = ""
    with pytest.raises(ValueError, match="name is required"):
        controller.update_homebrew_entity(homebrew.uid, invalid)
    assert controller.resolve_entity(source_record.uid).payload == source_before.payload

    cancelled = HomebrewDraft.for_edit(homebrew)
    cancelled.name = "Cancelled Name"
    del cancelled

    accepted = HomebrewDraft.for_edit(homebrew)
    accepted.name = "Travel Pack"
    updated = controller.update_homebrew_entity(homebrew.uid, accepted)
    controller.save_project()

    reopened = ProjectController()
    reopened.load_project(project_file)

    assert reopened.resolve_entity(source_record.uid).name == source_before.name
    assert reopened.resolve_entity(source_record.uid).payload == source_before.payload
    assert reopened.resolve_entity(updated.uid).name == "Travel Pack"

    controller.close()
    reopened.close()