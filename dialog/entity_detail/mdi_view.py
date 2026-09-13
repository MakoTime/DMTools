from pathlib import Path

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout

from application.entity_rendering import render_entity_html
from dialog.base.widget_editor import WidgetEditorView

from .model import EntityDetailModel


class EntityDetailMdiView(WidgetEditorView):
    """Modeless read-only entity inspection view for a QMdiArea host."""

    def __init__(
        self,
        model: EntityDetailModel,
        parent=None,
        *,
        on_close=None,
        on_link=None,
    ):
        super().__init__(model, parent=parent, on_close=on_close)
        self.setWindowTitle(model.title)
        self.resize(720, 620)
        self.browser = QTextBrowser(self)
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        if on_link is not None:
            self.browser.anchorClicked.connect(lambda url: on_link(url.toString()))
        stylesheet = Path(__file__).resolve().parents[2] / "views" / "entity_inspection.css"
        if stylesheet.exists():
            self.browser.document().setDefaultStyleSheet(
                stylesheet.read_text(encoding="utf-8")
            )
        entity = model.entity
        self.browser.setHtml(render_entity_html(entity))
        model.release_entity()
        layout = QVBoxLayout(self)
        layout.addWidget(self.browser, 1)

    def refresh_entity(self, entity):
        """Replace derived presentation after the canonical record changes."""
        self.model._entity = entity
        self.setWindowTitle(self.model.title)
        self.browser.setHtml(render_entity_html(entity))
        self.model.release_entity()

    def closeEvent(self, event):
        self.notify_closed("window")
        self.model = None
        super().closeEvent(event)
