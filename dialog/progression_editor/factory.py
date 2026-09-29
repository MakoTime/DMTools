from .model import ProgressionEditorModel
from .view import ProgressionEditorView


def create_progression_editor(payload, parent=None, *, on_apply=None):
    model = ProgressionEditorModel(payload)
    return ProgressionEditorView(model, parent=parent, on_apply=on_apply)