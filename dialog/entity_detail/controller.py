from __future__ import annotations

from urllib.parse import unquote, urlparse

from PySide6.QtWidgets import QMdiArea

from application.entity_references import EntityNavigationController, EntityReference
from application.rules_catalog import _RULE_DESCRIPTIONS

from .factory import create_entity_detail_mdi_view


class EntityInspectionController:
    """Open and reuse modeless entity inspections in one MDI area."""

    def __init__(
        self, project_controller, mdi_area: QMdiArea, *, on_edit=None, on_rule=None
    ):
        self.project_controller = project_controller
        self.mdi_area = mdi_area
        self.on_edit = on_edit
        self.on_rule = on_rule
        self.navigation = EntityNavigationController(
            project_controller,
            on_open=self._display,
        )
        self._windows = {}
        self._active_uid = None

    def open(self, reference, *, origin_uid=None):
        return self.navigation.open(reference, origin_uid=origin_uid)

    def back(self):
        return self.navigation.back()

    def open_link(self, link, *, on_rule=None):
        """Open one renderer-generated entity or rule link."""
        parsed = urlparse(link)
        if parsed.scheme != "dmtools":
            raise ValueError("Unsupported entity link")
        if parsed.netloc == "rule":
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            if len(parts) != 2 or not all(parts):
                raise ValueError("Rule link is missing a valid category or value")
            category, value = parts
            values = _RULE_DESCRIPTIONS.get(category, {})
            if value not in values or value in {"description", "handbook_reference"}:
                raise ValueError("Rule link does not identify a catalog value")
            callback = on_rule or self.on_rule
            if callback is None:
                raise ValueError("No rule link handler is configured")
            return callback(category, value)
        if parsed.netloc != "entity":
            raise ValueError("Unsupported entity link")
        entity_uid = parsed.path.strip("/")
        if not entity_uid or "/" in entity_uid:
            raise ValueError("Entity link is missing a valid UID")
        entity = self.project_controller.resolve_entity(entity_uid)
        return self.navigation.open(
            EntityReference(
                entity_uid,
                entity.entity_type,
                entity.source_namespace,
                entity.name,
            ),
            origin_uid=self._active_uid,
        )

    def display(self, entity):
        """Display an already-resolved canonical entity without re-resolving it."""
        return self._display(entity)

    def refresh(self, entity_uid):
        """Re-resolve one open entity and invalidate its derived HTML."""
        window = self._windows.get(entity_uid)
        if window is None:
            return None
        entity = self.project_controller.resolve_entity(entity_uid)
        window.widget().refresh_entity(entity)
        return window.widget()

    def _display(self, entity):
        self._active_uid = entity.uid
        window = self._windows.get(entity.uid)
        if window is None:
            view = create_entity_detail_mdi_view(
                entity_uid=entity.uid,
                entity_loader=self.project_controller.resolve_entity,
                on_close=lambda _model, _reason, uid=entity.uid: self._windows.pop(
                    uid, None
                ),
                on_link=self.open_link,
                on_rule=self.on_rule,
                on_edit=self.on_edit,
            )
            window = self.mdi_area.addSubWindow(view)
            self._windows[entity.uid] = window
            view.show()
        self.mdi_area.setActiveSubWindow(window)
        window.showNormal()
        window.raise_()
        return window.widget()
