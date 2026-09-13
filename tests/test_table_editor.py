import pandas as pd
from PySide6.QtWidgets import QApplication

from dialog.table_editor import TableEditorModel, create_table_editor


def qt_app():
    return QApplication.instance() or QApplication([])


def test_table_editor_model_loads_uid_and_commits_temporary_frame():
    committed = []
    table = type("Table", (), {"guid": "table-1", "data": pd.DataFrame([{"name": "Owlbear"}])})()
    model = TableEditorModel(
        table_uid="table-1",
        table_loader=lambda uid: table,
        commit_callback=lambda uid, frame: committed.append((uid, frame.copy())),
    )

    model.frame.loc[0, "name"] = "Dragon"
    assert model.commit_changes() is True
    assert committed[0][0] == "table-1"
    assert committed[0][1].iloc[0, 0] == "Dragon"
    assert model._draft is None
    model.release_table()
    assert model._table is None


def test_table_editor_view_releases_lazy_table_on_close():
    qt_app()
    view = create_table_editor(
        table_uid="table-1",
        table_loader=lambda uid: type(
            "Table", (), {"guid": uid, "data": pd.DataFrame([{"name": "Owlbear"}])}
        )(),
        commit_callback=lambda uid, frame: True,
    )

    assert view.table_model.rowCount() == 1
    view.close()
    assert view.model is None
