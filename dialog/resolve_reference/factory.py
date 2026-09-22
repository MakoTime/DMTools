from .model import ResolveReferencesModel
from .view import ResolveReferencesView


def create_resolve_references_dialog(entity, *, project_controller, parent=None):
    return ResolveReferencesView(
        ResolveReferencesModel(entity, project_controller),
        parent=parent,
    )
