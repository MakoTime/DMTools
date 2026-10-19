from PySide6.QtWidgets import QWidget

from .model import SpellPropertyEditorModel
from .view import SpellPropertyEditorView


def create_spell_property_dialog(
    payload=None,
    parent: QWidget | None = None,
    on_apply=None,
    on_clone=None,
    draft=None,
    class_options=(),
):
    model = (
        SpellPropertyEditorModel.from_draft(draft)
        if draft is not None
        else SpellPropertyEditorModel.from_payload(payload or {})
    )

    def notify_apply(_record):
        if on_apply is not None:
            on_apply(model)

    return SpellPropertyEditorView(
        model,
        parent=parent,
        on_apply=notify_apply if on_apply is not None else None,
        on_clone=on_clone,
        class_options=class_options,
    )
