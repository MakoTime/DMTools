from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from projectfoundry import ArtifactStore, Project, ProjectContext

from application.legacy_compatibility import LegacyProjectCompatibility


@dataclass
class LoadedProject:
    project: Project
    context: ProjectContext
    loaded_objects: list
    artifact_store: ArtifactStore


class ProjectLifecycleService:
    """Own compatibility-aware project package lifecycle operations.

    DMTools projects still contain a legacy ``roots`` document alongside the
    ProjectFoundry ``framework`` document.  This service keeps that migration
    contract in one place while callers remain responsible for rebinding views.
    """

    def __init__(self, legacy_serializer, framework_serializer):
        self.legacy_compatibility = LegacyProjectCompatibility(legacy_serializer)
        self.framework_serializer = framework_serializer

    @staticmethod
    def new_project(artifact_store=None):
        """Construct a fresh ProjectFoundry composition root."""
        return Project(artifact_store=artifact_store)

    def save(self, project_file, project, tree_manager):
        return self.legacy_compatibility.save(
            project_file,
            tree_manager,
            framework_document=self.framework_serializer.project_document(project),
        )

    def create(self, project_directory, project, tree_manager):
        artifact_store = ArtifactStore(project_directory)
        project.artifact_store = artifact_store
        project_file = self.save(project_directory, project, tree_manager)
        return project_file, ProjectContext(
            project_file,
            Path(project_directory),
            project,
        ), artifact_store

    def load(self, project_file, tree_manager, tree_model=None):
        project_file = Path(project_file)
        document = json.loads(project_file.read_text(encoding="utf-8"))
        if "framework" not in document:
            raise ValueError(
                "Legacy DMTools project detected; use import_legacy() "
                "to import it explicitly"
            )
        artifact_store = ArtifactStore(project_file.parent)
        project = self.new_project(artifact_store)
        self.framework_serializer.load_document(document["framework"], project)
        loaded_objects = self.legacy_compatibility.load(
            project_file,
            tree_manager,
            tree_model,
        )
        context = ProjectContext(project_file, project_file.parent, project)
        return LoadedProject(project, context, loaded_objects, artifact_store)

    def import_legacy(self, project_file, tree_manager, tree_model=None):
        """Import a legacy roots document into a fresh ProjectFoundry project."""
        project_file = Path(project_file)
        document = json.loads(project_file.read_text(encoding="utf-8"))
        if "roots" not in document:
            raise ValueError("Legacy DMTools project is missing its roots document")
        if "framework" in document:
            raise ValueError(
                "Project already contains a ProjectFoundry framework document; "
                "load it normally"
            )
        artifact_store = ArtifactStore(project_file.parent)
        project = self.new_project(artifact_store)
        loaded_objects = self.legacy_compatibility.import_legacy(
            project_file,
            tree_manager,
            tree_model,
        )
        context = ProjectContext(project_file, project_file.parent, project)
        return LoadedProject(project, context, loaded_objects, artifact_store)
