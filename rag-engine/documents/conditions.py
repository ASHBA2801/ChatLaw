"""Evaluate template clause conditions against user-supplied values."""

from __future__ import annotations

from typing import Any, Mapping


def has_value(values: Mapping[str, Any], field_id: str) -> bool:
    value = values.get(field_id)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return value
    return True


def clause_is_active(condition: dict[str, Any] | None, values: Mapping[str, Any]) -> bool:
    if not condition:
        return True
    if "equals" in condition:
        field_id, expected = condition["equals"]
        actual = values.get(field_id)
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip() == expected
        return actual == expected
    if "truthy" in condition:
        return has_value(values, condition["truthy"])
    if "has_value" in condition:
        return has_value(values, condition["has_value"])
    return False
