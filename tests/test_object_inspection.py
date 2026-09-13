from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from dialog.object_inspection import create_object_inspection_view
from dialog.object_inspection.model import ObjectInspectionModel


def qt_app():
    return QApplication.instance() or QApplication([])


def test_object_inspection_model_resolves_uid_and_releases_payload():
    loaded = []
    model = ObjectInspectionModel(
        object_uid="object-1",
        object_loader=lambda uid: loaded.append(uid) or SimpleNamespace(
            guid=uid,
            name="Rules",
            metadata={"source": "rules"},
        ),
    )

    assert model.title == "Rules"
    assert loaded == ["object-1"]
    assert model.details["UID"] == "object-1"
    model.release_object()
    assert model._object is None


def test_object_inspection_view_releases_lazy_object_on_close():
    qt_app()
    view = create_object_inspection_view(
        object_uid="object-1",
        object_loader=lambda uid: SimpleNamespace(guid=uid, name="Rules"),
    )

    assert view.model.title == "Rules"
    view.close()
    assert view.model is None
