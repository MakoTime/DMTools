from .model import WorkspaceTabModel
from .view import WorkspaceTabView


def create_workspace_tab(
    tabs,
    widget,
    title=None,
    *,
    on_restore=None,
    insert_index=None,
):
    model = WorkspaceTabModel(
        title=widget.windowTitle() if title is None else title,
        can_restore=on_restore is not None,
    )
    return WorkspaceTabView(
        model,
        tabs,
        widget,
        on_restore=on_restore,
        insert_index=insert_index,
    )