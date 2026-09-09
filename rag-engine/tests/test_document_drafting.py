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
    result = process_document_turn("Please draft a will and testament for my property")
    assert result.action == "unsupported"
    assert result.state.get("unsupported") is True


def test_power_of_attorney_is_now_supported():
    result = process_document_turn("Please draft a power of attorney for my mother")
    assert result.action == "clarify"
    assert result.state["template_id"] == "general_power_of_attorney"


def test_multi_entity_extraction_from_prompt():
    prompt = (
        "I need a rental agreement for my flat in Coimbatore. Rent is 18,000 per month, "
        "deposit is 1 Lakh, tenant is Vignesh and landlord is Senthil Kumar for 11 months."
    )
    result = process_document_turn(prompt)
    assert result.action == "clarify"
    assert result.state["template_id"] == "rental_agreement_tamil_nadu"
    vals = result.state["values"]
    assert vals["jurisdiction_region"] == "Tamil Nadu"
    assert vals["governing_law_seat"] == "Coimbatore"
    assert vals["landlord_name"] == "Senthil Kumar"
    assert vals["tenant_name"] == "Vignesh"
    assert vals["rent_amount"] == 18000
    assert vals["deposit_amount"] == 100000
    assert vals["duration_months"] == 11
    # Check that grouped clarification includes recorded summary and asks remaining required fields
    assert "Senthil Kumar" in result.message
    assert "Vignesh" in result.message
    assert "18,000" in result.message


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


def test_multilingual_document_clarification():
    # Tamil drafting turn
    res_ta = process_document_turn("வாடகை ஒப்பந்தம் வேண்டும்", language="ta")
    assert res_ta.action == "clarify"
    assert "உங்களுக்கு" in res_ta.message
    assert "Rental Agreement" in res_ta.message

    # Hindi drafting turn
    res_hi = process_document_turn("Please draft an NDA", language="hi")
    assert res_hi.action == "clarify"
    assert "मैंने पहचाना है" in res_hi.message
