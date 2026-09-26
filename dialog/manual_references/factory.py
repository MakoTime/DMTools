from .model import ManualReferencesModel
from .view import ManualReferencesView


def create_manual_references_dialog(
    project_controller, *, on_open_entity=None, parent=None
):
    return ManualReferencesView(
        ManualReferencesModel(project_controller),
        on_open_entity=on_open_entity,
        parent=parent,
    )
