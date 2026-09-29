from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
import ast
import operator
import re
from typing import Any


TABLE_ID = "class_progression"
CONFIG_KEY = "presentation_progression"
GENERATED_COLUMNS = (
    {"key": "level", "label": "Level", "source": "generated"},
    {"key": "proficiency_bonus", "label": "Proficiency Bonus", "source": "generated"},
    {"key": "features", "label": "Features", "source": "generated"},
)
VISIBILITY_MODES = {"values", "both", "changes"}
RECHARGE_TYPES = ("short_rest", "long_rest", "dawn", "dusk", "round")
DEFAULT_MINI_COLUMNS = (
    {"key": "value", "label": "Value", "visible": True, "merge": False},
    {"key": "recharge", "label": "Recharge", "visible": False, "merge": True},
)


def table_configuration(value: Any) -> dict[str, Any] | None:
    """Return a validated custom table configuration, or ``None``."""
    if not isinstance(value, Mapping):
        return None
    columns = value.get("columns")
    if not isinstance(columns, list):
        return None
    normalized = {
        "table_id": str(value.get("table_id") or TABLE_ID),
        "columns": [],
        "generated_order": ["features"],
    }
    for column in columns:
        if not isinstance(column, Mapping):
            continue
        key = str(column.get("key", "")).strip()
        label = str(column.get("label", column.get("display_name", key))).strip()
        if not key or not label:
            continue
        if key in {column["key"] for column in GENERATED_COLUMNS} or column.get("source") == "generated":
            continue
        values = column.get("values", {})
        if not isinstance(values, Mapping):
            values = {}
        normalized_column = {
            "key": key,
            "label": label,
            "type": str(column.get("type", "text")),
            "source": str(column.get("source", "manual")),
            "values": {str(level): deepcopy(item) for level, item in values.items()},
            "visible": column.get("visible", True) is not False,
            "method": str(column.get("method", "table")),
            "visibility_mode": str(column.get("visibility_mode", "values")),
        }
        mini_columns = column.get("mini_columns")
        if not isinstance(mini_columns, list):
            legacy_mode = normalized_column["visibility_mode"]
            legacy_recharge = column.get("recharge_values", {})
            mini_columns = [
                {"key": "value", "label": "Value", "visible": True, "merge": False},
                {
                    "key": "recharge",
                    "label": "Recharge",
                    "visible": legacy_mode == "both" or bool(legacy_recharge),
                    "merge": False,
                },
            ]
        normalized_column["mini_columns"] = _normalize_mini_columns(mini_columns)
        recharge_values = column.get("recharge_values", {})
        normalized_column["recharge_values"] = (
            {str(level): str(value) for level, value in recharge_values.items()}
            if isinstance(recharge_values, Mapping) else {}
        )
        if normalized_column["method"] not in {"table", "formula"}:
            normalized_column["method"] = "table"
        if normalized_column["visibility_mode"] not in VISIBILITY_MODES:
            normalized_column["visibility_mode"] = "values"
        for optional in ("formula", "notes"):
            if optional in column:
                normalized_column[optional] = deepcopy(column[optional])
        normalized["columns"].append(normalized_column)
    configured_order = value.get("generated_order")
    valid_keys = {"features", *(column["key"] for column in normalized["columns"])}
    if isinstance(configured_order, list):
        order = [str(key) for key in configured_order if str(key) in valid_keys]
        normalized["generated_order"] = order + [
            key for key in ("features", *(column["key"] for column in normalized["columns"]))
            if key not in order
        ]
    else:
        normalized["generated_order"].extend(column["key"] for column in normalized["columns"])
    return normalized


def custom_progression_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """Build rows from user-authored columns while preserving saved order."""
    configuration = table_configuration(payload.get(CONFIG_KEY))
    if configuration is None:
        return None
    columns = [column for column in configuration["columns"] if column["visible"]]
    default_rows = _default_class_rows(payload)
    rows = []
    for level in range(1, 21):
        row = default_rows[level - 1]
        for column in columns:
            value = _display_resource_value(_column_value(column, level, row))
            if column["visibility_mode"] == "changes":
                previous = _column_value(column, level - 1, default_rows[level - 2]) if level > 1 else None
                if value == previous:
                    value = ""
            display_value = (
                "" if column["visibility_mode"] == "changes" and value == ""
                else "-" if value in (None, "", False, 0) else value
            )
            recharge = column["recharge_values"].get(str(level))
            mini_columns = {item["key"]: item for item in column["mini_columns"]}
            value_column = mini_columns.get("value")
            recharge_column = mini_columns.get("recharge")
            if value_column and value_column["visible"]:
                if recharge and recharge_column and recharge_column["visible"] and recharge_column["merge"]:
                    display_value = f"{display_value} ({recharge})"
                row[column["key"]] = display_value
                if column["visibility_mode"] == "both":
                    row[f"{column['key']}_values"] = display_value
            if recharge and recharge_column and recharge_column["visible"] and not recharge_column["merge"]:
                row[f"{column['key']}_recharge"] = recharge
        rows.append(row)
    return rows


def _normalize_mini_columns(columns):
    normalized = []
    seen = set()
    for item in columns:
        if not isinstance(item, Mapping):
            continue
        key = str(item.get("key", "")).strip()
        if not key or key in seen or key not in {"value", "recharge"}:
            continue
        seen.add(key)
        normalized.append({
            "key": key,
            "label": str(item.get("label", key.title())).strip() or key.title(),
            "visible": item.get("visible", True) is not False,
            "merge": item.get("merge", False) is True,
        })
    return normalized or [deepcopy(item) for item in DEFAULT_MINI_COLUMNS[:1]]


def _default_class_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    features_by_level = {}
    for feature in payload.get("features", ()):
        if isinstance(feature, Mapping) and isinstance(feature.get("level"), int):
            features_by_level.setdefault(feature["level"], []).append(str(feature.get("name", "")))
    return [
        {
            "level": _ordinal(level),
            "proficiency_bonus": f"+{2 + (level - 1) // 4}",
            "features": ", ".join(features_by_level.get(level, ())) or "-",
        }
        for level in range(1, 21)
    ]


def _column_value(column: Mapping[str, Any], level: int, row: Mapping[str, Any]) -> Any:
    if level < 1:
        return None
    values = column.get("values", {})
    if isinstance(values, Mapping):
        if column.get("method") == "formula":
            if str(level) in values:
                return values[str(level)]
            return _evaluate_formula(column.get("formula", ""), level, row)
        eligible = [int(key) for key in values if str(key).isdigit() and int(key) <= level]
        if eligible:
            override = values.get(str(max(eligible)))
            if override not in (None, ""):
                return override
    if not isinstance(values, Mapping):
        return None
    eligible = [int(key) for key in values if str(key).isdigit() and int(key) <= level]
    return values.get(str(max(eligible))) if eligible else None


def _evaluate_formula(formula: Any, level: int, row: Mapping[str, Any]) -> Any:
    if not isinstance(formula, str) or not formula.strip():
        return None
    expression = formula.format(
        level=level,
        class_level=level,
        proficiency=row.get("proficiency_bonus", ""),
        proficiency_bonus=row.get("proficiency_bonus", ""),
    )
    expression = re.sub(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", r"\1", expression)
    try:
        tree = ast.parse(expression, mode="eval")
        proficiency = row.get("proficiency_bonus", 0)
        if isinstance(proficiency, str) and proficiency.startswith("+"):
            proficiency = int(proficiency[1:])
        names = {
            "level": level,
            "class_level": level,
            "proficiency": proficiency,
            "proficiency_bonus": proficiency,
            "ability_modifier": 0,
            "STR": 0,
            "DEX": 0,
            "CON": 0,
            "INT": 0,
            "WIS": 0,
            "CHA": 0,
        }
        names.update({
            key: value
            for key, value in row.items()
            if isinstance(key, str) and key.isidentifier() and key not in names
        })
        return _safe_eval(tree.body, names)
    except (ValueError, SyntaxError, KeyError, TypeError):
        return expression


def validate_formula(formula: Any) -> None:
    """Validate an arithmetic progression formula without evaluating variables."""
    if not isinstance(formula, str) or not formula.strip():
        raise ValueError("Formula columns require a formula")
    try:
        expression = formula.format(
            level="level",
            class_level="class_level",
            proficiency="proficiency",
            proficiency_bonus="proficiency_bonus",
            ability_modifier="ability_modifier",
        )
        expression = re.sub(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", r"\1", expression)
        tree = ast.parse(expression, mode="eval")
        _validate_formula_node(tree.body)
    except (KeyError, SyntaxError, ValueError, TypeError) as error:
        raise ValueError("Formula must be valid arithmetic") from error


def _validate_formula_node(node):
    operators = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return
    if isinstance(node, ast.Name):
        return
    if isinstance(node, ast.BinOp) and isinstance(node.op, operators):
        _validate_formula_node(node.left)
        _validate_formula_node(node.right)
        return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        _validate_formula_node(node.operand)
        return
    raise ValueError("Unsupported formula expression")


def _safe_eval(node, names):
    operators = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in operators:
        return operators[type(node.op)](_safe_eval(node.left, names), _safe_eval(node.right, names))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _safe_eval(node.operand, names)
        return -value if isinstance(node.op, ast.USub) else value
    raise ValueError("Unsupported progression formula")


def _display_resource_value(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return value
    dice = value.get("dice_roll", value.get("dice"))
    if isinstance(dice, Mapping):
        count = dice.get("count", 1)
        sides = dice.get("dice", dice.get("sides"))
        modifier = dice.get("modifier", 0)
        if sides is not None:
            suffix = f"{modifier:+}" if modifier else ""
            return f"{count}d{sides}{suffix}"
    return value.get("value", value.get("maximum", value))


def _ordinal(value: int) -> str:
    suffix = "th" if 10 < value % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"