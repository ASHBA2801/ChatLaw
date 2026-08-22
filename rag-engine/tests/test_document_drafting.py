"""Deterministic document-drafting intent tests (no Gemini)."""

from conversation.document_drafting import (
    detect_template_id,
    looks_like_document_request,
    process_document_turn,
)


def test_detects_supported_document_intents():
    assert detect_template_id("Please draft an NDA for my startup") == "nda"
    assert detect_template_id("I need a rent agreement") == "rent_lease"
    assert detect_template_id("Create an employment agreement") == "employment_agreement"
    assert detect_template_id("Prepare a partnership deed") == "partnership_agreement"
    assert detect_template_id("Draft a sale agreement") == "sale_agreement"
    assert detect_template_id("Write an MoU") == "mou"


def test_looks_like_document_request():
    assert looks_like_document_request("Please draft an NDA")
    assert not looks_like_document_request("What is section 302 IPC?")


def test_unsupported_document_type():
    result = process_document_turn("Please draft a power of attorney for my mother")
    assert result.action == "unsupported"
    assert result.state.get("unsupported") is True


def test_clarifies_jurisdiction_and_reaches_ready():
    first = process_document_turn("Please draft an authorization letter")
    assert first.action == "clarify"
    assert first.state["template_id"] == "authorization_letter"
    pending = first.state["pending_field"]
    assert pending

    state = first.state
    # Answer fields until ready or we hit jurisdiction repeatedly with concrete answers.
    answers = {
        "jurisdiction_region": "Karnataka",
        "principal_name": "Asha Rao",
        "principal_type": "individual",
        "principal_address": "1 MG Road, Bengaluru",
        "authorized_name": "Ravi Kumar",
        "authorized_type": "individual",
        "authorized_address": "2 Brigade Road, Bengaluru",
        "purpose": "Collect documents from the registrar",
        "scope_of_authority": "Sign and collect certified copies",
        "effective_date": "2026-08-21",
    }
    result = first
    for _ in range(12):
        if result.action != "clarify":
            break
        field = result.state.get("pending_field")
        message = answers.get(field or "", "Karnataka")
        result = process_document_turn(message, result.state)
    assert result.action == "ready"
    assert result.state["values"].get("jurisdiction_country") == "IN"
    assert result.state["values"].get("jurisdiction_region") == "Karnataka"
