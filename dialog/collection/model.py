from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from application.entity_database import MissingEntityRow
from application.entity_references import EntityReference


class CollectionTableModel(QAbstractTableModel):
    """Lazy presentation adapter over Collection member UIDs."""

    EntityUidRole = Qt.ItemDataRole.UserRole + 1
    EntityReferenceRole = Qt.ItemDataRole.UserRole + 2
    COLUMNS = (
        ("Name", "name"),
        ("Type", "entity_type"),
        ("Source", "source_namespace"),
        ("Status", "status"),
    )

    def __init__(self, project_controller, collection_uid, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.collection_uid = collection_uid
        self._cache = {}
        self._entity_type = None
        self._source_namespace = None
        self._tag = None
        self._text = None
        self._group_by = None
        self._uids = []
        self._visible_uids = []
        self.page_size = 100
        self._page = 0
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self._cache.clear()
        members = self.project_controller.resolve_collection_members(
            self.collection_uid
        )
        self._uids = [member.uid for member in members]
        self._visible_uids = list(self._uids)
        self._apply_filters()
        self.endResetModel()

    @property
    def page(self):
        return self._page

    @property
    def page_count(self):
        return max(1, (len(self._visible_uids) + self.page_size - 1) // self.page_size)

    def set_page(self, page):
        page = max(0, min(int(page), self.page_count - 1))
        if page == self._page:
            return False
        self.beginResetModel()
        self._page = page
        self.endResetModel()
        return True

    def _page_uids(self):
        start = self._page * self.page_size
        return self._visible_uids[start : start + self.page_size]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._page_uids())

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entity_uid = self._page_uids()[index.row()]
        if role == self.EntityUidRole:
            return entity_uid
        if role == self.EntityReferenceRole:
            row = self._resolve(entity_uid)
            if isinstance(row, MissingEntityRow):
                return None
            return EntityReference(
                row.uid, row.entity_type, row.source_namespace, row.name
            )
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        row = self._resolve(entity_uid)
        attribute = self.COLUMNS[index.column()][1]
        if isinstance(row, MissingEntityRow):
            values = {
                "name": entity_uid,
                "entity_type": "",
                "source_namespace": "",
                "status": "Missing",
            }
            return values[attribute]
        if attribute == "status":
            return "Available"
        return str(getattr(row, attribute))

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section][0]
        return section + 1

    def entity_uid(self, index):
        return self._page_uids()[index.row()] if index.isValid() else None

    def set_filters(
        self,
        *,
        entity_type=None,
        source_namespace=None,
        tag=None,
        text=None,
    ):
        self.beginResetModel()
        self._entity_type = entity_type or None
        self._source_namespace = source_namespace or None
        self._tag = tag.casefold() if tag else None
        self._text = text.casefold() if text else None
        self._apply_filters()
        self._page = min(self._page, self.page_count - 1)
        self.endResetModel()

    def set_group_by(self, attribute=None):
        if attribute not in {None, "entity_type", "source_namespace"}:
            raise ValueError(f"Unsupported Collection grouping: {attribute}")
        self.beginResetModel()
        self._group_by = attribute
        self._apply_filters()
        self.endResetModel()

    def move_member(self, source_row, destination_row):
        if self._group_by or len(self._visible_uids) != len(self._uids):
            raise ValueError("Clear Collection filters and grouping before reordering")
        reordered = list(self._uids)
        entity_uid = reordered.pop(source_row)
        reordered.insert(destination_row, entity_uid)
        self.project_controller.reorder_collection_entities(
            self.collection_uid, reordered
        )
        self.refresh()

    def _resolve(self, entity_uid):
        if entity_uid not in self._cache:
            try:
                self._cache[entity_uid] = self.project_controller.resolve_entity(
                    entity_uid
                )
            except ValueError:
                self._cache[entity_uid] = MissingEntityRow(entity_uid)
        return self._cache[entity_uid]

    def _apply_filters(self):
        filters_active = any(
            (self._entity_type, self._source_namespace, self._tag, self._text)
        )
        self._visible_uids = (
            [uid for uid in self._uids if self._matches(uid)]
            if filters_active
            else list(self._uids)
        )
        if self._group_by:
            self._visible_uids.sort(key=self._group_key)

    def _matches(self, entity_uid):
        row = self._resolve(entity_uid)
        if isinstance(row, MissingEntityRow):
            return not any(
                (self._entity_type, self._source_namespace, self._tag, self._text)
            )
        if self._entity_type and row.entity_type != self._entity_type:
            return False
        if self._source_namespace and row.source_namespace != self._source_namespace:
            return False
        tags = row.payload.get("tags", ())
        if isinstance(tags, str):
            tags = (tags,)
        if self._tag and self._tag not in {str(tag).casefold() for tag in tags}:
            return False
        if self._text:
            searchable = [row.name, row.entity_type, row.source_namespace]
            searchable.extend(
                str(value)
                for value in row.payload.values()
                if isinstance(value, (str, int, float, bool))
            )
            if not any(self._text in value.casefold() for value in searchable):
                return False
        return True

    def _group_key(self, entity_uid):
        row = self._resolve(entity_uid)
        if isinstance(row, MissingEntityRow):
            return ("~missing", entity_uid)
        return (
            str(getattr(row, self._group_by)).casefold(),
            row.name.casefold(),
            row.uid,
        )