from pathlib import Path

from application.project_controller import ProjectController


def test_save_as_rebinds_project_context_and_round_trips(tmp_path, monkeypatch):
    controller = ProjectController()
    controller.create_project(tmp_path / "source")
    target = tmp_path / "copy" / "project.json"
    monkeypatch.setattr(
        "application.project_controller.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(target), "Project files (project.json)"),
    )

    saved = controller.save_project_as()

    assert saved == target
    assert controller.project_file == target
    assert controller.project_context.package_path == target
    assert Path(target).is_file()

    reopened = ProjectController()
    reopened.load_project(target)
    assert reopened.project_context.package_path == target
    controller.close()
    reopened.close()
