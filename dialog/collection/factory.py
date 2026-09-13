from .model import CollectionTableModel
from .view import CollectionTableView


def create_collection_table(
    collection_uid,
    *,
    project_controller,
    on_open=None,
    origin_uid=None,
    parent=None,
):
    model = CollectionTableModel(project_controller, collection_uid)
    return CollectionTableView(
        model, on_open=on_open, origin_uid=origin_uid, parent=parent
    )