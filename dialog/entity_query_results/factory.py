from .model import EntityQueryResultsModel
from .view import EntityQueryResultsView


def create_entity_query_results(
    rows=(),
    *,
    project_controller,
    result_uid=None,
    rows_loader=None,
    collection_uid=None,
    on_open=None,
    on_clone=None,
    on_edit=None,
    origin_uid=None,
    parent=None,
):
    model = EntityQueryResultsModel(
        rows,
        result_uid=result_uid,
        rows_loader=rows_loader,
    )
    return EntityQueryResultsView(
        model,
        project_controller=project_controller,
        collection_uid=collection_uid,
        on_open=on_open,
        on_clone=on_clone,
        on_edit=on_edit,
        origin_uid=origin_uid,
        parent=parent,
    )