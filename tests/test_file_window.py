import json

from application.file_window import ProjectPackageAdapter, framework_project_counts
from application.startup import ApplicationLauncher


def test_framework_project_counts_use_block_metadata_only():
    data = {
        "framework": {
            "blocks": [
                {
                    "type": "entity_database",
                    "data": {"namespace": "compendium", "row_count": 120},
                },
                {
                    "type": "entity_database",
                    "data": {"namespace": "homebrew", "row_count": 7},
                },
                {"type": "collection", "data": {"entity_uids": ["a", "b"]}},
                {"type": "collection", "data": {"entity_uids": []}},
            ]
        }
    }

    assert framework_project_counts(data) == {
        "compendium": 120,
        "homebrew": 7,
        "collections": 2,
    }


def test_framework_project_counts_support_legacy_projects():
    assert framework_project_counts({"roots": []}) == {
        "compendium": 0,
        "homebrew": 0,
        "collections": 0,
    }


def test_project_package_adapter_normalizes_directory_and_file_selections(tmp_path):
    project_file = tmp_path / "campaign" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text(json.dumps({"version": 1, "roots": []}), encoding="utf-8")

    assert ProjectPackageAdapter.from_selection(project_file).project_file == project_file
    assert ProjectPackageAdapter.from_selection(project_file.parent).project_file == project_file
    assert ApplicationLauncher._project_file(project_file.parent) == project_file
    assert ProjectPackageAdapter.from_selection(project_file).read_document()["roots"] == []