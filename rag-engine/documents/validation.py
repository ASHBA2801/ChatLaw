"""Validate document-builder input against a template."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Mapping

from .conditions import clause_is_active, has_value
from .constants import INDIA_REGIONS
from .types import FieldSpec, TemplateSpec

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


class FieldIssue(dict):
    """JSON-serialisable validation issue."""


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def validate_field(field: FieldSpec, values: Mapping[str, Any]) -> list[dict[str, str]]:
    field_id = field["id"]
    raw = values.get(field_id)
    requirement = field["requirement"]
    present = has_value(values, field_id)
    issues: list[dict[str, str]] = []

    if not present:
        if requirement == "required":
            issues.append({"field_id": field_id, "level": "error",
                           "message": f"{field['label']} is required before a draft can be generated."})
        elif requirement == "recommended":
            issues.append({"field_id": field_id, "level": "recommended",
                           "message": f"{field['label']} is recommended. The draft will mark it for completion if this clause is used."})
        return issues

    field_type = field["type"]
    if field_type in {"text", "textarea", "tel"} and not _string(raw):
        issues.append({"field_id": field_id, "level": "error", "message": f"{field['label']} cannot be empty."})
    if field_type == "email" and not EMAIL_RE.match(_string(raw)):
        issues.append({"field_id": field_id, "level": "error", "message": f"{field['label']} must be a valid email address."})
    if field_type == "date":
        match = ISO_DATE_RE.match(_string(raw))
        valid = False
        if match:
            try:
                date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                valid = True
            except ValueError:
                valid = False
        if not valid:
            issues.append({"field_id": field_id, "level": "error", "message": f"{field['label']} must be a valid date."})
    if field_type in {"number", "currency"}:
        try:
            number = float(raw)
        except (TypeError, ValueError):
            issues.append({"field_id": field_id, "level": "error", "message": f"{field['label']} must be a number."})
        else:
            if "min" in field and number < field["min"]:
                issues.append({"field_id": field_id, "level": "error",
                               "message": f"{field['label']} must be at least {field['min']}."})
            if "max" in field and number > field["max"]:
                issues.append({"field_id": field_id, "level": "error",
                               "message": f"{field['label']} must be at most {field['max']}."})
    if field_type == "select" and field.get("options"):
        allowed = {option["value"] for option in field["options"]}
        if str(raw) not in allowed:
            issues.append({"field_id": field_id, "level": "error",
                           "message": f"{field['label']} must be one of the listed options."})
    if field_id == "jurisdiction_country" and _string(raw) != "IN":
        issues.append({"field_id": field_id, "level": "error",
                       "message": "This generator currently supports India only."})
    if field_id == "jurisdiction_region" and _string(raw) not in INDIA_REGIONS:
        issues.append({"field_id": field_id, "level": "error",
                       "message": "Select a State or Union Territory in India."})
    if field.get("pattern") and _string(raw) and not re.match(field["pattern"], _string(raw)):
        issues.append({"field_id": field_id, "level": "error", "message": f"{field['label']} is not in the expected format."})
    return issues


def validate_values(template: TemplateSpec, values: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    for field in template["fields"]:
        issues.extend(validate_field(field, values))
    start = _string(values.get("effective_date"))
    end = _string(values.get("end_date"))
    if start and end and ISO_DATE_RE.match(start) and ISO_DATE_RE.match(end):
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        if end_date < start_date:
            issues.append({"field_id": "end_date", "level": "error",
                           "message": "The end date cannot be earlier than the start date."})
    blocking = [issue for issue in issues if issue["level"] == "error"]
    return {
        "ok": not blocking,
        "blocking": blocking,
        "issues": issues,
        "can_generate": not blocking,
    }


def active_clauses(template: TemplateSpec, values: Mapping[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for clause in template["clauses"]:
        if clause_is_active(clause.get("condition"), values):
            selected.append(clause)
    return selected


def placeholder_for(field: FieldSpec) -> str:
    return f"[{field['placeholder_label']} REQUIRED]"


CRITICAL_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9 /._-]{2,} REQUIRED\]")


def unresolved_critical_placeholders(template: TemplateSpec, values: Mapping[str, Any], sections: list[dict[str, Any]]) -> list[str]:
    fields = {field["id"]: field for field in template["fields"]}
    required_placeholders = {
        placeholder_for(field) for field in template["fields"] if field["requirement"] == "required"
    }
    found: list[str] = []
    for section in sections:
        body = section.get("body") or ""
        for placeholder in required_placeholders:
            if placeholder in body:
                field_id = next(fid for fid, field in fields.items() if placeholder_for(field) == placeholder)
                if has_value(values, field_id):
                    found.append(placeholder)
                elif fields[field_id]["requirement"] == "required":
                    found.append(placeholder)
    return list(dict.fromkeys(found))
