from .model import ObjectInspectionModel
from .view import ObjectInspectionView


def create_object_inspection_view(
    inspected_object=None,
    parent=None,
    *,
    object_uid=None,
    object_loader=None,
    on_close=None,
):
    return ObjectInspectionView(
        ObjectInspectionModel(
            inspected_object,
            object_uid=object_uid,
            object_loader=object_loader,
        ),
        parent=parent,
        on_close=on_close,
    )
