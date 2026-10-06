from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from application.progression_table import (
    CONFIG_KEY,
    GENERATED_COLUMNS,
    RECHARGE_TYPES,
    TABLE_ID,
    table_configuration,
    validate_formula,
)
from dialog.base.editor import EditorModel


class ProgressionEditorModel(EditorModel):
    """Detached draft for a class progression table."""

    def __init__(self, payload: dict[str, Any]):
        self._payload = payload
        existing = table_configuration(payload.get(CONFIG_KEY))
        self._draft = deepcopy(existing or {"table_id": TABLE_ID, "columns": []})
        self._draft.setdefault("generated_order", ["features"])
        for column in self._draft["columns"]:
            if column["key"] not in self._draft["generated_order"]:
                self._draft["generated_order"].append(column["key"])

    @property
    def configuration(self):
        return deepcopy(self._draft)

    @property
    def editor_columns(self):
        generated = {column["key"]: column for column in GENERATED_COLUMNS}
        custom = {column["key"]: column for column in self.configuration["columns"]}
        ordered = [generated[column["key"]] for column in GENERATED_COLUMNS[:2]]
        ordered.extend(
            generated[key] if key in generated else custom[key]
            for key in self.configuration["generated_order"]
            if key in generated or key in custom
        )
        return deepcopy(ordered)

    def add_column(self, label, legacy_label=None, *, key=None, column_type="text", source="manual", values=None):
        if legacy_label is not None:
            key, label = label, legacy_label
        label = str(label).strip()
        key = key or re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
        existing_keys = {column["key"] for column in self.editor_columns}
        if not key or key in existing_keys:
            raise ValueError("Column display names must produce a unique key")
        self._draft["columns"].append({
            "key": key,
            "label": label,
            "type": str(column_type),
            "source": str(source),
            "values": {str(level): deepcopy(value) for level, value in (values or {}).items()},
            "visible": True,
            "method": "table",
            "visibility_mode": "values",
            "recharge_values": {},
            "mini_columns": [
                {"key": "value", "label": "Value", "visible": True, "merge": False},
            ],
        })
        self._draft["generated_order"].append(key)

    def update_column(self, key, **changes):
        column = self._column(key)
        for name in ("label", "type", "source", "formula", "notes", "visible", "method", "visibility_mode", "mini_columns"):
            if name in changes:
                column[name] = deepcopy(changes[name])
        if "values" in changes:
            column["values"] = {str(level): deepcopy(value) for level, value in changes["values"].items()}
        if "recharge_values" in changes:
            column["recharge_values"] = {
                str(level): str(value)
                for level, value in changes["recharge_values"].items()
            }

    def remove_column(self, key):
        if key in {column["key"] for column in GENERATED_COLUMNS}:
            raise ValueError("Generated progression columns cannot be removed")
        self._draft["columns"] = [column for column in self._draft["columns"] if column["key"] != key]
        self._draft["generated_order"] = [item for item in self._draft["generated_order"] if item != key]

    def reorder_columns(self, keys):
        fixed_keys = [column["key"] for column in GENERATED_COLUMNS[:2]]
        if set(keys) == {column["key"] for column in self._draft["columns"]}:
            by_key = {column["key"]: column for column in self._draft["columns"]}
            self._draft["columns"] = [by_key[key] for key in keys]
            return
        if tuple(keys[: len(fixed_keys)]) != tuple(fixed_keys):
            raise ValueError("Level and proficiency bonus must remain first")
        keys = tuple(keys[len(fixed_keys):])
        valid_keys = {"features", *(column["key"] for column in self._draft["columns"])}
        if set(keys) != valid_keys or len(keys) != len(valid_keys):
            raise ValueError("Column order must contain every column exactly once")
        self._draft["generated_order"] = list(keys)
        return

    def move_column(self, key, direction):
        keys = [column["key"] for column in self.editor_columns]
        index = keys.index(key)
        target = index + (-1 if direction == "left" else 1)
        fixed_count = 2
        if index < fixed_count or target < fixed_count or target >= len(keys):
            return
        keys[index], keys[target] = keys[target], keys[index]
        self.reorder_columns(keys)

    def validate(self):
        configuration = table_configuration(self._draft)
        if configuration is None:
            raise ValueError("A progression table requires at least one valid column")
        if not configuration["columns"]:
            raise ValueError("A progression table requires at least one column")
        keys = [column["key"] for column in configuration["columns"]]
        if len(keys) != len(set(keys)):
            raise ValueError("Progression column keys must be unique")
        for column in configuration["columns"]:
            if any(not str(level).isdigit() or not 1 <= int(level) <= 20 for level in column["values"]):
                raise ValueError("Progression values must use class levels 1 through 20")
            if column["method"] == "table" and "1" not in column["values"]:
                raise ValueError("Every resource column requires a level 1 value")
            if column["method"] not in {"table", "formula"}:
                raise ValueError("Progression columns require a table or formula method")
            if column["method"] == "formula":
                validate_formula(column.get("formula"))
            if column["visibility_mode"] not in {"values", "both", "changes"}:
                raise ValueError("Unknown progression visibility mode")
            if any(value not in RECHARGE_TYPES for value in column["recharge_values"].values()):
                raise ValueError("Unknown resource recharge type")
            if any(
                not str(level).isdigit() or not 1 <= int(level) <= 20
                for level in column["recharge_values"]
            ):
                raise ValueError("Recharge values must use class levels 1 through 20")
            mini_keys = [item["key"] for item in column["mini_columns"]]
            if len(mini_keys) != len(set(mini_keys)) or any(key not in {"value", "recharge"} for key in mini_keys):
                raise ValueError("Small table columns must be value or recharge")

    def apply(self):
        self.validate()
        return deepcopy(self._draft)

    def _column(self, key):
        for column in self._draft["columns"]:
            if column["key"] == key:
                return column
        raise KeyError(key)