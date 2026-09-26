import json
from threading import Event, get_ident
from types import SimpleNamespace

from projectfoundry import ArtifactStore, QtTaskRunner, Task, TaskRunner
from PySide6.QtCore import QModelIndex, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMainWindow,
    QProgressBar,
)

from application.controllers.import_controller import EntityImportController
from application.imports import EntityImportService, ImportPreview
from application.project_controller import ProjectController
from dialog.base.popup_editor import PopupEditorView
from dialog.import_progress.factory import create_import_progress
from dialog.import_progress.view import ImportProgressView
from dialog.import_preview.factory import create_import_preview
from menu import setup_menu


ITEM_XML = """
<compendium>
    <item><name>Backpack</name><type>G</type><weight>5</weight><value>2</value></item>
</compendium>
"""


def qt_app():
    return QApplication.instance() or QApplication([])


class PreviewDialog:
    def __init__(self, preview, result, *, skip_invalid=False):
        self.model = SimpleNamespace(
            preview=preview,
            destination="compendium",
            duplicate_policy="replace",
            skip_invalid=skip_invalid,
        )
        self.result = result

    def exec(self):
        return self.result


class FakeSrdClient:
    def __init__(self, resources_by_collection):
        self.resources_by_collection = resources_by_collection

    def fetch_collection_resources(
        self,
        collection,
        *,
        query=None,
        is_cancelled=None,
        progress_callback=None,
    ):
        del query
        resources = self.resources_by_collection[collection]
        if progress_callback is not None:
            progress_callback(len(resources), len(resources))
        if is_cancelled is not None and is_cancelled():
            return []
        return resources


def project_controller(tmp_path):
    controller = ProjectController(artifact_store=ArtifactStore(tmp_path))
    controller.project_file = tmp_path / "project.json"
    return controller


def tree_model_names(model, parent=None):
    parent = QModelIndex() if parent is None else parent
    names = []
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        names.append(model.data(index))
        names.extend(tree_model_names(model, index))
    return names


def test_import_file_selection_cancel_does_not_mutate_project(tmp_path):
    controller = project_controller(tmp_path)

    import_controller = EntityImportController(
        controller,
        file_chooser=lambda source_format: "",
        error_reporter=lambda message: None,
    )

    assert import_controller.import_xml() is None
    assert not controller.project.blocks.contains(
        "dmtools-compendium-entity-database"
    )
    assert not (tmp_path / "data" / "compendium.sqlite").exists()


def test_menu_exposes_normalise_references_action():
    qt_app()
    window = QMainWindow()
    window.menuFile = window.menuBar().addMenu("File")
    window.menuEdit = window.menuBar().addMenu("Edit")
    calls = []
    controller = SimpleNamespace(
        normalize_entity_references=lambda **kwargs: calls.append("normalise")
    )

    actions = setup_menu(window, project_controller=controller)

    assert actions["normalize_references"].text() == "Normalise References"
    actions["normalize_references"].trigger()
    assert calls == ["normalise"]


def test_accepted_xml_import_commits_and_registers_category_node(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    source = tmp_path / "items.xml"
    source.write_text(ITEM_XML, encoding="utf-8")
    import_controller = EntityImportController(
        controller,
        file_chooser=lambda source_format: source,
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview, QDialog.DialogCode.Accepted
        ),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_xml() == 1
    store = controller.entity_database_store("compendium")
    row = store.query("item", value="Backpack")[0]
    entity_node = controller.project.nodes.get(
        f"dmtools-compendium-entity-{row.uid}"
    )
    assert entity_node.parent_uid == "dmtools-compendium-item-category"
    assert entity_node.entity_uid == row.uid
    compendium_data = json.loads(
        (tmp_path / "data" / "compendium.json").read_text(encoding="utf-8")
    )
    assert any(
        record["payload"].get("name") == "Backpack"
        for record in compendium_data.values()
    )
    manifest = json.loads(
        (tmp_path / "project.json").read_text(encoding="utf-8")
    )
    assert manifest["data_files"]["compendium"] == "data/compendium.json"


def test_api_import_reaches_persistence_and_project_save(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    resources = {
        "equipment": [{
            "collection": "equipment",
            "payload": {
                "index": "handaxe",
                "name": "Handaxe",
                "equipment_category": {"name": "Weapon"},
                "weapon_category": "Simple",
                "weapon_range": "Melee",
                "damage": {
                    "damage_dice": "1d6",
                    "damage_type": {"name": "Slashing"},
                },
                "range": {"normal": 5},
                "cost": {"quantity": 5, "unit": "gp"},
                "weight": 2,
                "url": "/api/2014/equipment/handaxe",
            },
            "parent": None,
        }]
    }
    import_controller = EntityImportController(
        controller,
        srd_client=FakeSrdClient(resources),
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview, QDialog.DialogCode.Accepted
        ),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_srd_collection("equipment") == 1

    row = controller.entity_database_store("compendium").query(
        "item", value="Handaxe"
    )[0]
    assert controller.project.nodes.contains(
        f"dmtools-compendium-entity-{row.uid}"
    )
    assert "Handaxe" in tree_model_names(controller.project_tree_model)
    compendium_data = json.loads(
        (tmp_path / "data" / "compendium.json").read_text(encoding="utf-8")
    )
    assert compendium_data[row.uid]["payload"]["name"] == "Handaxe"
    manifest = json.loads((tmp_path / "project.json").read_text(encoding="utf-8"))
    assert manifest["data_files"]["compendium"] == "data/compendium.json"


def test_api_import_reaches_commit_for_multiple_collections(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    resources = {
        "equipment": [{
            "collection": "equipment",
            "payload": {
                "index": "rope",
                "name": "Rope",
                "equipment_category": {"name": "Adventuring Gear"},
                "desc": ["A length of rope."],
                "cost": {"quantity": 1, "unit": "gp"},
                "weight": 10,
                "url": "/api/2014/equipment/rope",
            },
            "parent": None,
        }],
        "backgrounds": [{
            "collection": "backgrounds",
            "payload": {
                "index": "acolyte",
                "name": "Acolyte",
                "desc": ["You have spent your life in service."],
                "starting_proficiencies": [],
                "url": "/api/2014/backgrounds/acolyte",
            },
            "parent": None,
        }],
    }
    import_controller = EntityImportController(
        controller,
        srd_client=FakeSrdClient(resources),
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview, QDialog.DialogCode.Accepted
        ),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_srd(
        collections=("equipment", "backgrounds")
    ) == 2

    store = controller.entity_database_store("compendium")
    assert [row.name for row in store.query("item", operator="all")] == ["Rope"]
    assert [row.name for row in store.query("background", operator="all")] == [
        "Acolyte"
    ]
    assert all(
        controller.project.nodes.contains(f"dmtools-compendium-entity-{row.uid}")
        for entity_type in ("item", "background")
        for row in store.query(entity_type, operator="all")
    )
    tree_names = tree_model_names(controller.project_tree_model)
    assert "Rope" in tree_names
    assert "Acolyte" in tree_names


def test_preview_rejection_does_not_create_entity_database(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    source = tmp_path / "items.xml"
    source.write_text(ITEM_XML, encoding="utf-8")
    import_controller = EntityImportController(
        controller,
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview, QDialog.DialogCode.Rejected
        ),
        error_reporter=lambda message: None,
    )

    assert import_controller.import_source(source, "xml") is None
    assert not controller.project.blocks.contains(
        "dmtools-compendium-entity-database"
    )


def test_accepted_skip_import_commits_valid_records_from_mixed_batch(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    item = EntityImportService().preview_xml(ITEM_XML).records[0]
    source = tmp_path / "mixed.json"
    source.write_text(
        json.dumps(
            [
                {"entity_type": "item", "payload": item.payload},
                {"entity_type": "unknown", "name": "Future"},
            ]
        ),
        encoding="utf-8",
    )
    import_controller = EntityImportController(
        controller,
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview,
            QDialog.DialogCode.Accepted,
            skip_invalid=True,
        ),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_source(source, "json") == 1
    rows = controller.entity_database_store("compendium").query(
        "item", operator="all"
    )
    assert [row.name for row in rows] == ["Backpack"]


def test_preview_runs_on_worker_and_commit_runs_on_gui_thread(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    source = tmp_path / "items.xml"
    source.write_text(ITEM_XML, encoding="utf-8")
    gui_thread_id = get_ident()
    preview_thread_ids = []
    commit_thread_ids = []

    class TrackingService(EntityImportService):
        def preview_xml(self, *args, **kwargs):
            preview_thread_ids.append(get_ident())
            return super().preview_xml(*args, **kwargs)

    commit = controller.commit_imported_entities

    def tracked_commit(*args, **kwargs):
        commit_thread_ids.append(get_ident())
        return commit(*args, **kwargs)

    controller.commit_imported_entities = tracked_commit
    import_controller = EntityImportController(
        controller,
        service=TrackingService(),
        preview_factory=lambda preview, **kwargs: PreviewDialog(
            preview, QDialog.DialogCode.Accepted
        ),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_source(source, "xml") == 1
    assert preview_thread_ids
    assert preview_thread_ids[0] != gui_thread_id
    assert commit_thread_ids == [gui_thread_id]


def test_progress_dialog_reports_validation_progress():
    qt_app()
    task_runner = QtTaskRunner(TaskRunner())
    dialog = create_import_progress(
        task_runner,
        EntityImportService(),
        ITEM_XML,
        "xml",
        duplicate_policy="replace",
        existing_source_identities=(),
    )

    assert isinstance(dialog, ImportProgressView)
    assert dialog.exec() == QDialog.DialogCode.Accepted
    assert dialog.model.preview.can_commit is True
    assert isinstance(dialog.model.task, Task)
    assert dialog.model.current == 1
    assert dialog.model.total == 1
    assert dialog.progress_bar.value() == 1000
    assert dialog.status_label.text() == "Resolving entity references: 1 of 1"
    task_runner.shutdown()


def test_progress_dialog_does_not_append_counts_to_its_status():
    qt_app()
    model = SimpleNamespace(
        status="Updating records",
        snapshot=lambda: (model.status, 25, 4000),
        update_progress=lambda current, total: None,
    )
    dialog = ImportProgressView.__new__(ImportProgressView)
    dialog.model = model
    dialog.progress_bar = QProgressBar()
    dialog.status_label = QLabel()

    dialog._sync_progress()
    dialog._sync_progress()

    assert model.status == "Updating records"
    assert dialog.status_label.text() == "Updating records: 25 of 4000"


def test_progress_cancel_stops_import_before_preview_or_commit(tmp_path):
    qt_app()
    controller = project_controller(tmp_path)
    source = tmp_path / "items.xml"
    source.write_text(ITEM_XML, encoding="utf-8")
    preview_opened = []

    class CancellableService(EntityImportService):
        def preview_xml(self, source, *, is_cancelled=None, **kwargs):
            wait = Event()
            while not is_cancelled():
                wait.wait(0.001)
            return ImportPreview((), (), str(source), cancelled=True)

    def cancelling_progress_factory(*args, **kwargs):
        dialog = create_import_progress(*args, **kwargs)
        QTimer.singleShot(0, dialog._request_cancel)
        return dialog

    import_controller = EntityImportController(
        controller,
        service=CancellableService(),
        progress_factory=cancelling_progress_factory,
        preview_factory=lambda *args, **kwargs: preview_opened.append(True),
        error_reporter=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )

    assert import_controller.import_source(source, "xml") is None
    assert preview_opened == []
    assert not controller.project.blocks.contains(
        "dmtools-compendium-entity-database"
    )


def test_import_preview_factory_uses_popup_editor():
    qt_app()
    preview = EntityImportService().preview_xml(ITEM_XML)

    dialog = create_import_preview(preview)

    assert isinstance(dialog, PopupEditorView)
    assert "Valid records: 1" in dialog.model.summary


def test_import_preview_requires_explicit_skip_for_mixed_batch():
    qt_app()
    service = EntityImportService()
    item = service.preview_xml(ITEM_XML).records[0]
    preview = service.preview_json(
        [
            {"entity_type": "item", "payload": item.payload},
            {"entity_type": "unknown", "name": "Future"},
        ]
    )
    dialog = create_import_preview(preview)

    assert dialog.skip_invalid_check.isHidden() is False
    assert dialog.ok_button.isEnabled() is False

    dialog.skip_invalid_check.setChecked(True)

    assert dialog.ok_button.isEnabled() is True
    assert dialog.update_model().skip_invalid is True


def test_menu_import_actions_are_guarded_and_delegate():
    qt_app()
    disabled_window = QMainWindow()
    disabled_window.menuFile = disabled_window.menuBar().addMenu("File")
    disabled_window.menuEdit = disabled_window.menuBar().addMenu("Edit")
    setup_menu(disabled_window)
    assert disabled_window.import_xml_action.isEnabled() is False
    assert disabled_window.import_json_action.isEnabled() is False

    calls = []
    enabled_window = QMainWindow()
    enabled_window.menuFile = enabled_window.menuBar().addMenu("File")
    enabled_window.menuEdit = enabled_window.menuBar().addMenu("Edit")
    import_controller = SimpleNamespace(
        can_import=True,
        import_xml=lambda: calls.append("xml"),
        import_json=lambda: calls.append("json"),
    )
    setup_menu(enabled_window, import_controller)

    enabled_window.import_xml_action.trigger()
    enabled_window.import_json_action.trigger()
    assert calls == ["xml", "json"]