"""Deterministic document-drafting intent and field clarification (no Gemini)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from documents.templates import TEMPLATES, get_template
from documents.validation import validate_values

MAX_ROUNDS = 8

# Ordered patterns: first match wins.
_INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("nda", re.compile(r"\b(?:nda|non[\s-]?disclosure|confidentiality agreement)\b", re.I)),
    ("employment_agreement", re.compile(r"\b(?:employment|employee|employer)\s+agreement\b|\bcontract of employment\b|\bjob\s+contract\b", re.I)),
    ("partnership_agreement", re.compile(r"\bpartnership\s+(?:agreement|deed)\b|\bpartners?\s+agreement\b", re.I)),
    ("sale_agreement", re.compile(r"\bsale\s+(?:of\s+)?(?:goods\s+)?agreement\b|\bagreement\s+(?:to\s+)?sell\b|\bpurchase\s+agreement\b", re.I)),
    ("mou", re.compile(r"\b(?:mou|memorandum of understanding)\b", re.I)),
    ("rent_lease", re.compile(r"\b(?:rent(?:al)?|lease)\s+agreement\b|\btenancy\s+agreement\b", re.I)),
    ("service_agreement", re.compile(r"\bservice\s+agreement\b|\bservices?\s+contract\b", re.I)),
    ("affidavit", re.compile(r"\baffidavit\b", re.I)),
    ("authorization_letter", re.compile(r"\bauthorization\s+letter\b|\bletter of authority\b|\bauthorisation\s+letter\b", re.I)),
    ("legal_notice", re.compile(r"\blegal\s+notice\b|\bdemand\s+notice\b", re.I)),
    ("consumer_complaint", re.compile(r"\bconsumer\s+complaint\b", re.I)),
    ("complaint", re.compile(r"\b(?:police\s+)?complaint\b|\bfir\b", re.I)),
]

_UNSUPPORTED = re.compile(
    r"\b(?:power of attorney|will|testament|divorce petition|bail application|writ petition|plaint)\b",
    re.I,
)

_DRAFT_VERB = re.compile(
    r"\b(?:draft|generate|create|prepare|write|make)\b.{0,40}\b(?:agreement|contract|nda|affidavit|notice|letter|mou|complaint|deed)\b"
    r"|\b(?:agreement|contract|nda|affidavit|notice|letter|mou)\b.{0,20}\b(?:draft|generate|create|prepare|write)\b",
    re.I,
)
_DRAFT_LOOSE = re.compile(r"\b(?:draft|generate|create|prepare|write|make)\b", re.I)

_REGION_HINTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Puducherry", "Chandigarh", "Jammu and Kashmir", "Ladakh",
]


@dataclass(frozen=True)
class DocumentDraftResult:
    action: str  # "pass" | "unsupported" | "clarify" | "ready"
    message: str
    state: dict[str, Any]


def detect_template_id(message: str) -> str | None:
    text = message or ""
    for template_id, pattern in _INTENT_PATTERNS:
        if pattern.search(text):
            return template_id
    return None


def looks_like_document_request(message: str) -> bool:
    text = message or ""
    if _UNSUPPORTED.search(text) and _DRAFT_LOOSE.search(text):
        return True
    if detect_template_id(text) and _DRAFT_VERB.search(text):
        return True
    if detect_template_id(text) and re.search(r"\b(?:need|want|help(?:\s+me)?)\b", text, re.I):
        return True
    return bool(_DRAFT_VERB.search(text))


def _empty_state(template_id: str | None = None, original_query: str = "") -> dict[str, Any]:
    return {
        "mode": "document_drafting",
        "template_id": template_id,
        "values": {"jurisdiction_country": "IN"},
        "asked": [],
        "round": 0,
        "max_rounds": MAX_ROUNDS,
        "original_query": original_query,
        "unsupported": False,
    }


def drafting_state_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata or not isinstance(metadata, dict):
        return None
    draft = metadata.get("document_draft")
    if isinstance(draft, dict) and draft.get("mode") == "document_drafting":
        return {
            "mode": "document_drafting",
            "template_id": draft.get("template_id"),
            "values": dict(draft.get("values") or {"jurisdiction_country": "IN"}),
            "asked": list(draft.get("asked") or []),
            "round": int(draft.get("round") or 0),
            "max_rounds": int(draft.get("max_rounds") or MAX_ROUNDS),
            "original_query": draft.get("original_query") or "",
            "unsupported": bool(draft.get("unsupported")),
            "pending_field": draft.get("pending_field"),
        }
    if metadata.get("kind") in {"document_clarification", "document_ready"} and isinstance(metadata.get("document_draft"), dict):
        return drafting_state_from_metadata({"document_draft": metadata["document_draft"]})
    return None


def _required_fields(template_id: str) -> list[dict[str, Any]]:
    template = get_template(template_id)
    return [field for field in template["fields"] if field.get("requirement") == "required"]


def _missing_required(template_id: str, values: dict[str, Any]) -> list[dict[str, Any]]:
    validation = validate_values(get_template(template_id), values)
    blocking_ids = {issue["field_id"] for issue in validation["blocking"]}
    return [field for field in _required_fields(template_id) if field["id"] in blocking_ids]


def _optional_missing(template_id: str, values: dict[str, Any]) -> list[str]:
    template = get_template(template_id)
    missing = []
    for field in template["fields"]:
        if field.get("requirement") not in {"recommended", "optional"}:
            continue
        raw = values.get(field["id"])
        if raw in (None, "", False):
            missing.append(field["id"])
    return missing


def _question_for_field(field: dict[str, Any]) -> str:
    help_text = (field.get("help") or "").strip()
    base = f"To draft this document, what is the {field['label'].lower()}?"
    if field["type"] == "select" and field.get("options"):
        options = ", ".join(option["label"] for option in field["options"][:12])
        base = f"Please choose {field['label'].lower()} ({options})."
    if field["id"] == "jurisdiction_region":
        base = "Which Indian state or union territory should govern this draft? I will not guess the jurisdiction."
    if help_text:
        return f"{base} {help_text}"
    return base


def _extract_region(text: str) -> str | None:
    lowered = text.lower()
    for region in _REGION_HINTS:
        if region.lower() in lowered:
            return region
    return None


def _assign_answer(field: dict[str, Any], message: str, values: dict[str, Any]) -> None:
    text = (message or "").strip()
    if not text:
        return
    field_id = field["id"]
    field_type = field["type"]
    if field_id == "jurisdiction_region":
        region = _extract_region(text)
        if region:
            values[field_id] = region
            return
        # Accept exact option match
        for option in field.get("options") or []:
            if option["value"].lower() == text.lower() or option["label"].lower() == text.lower():
                values[field_id] = option["value"]
                return
        values[field_id] = text
        return
    if field_type == "checkbox":
        values[field_id] = text.lower() in {"yes", "y", "true", "mutual", "include", "ok"}
        return
    if field_type == "select":
        for option in field.get("options") or []:
            if option["value"].lower() == text.lower() or option["label"].lower() in text.lower():
                values[field_id] = option["value"]
                return
        values[field_id] = text
        return
    if field_type in {"number", "currency"}:
        match = re.search(r"[\d,.]+", text.replace(",", ""))
        if match:
            try:
                values[field_id] = float(match.group(0)) if "." in match.group(0) else int(match.group(0))
            except ValueError:
                values[field_id] = text
        else:
            values[field_id] = text
        return
    if field_type == "date":
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        values[field_id] = match.group(0) if match else text
        return
    values[field_id] = text


def _seed_from_message(template_id: str, message: str, values: dict[str, Any]) -> None:
    region = _extract_region(message)
    if region:
        values["jurisdiction_region"] = region
    values.setdefault("jurisdiction_country", "IN")
    # Soft seed purpose-like free text from the original request when present.
    purpose_fields = [field for field in get_template(template_id)["fields"] if field["id"] in {"purpose", "facts", "duties", "business_nature", "goods_description", "scope"}]
    if purpose_fields and purpose_fields[0]["id"] not in values:
        cleaned = re.sub(r"\s+", " ", message).strip()
        if len(cleaned) > 40:
            values[purpose_fields[0]["id"]] = cleaned[:500]


def process_document_turn(message: str, prior: dict[str, Any] | None = None) -> DocumentDraftResult:
    """Return pass to fall through to legal Q&A interview when not drafting."""
    prior = prior if isinstance(prior, dict) and prior.get("mode") == "document_drafting" else None

    if prior and prior.get("unsupported"):
        return DocumentDraftResult("pass", "", {})

    if prior is None:
        if not looks_like_document_request(message):
            return DocumentDraftResult("pass", "", {})
        if _UNSUPPORTED.search(message) and not detect_template_id(message):
            state = _empty_state(None, message)
            state["unsupported"] = True
            return DocumentDraftResult(
                "unsupported",
                "ChatLaw can draft from its supported templates (for example NDA, lease, employment, "
                "partnership, sale, MoU, affidavit, notice, authorization letter, and complaints). "
                "That document type is not supported yet. You can open Research for legal sources, "
                "or pick the closest template under Documents.",
                state,
            )
        template_id = detect_template_id(message)
        if template_id is None or template_id not in TEMPLATES:
            state = _empty_state(None, message)
            state["unsupported"] = True
            return DocumentDraftResult(
                "unsupported",
                "I recognized a document request, but not a supported template. "
                "Try naming a supported type such as NDA, rent agreement, employment agreement, "
                "partnership agreement, sale agreement, or MoU.",
                state,
            )
        state = _empty_state(template_id, message)
        _seed_from_message(template_id, message, state["values"])
    else:
        state = {
            "mode": "document_drafting",
            "template_id": prior.get("template_id"),
            "values": dict(prior.get("values") or {"jurisdiction_country": "IN"}),
            "asked": list(prior.get("asked") or []),
            "round": int(prior.get("round") or 0),
            "max_rounds": int(prior.get("max_rounds") or MAX_ROUNDS),
            "original_query": prior.get("original_query") or "",
            "unsupported": False,
            "pending_field": prior.get("pending_field"),
        }
        template_id = state["template_id"]
        if not template_id or template_id not in TEMPLATES:
            return DocumentDraftResult("pass", "", {})
        pending_id = state.get("pending_field")
        if pending_id:
            fields = {field["id"]: field for field in get_template(template_id)["fields"]}
            field = fields.get(pending_id)
            if field:
                _assign_answer(field, message, state["values"])

    assert template_id
    missing = _missing_required(template_id, state["values"])
    if not missing or state["round"] >= state["max_rounds"]:
        # If still missing jurisdiction after max rounds, keep asking for it.
        still = _missing_required(template_id, state["values"])
        jurisdiction_missing = [field for field in still if field["id"] in {"jurisdiction_region", "jurisdiction_country"}]
        if jurisdiction_missing:
            field = jurisdiction_missing[0]
            state["pending_field"] = field["id"]
            if field["id"] not in state["asked"]:
                state["asked"].append(field["id"])
            state["round"] = int(state["round"]) + 1
            title = get_template(template_id)["title"]
            return DocumentDraftResult(
                "clarify",
                f"Drafting a {title}. {_question_for_field(field)}",
                state,
            )
        state["pending_field"] = None
        state["missing_optional"] = _optional_missing(template_id, state["values"])
        title = get_template(template_id)["title"]
        return DocumentDraftResult(
            "ready",
            f"I have the required details for a {title} draft. Opening your document workspace to generate it now.",
            state,
        )

    field = missing[0]
    state["pending_field"] = field["id"]
    if field["id"] not in state["asked"]:
        state["asked"].append(field["id"])
    state["round"] = int(state["round"]) + 1
    title = get_template(template_id)["title"]
    return DocumentDraftResult(
        "clarify",
        f"Drafting a {title}. {_question_for_field(field)}",
        state,
    )
