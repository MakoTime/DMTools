from .model import TableEditorModel
from .view import TableEditorView


def create_table_editor(
    table=None,
    parent=None,
    *,
    table_uid=None,
    table_loader=None,
    commit_callback=None,
    on_close=None,
):
    return TableEditorView(
        TableEditorModel(
            table,
            table_uid=table_uid,
            table_loader=table_loader,
            commit_callback=commit_callback,
        ),
        parent=parent,
        on_close=on_close,
    )
