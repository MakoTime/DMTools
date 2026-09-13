class LegacyProjectCompatibility:
    """Explicit boundary for the roots-only DMTools project format."""

    def __init__(self, serializer):
        self.serializer = serializer

    def save(self, project_file, tree_manager, *, framework_document=None):
        return self.serializer.save(
            project_file,
            tree_manager,
            framework_document=framework_document,
        )

    def load(self, project_file, tree_manager, tree_model=None):
        return self.serializer.load(project_file, tree_manager, tree_model)

    def import_legacy(self, project_file, tree_manager, tree_model=None):
        return self.serializer.load(project_file, tree_manager, tree_model)
