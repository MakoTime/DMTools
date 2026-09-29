import json
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)

from application.entity_rendering import render_entity_html
from common.icons import get_icon
from common import dev_mode
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
        on_rule=None,
        on_edit=None,
        on_class_progression=None,
        on_resolve=None,
    ):
        super().__init__(model, parent=parent, on_close=on_close)
        self.setWindowTitle(model.title)
        self.resize(720, 620)
        self.raw_view = None
        if dev_mode.is_enabled():
            self.raw_view = QPlainTextEdit(self)
            self.raw_view.setReadOnly(True)
            self.raw_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.browser = QTextBrowser(self)
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        if on_link is not None:
            self.browser.anchorClicked.connect(
                lambda url: on_link(url.toString(), on_rule=on_rule)
            )
        stylesheet = Path(__file__).resolve().parents[2] / "views" / "entity_inspection.css"
        if stylesheet.exists():
            self.browser.document().setDefaultStyleSheet(
                stylesheet.read_text(encoding="utf-8")
            )
        entity = model.entity
        self.browser.setHtml(render_entity_html(entity))
        model.release_entity()
        toolbar = QHBoxLayout()
        self.raw_button = None
        self.source_button = None
        if dev_mode.is_enabled():
            self.raw_button = QPushButton("Raw JSON", self)
            self.raw_button.setCheckable(True)
            self.raw_button.setChecked(True)
            self.raw_button.setToolTip("Show or hide raw entity JSON")
            self.raw_button.toggled.connect(self._toggle_raw_view)
            toolbar.addWidget(self.raw_button)
            self.source_button = QPushButton(self)
            self.source_button.setCheckable(True)
            self.source_button.setToolTip("Toggle between canonical payload and imported source JSON")
            self.source_button.toggled.connect(self._toggle_raw_source)
            toolbar.addWidget(self.source_button)
            self._update_raw_source(entity)
        toolbar.addStretch(1)
        if on_edit is not None:
            edit_button = QPushButton(self)
            edit_button.setIcon(get_icon("edit"))
            edit_button.setToolTip("Edit Homebrew data")
            edit_button.clicked.connect(lambda: on_edit(entity))
            toolbar.addWidget(edit_button)
        if on_class_progression is not None and getattr(entity, "entity_type", None) == "class":
            progression_button = QPushButton(self)
            progression_button.setIcon(get_icon("grid"))
            progression_button.setToolTip("Edit class progression table")
            progression_button.clicked.connect(lambda: on_class_progression(entity))
            toolbar.addWidget(progression_button)
        if on_resolve is not None and getattr(entity, "source_metadata", {}).get(
            "reference_diagnostics"
        ):
            self.resolve_button = QPushButton("Resolve references", self)
            self.resolve_button.clicked.connect(lambda: on_resolve(entity))
            toolbar.addWidget(self.resolve_button)
        else:
            self.resolve_button = None
        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        splitter = QSplitter(self)
        if dev_mode.is_enabled():
            splitter.addWidget(self.raw_view)
        splitter.addWidget(self.browser)
        if dev_mode.is_enabled():
            splitter.setSizes((360, 640))
        layout.addWidget(splitter, 1)

    @staticmethod
    def _source_info(entity):
        metadata = getattr(entity, "source_metadata", {}) or {}
        for key, label in (("api_source", "API source"), ("xml_source", "XML source")):
            if metadata.get(key) is not None:
                return key, label, metadata[key]
        return None, None, None

    @classmethod
    def _raw_json(cls, entity, source_type="payload"):
        source = getattr(entity, "payload", {})
        if source_type != "payload":
            source = (getattr(entity, "source_metadata", {}) or {}).get(source_type)
        return json.dumps(source, indent=2, ensure_ascii=False, sort_keys=True)

    def _update_raw_source(self, entity):
        source_type, source_label, _source = self._source_info(entity)
        has_source = source_type is not None
        self.source_button.setText(source_label or "Source")
        self.source_button.setVisible(
            has_source and self.raw_button.isChecked()
        )
        self.source_button.setEnabled(has_source)
        source_type = source_type if has_source and self.source_button.isChecked() else "payload"
        self.raw_view.setPlainText(self._raw_json(entity, source_type))

    def _toggle_raw_view(self, visible):
        self.raw_view.setVisible(visible)
        self.source_button.setVisible(visible and self.source_button.isEnabled())

    def _toggle_raw_source(self, _checked):
        entity = self.model.entity
        if entity is not None:
            self._update_raw_source(entity)

    def refresh_entity(self, entity):
        """Replace derived presentation after the canonical record changes."""
        self.model._entity = entity
        self.setWindowTitle(self.model.title)
        if dev_mode.is_enabled():
            self._update_raw_source(entity)
        self.browser.setHtml(render_entity_html(entity))
        if self.resolve_button is not None:
            self.resolve_button.setVisible(
                bool(getattr(entity, "source_metadata", {}).get("reference_diagnostics"))
            )
        self.model.release_entity()

    def closeEvent(self, event):
        self.notify_closed("window")
        self.model = None
        super().closeEvent(event)
