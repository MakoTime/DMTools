from __future__ import annotations

from typing import Callable

import pandas as pd

from dialog.base.editor import EditorModel


class TableEditorModel(EditorModel):
    """Temporary editable state for one UID-backed table artifact."""

    def __init__(
        self,
        table=None,
        *,
        table_uid=None,
        table_loader: Callable[[str], object] | None = None,
        commit_callback: Callable[[str, pd.DataFrame], object] | None = None,
    ):
        if table is None and (table_uid is None or table_loader is None):
            raise ValueError("A table or UID-backed table loader is required")
        self._table = table
        self.table_uid = table_uid or table.guid
        self._table_loader = table_loader
        self._commit_callback = commit_callback
        self._draft: pd.DataFrame | None = None

    @property
    def table(self):
        if self._table is None:
            self._table = self._table_loader(self.table_uid)
        return self._table

    @property
    def frame(self):
        if self._draft is None:
            value = self.table
            value = value if isinstance(value, pd.DataFrame) else value.data
            self._draft = value.copy()
        return self._draft

    def refresh_table(self):
        self._draft = None
        return self.frame

    def commit_changes(self, frame=None):
        if self._commit_callback is None:
            raise RuntimeError("Table editor has no commit callback")
        candidate = (self.frame if frame is None else frame).copy()
        result = self._commit_callback(self.table_uid, candidate)
        if result is False:
            return False
        self._draft = None
        return True

    def release_table(self):
        self._draft = None
        if self._table_loader is not None:
            self._table = None
