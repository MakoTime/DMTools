from PySide6.QtWidgets import QWidget

from .model import SpellPropertyEditorModel
from .view import SpellPropertyEditorView


def create_spell_property_dialog(
    payload=None,
    parent: QWidget | None = None,
    on_apply=None,
    draft=None,
):
    model = (
        SpellPropertyEditorModel.from_draft(draft)
        if draft is not None
        else SpellPropertyEditorModel.from_payload(payload or {})
    )
    return SpellPropertyEditorView(model, parent=parent, on_apply=on_apply)
