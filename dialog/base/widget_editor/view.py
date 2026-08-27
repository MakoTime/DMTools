from PySide6.QtWidgets import QWidget

from ..editor import EditorView


class WidgetEditorView(QWidget, EditorView):
    """Low-level editor view for widgets embedded in a host workspace."""

    def __init__(self, model, parent=None, on_apply=None, on_close=None):
        QWidget.__init__(self, parent)
        EditorView.__init__(self, model, on_apply=on_apply, on_close=on_close)

    def close_editor(self, reason="window"):
        self.notify_closed(reason)
        return self.close()
