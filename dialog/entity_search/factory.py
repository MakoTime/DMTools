from .model import EntitySearchModel
from .view import EntitySearchView


def create_entity_search_dialog(
    store,
    entity_type,
    *,
    project_controller=None,
    on_open=None,
    origin_uid=None,
    parent=None,
    on_close=None,
):
    model = EntitySearchModel(store=store, entity_type=entity_type)
    return EntitySearchView(
        model,
        project_controller=project_controller,
        on_open=on_open,
        origin_uid=origin_uid,
        parent=parent,
        on_close=on_close,
    )
