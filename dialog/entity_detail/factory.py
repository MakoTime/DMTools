from .model import EntityDetailModel
from .mdi_view import EntityDetailMdiView
from .view import EntityDetailView


def create_entity_detail_dialog(
    entity,
    parent=None,
    *,
    project_controller=None,
    on_clone=None,
    on_edit=None,
):
    return EntityDetailView(
        EntityDetailModel(entity),
        parent=parent,
        project_controller=project_controller,
        on_clone=on_clone,
        on_edit=on_edit,
    )


def create_entity_detail_mdi_view(
    entity=None,
    parent=None,
    *,
    entity_uid=None,
    entity_loader=None,
    on_close=None,
    on_link=None,
    on_rule=None,
    on_edit=None,
):
    """Create a modeless inspection view for insertion into a QMdiArea."""
    return EntityDetailMdiView(
        EntityDetailModel(
            entity,
            entity_uid=entity_uid,
            entity_loader=entity_loader,
        ),
        parent=parent,
        on_close=on_close,
        on_link=on_link,
        on_rule=on_rule,
        on_edit=on_edit,
    )
