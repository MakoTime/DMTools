from PySide6.QtWidgets import QApplication, QMdiArea
from projectfoundry import ArtifactStore

from application.entity_queries import EntityQueryFactory
from application.entity_references import EntityReference
from application.homebrew import HomebrewDraft
from application.imports import EntityImportService
from application.project_controller import ProjectController
from dialog.entity_detail.controller import EntityInspectionController
from dialog.entity_query_results import create_entity_query_results


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def test_desktop_workflow_imports_queries_authors_navigates_and_reopens(tmp_path):
    QApplication.instance() or QApplication([])
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    project_file = controller.create_project(tmp_path / "campaign")
    record = EntityImportService().preview_xml(
        ITEM_XML, source_name="rules.xml"
    ).records[0]
    controller.commit_imported_entities((record,))

    database = controller.entity_database_store("compendium").block
    query = EntityQueryFactory().name_search(
        "item", database_uid=database.guid, value="pack"
    )
    controller.register_entity_query(query)
    collection = controller.create_collection("Travel Gear", dynamic_query_uid=query.guid)
    rows = controller.execute_entity_query(query.guid)
    opened = []
    results = create_entity_query_results(
        rows,
        project_controller=controller,
        collection_uid=collection.guid,
        on_open=opened.append,
    )
    results.table.selectRow(0)
    assert results.add_selected_to_collection() is True
    assert results.open_selected_entity().uid == record.uid
    assert [entity.uid for entity in opened] == [record.uid]

    homebrew = results.clone_selected_to_homebrew()
    draft = HomebrewDraft.for_edit(homebrew)
    draft.name = "Travel Pack"
    controller.update_homebrew_entity(homebrew.uid, draft)

    mdi_area = QMdiArea()
    inspection = EntityInspectionController(controller, mdi_area)
    reference = EntityReference(record.uid, record.entity_type, "compendium")
    first_view = inspection.open(reference)
    assert inspection.open(reference) is first_view
    assert len(inspection._windows) == 1

    project_file = controller.save_project()
    reopened = ProjectController()
    reopened.load_project(project_file)
    assert reopened.resolve_entity(homebrew.uid).name == "Travel Pack"
    assert [row.uid for row in reopened.resolve_collection_members(collection.guid)] == [
        record.uid
    ]
    assert reopened.project.blocks.contains(collection.guid)
    assert reopened.project.nodes.get(
        f"dmtools-compendium-entity-{record.uid}"
    ).entity_uid == record.uid
    assert reopened.project.nodes.get(
        f"dmtools-homebrew-entity-{homebrew.uid}"
    ).entity_uid == homebrew.uid
    assert reopened.entity_database_store("compendium").get(record.uid).uid == record.uid

    mdi_area.closeAllSubWindows()
    controller.close()
    reopened.close()
    assert not inspection._windows
