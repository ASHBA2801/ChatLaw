"""Document template, validation, generation, and API tests. Gemini is never called."""

from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from api.main import app
from api.routes.search import get_service
from documents.assembler import assemble_document
from documents.conditions import clause_is_active
from documents.templates import TEMPLATES, get_template, list_templates
from documents.validation import active_clauses, validate_values
from generation.document import generate_structured_document
from retrieval.models import RetrievalResponse, RetrievalResult

AUTH = {"Authorization": "Bearer test-secret"}


@pytest.fixture(autouse=True)
def api_test_environment(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    from api import main
    main._rate_limit.clear()


def nda_values(**overrides):
    values = {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Karnataka",
        "governing_law_seat": "Bengaluru",
        "disclosing_party_name": "Acme Research Pvt Ltd",
        "disclosing_party_type": "company",
        "disclosing_party_address": "1 MG Road, Bengaluru",
        "receiving_party_name": "Beta Advisors LLP",
        "receiving_party_type": "firm",
        "receiving_party_address": "2 Brigade Road, Bengaluru",
        "purpose": "Evaluating a possible software engagement",
        "effective_date": "2026-08-20",
        "duration_months": 24,
        "exclude_public_info": True,
        "include_non_solicit": False,
        "dispute_resolution": "arbitration",
    }
    values.update(overrides)
    return values


def fake_result():
    return RetrievalResult(
        "chunk-1", "doc-1", "THE INDIAN CONTRACT ACT, 1872",
        "All agreements are contracts if they are made by the free consent of parties competent to contract.",
        "10", None, None, None, 12, 1, 0.91, {},
        source_name="Contract Act source",
    )


class FakeService:
    def __init__(self, results=(), generator=None):
        self.results = tuple(results)
        self.generator = generator
        self.search_queries = []

    def close(self):
        pass

    def search(self, query, top_k, min_similarity):
        self.search_queries.append(query)
        return RetrievalResponse(self.results, not self.results, 0.01, 0.02)

    def generate_document(self, template_id, values, *, use_model=True, section_ids=None, top_k=8, min_similarity=0.6):
        generator = self.generator if use_model else None
        return generate_structured_document(
            template_id, values, searcher=self, generator=generator,
            top_k=top_k, min_similarity=min_similarity, section_ids=section_ids,
        )

    def revise_document(self, template_id, values, sections, instruction, *,
                        target_section_ids=None, use_model=True, top_k=8, min_similarity=0.6):
        from generation.document_edit import revise_structured_document
        generator = self.generator if use_model else None
        return revise_structured_document(
            template_id, values, sections, instruction,
            searcher=self, generator=generator,
            top_k=top_k, min_similarity=min_similarity,
            target_section_ids=target_section_ids,
        )

    def selection_edit(self, *, selected_text, action, surrounding_section, document_title,
                       jurisdiction, custom_instruction="", language="en", use_model=True):
        from generation.document_edit import edit_document_selection
        generator = self.generator if use_model else None
        return edit_document_selection(
            selected_text=selected_text,
            action=action,
            surrounding_section=surrounding_section,
            document_title=document_title,
            jurisdiction=jurisdiction,
            custom_instruction=custom_instruction,
            language=language,
            generator=generator,
        )


def test_registry_exposes_only_implemented_templates():
    ids = {item["id"] for item in list_templates()}
    assert ids == {
        "nda",
        "service_agreement",
        "rent_lease",
        "rental_agreement_tamil_nadu",
        "affidavit",
        "legal_notice",
        "authorization_letter",
        "consumer_complaint",
        "complaint",
        "employment_agreement",
        "partnership_agreement",
        "sale_agreement",
        "mou",
        "sale_deed",
        "general_power_of_attorney",
        "special_power_of_attorney",
        "gift_deed",
        "release_deed",
        "commercial_lease",
        "leave_license",
        "loan_agreement",
        "rti_application",
        "legal_aid_application",
        "payment_demand_notice",
        "eviction_notice",
        "founder_agreement",
        "name_change_affidavit",
        "indemnity_bond",
    }
    assert "power_of_attorney" not in TEMPLATES


def test_assembled_sections_include_provision_class():
    assembled = assemble_document(get_template("employment_agreement"), {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Karnataka",
        "employer_name": "Acme",
        "employer_type": "company",
        "employer_address": "1 Road",
        "employee_name": "Riya",
        "employee_type": "individual",
        "employee_address": "2 Road",
        "job_title": "Engineer",
        "duties": "Build products",
        "effective_date": "2026-08-20",
    })
    by_id = {section["id"]: section for section in assembled["sections"]}
    assert by_id["parties"]["provision_class"] == "required"
    assert by_id["recitals"]["provision_class"] == "recommended"


def test_required_fields_block_generation():
    template = get_template("nda")
    result = validate_values(template, {"jurisdiction_country": "IN"})
    assert result["can_generate"] is False
    assert any(issue["field_id"] == "disclosing_party_name" for issue in result["blocking"])


def test_optional_and_recommended_fields_are_distinguished():
    template = get_template("nda")
    result = validate_values(template, nda_values(exclude_public_info=False, dispute_resolution=""))
    assert result["can_generate"] is True
    codes = {issue["field_id"] for issue in result["issues"] if issue["level"] == "recommended"}
    assert "dispute_resolution" in codes


def test_invalid_date_and_amount():
    template = get_template("service_agreement")
    values = {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Delhi",
        "client_name": "A",
        "client_type": "company",
        "client_address": "Address",
        "provider_name": "B",
        "provider_type": "individual",
        "provider_address": "Address",
        "purpose": "Advisory work",
        "effective_date": "2026-13-40",
        "fee_amount": "not-a-number",
    }
    result = validate_values(template, values)
    fields = {issue["field_id"] for issue in result["blocking"]}
    assert "effective_date" in fields
    assert "fee_amount" in fields


def test_end_date_cannot_precede_start_date():
    template = get_template("rent_lease")
    values = {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Maharashtra",
        "property_use": "residential",
        "landlord_name": "Owner",
        "landlord_type": "individual",
        "landlord_address": "A",
        "tenant_name": "Tenant",
        "tenant_type": "individual",
        "tenant_address": "B",
        "property_address": "Pune",
        "effective_date": "2026-08-20",
        "end_date": "2026-08-01",
    }
    result = validate_values(template, values)
    assert any(issue["field_id"] == "end_date" for issue in result["blocking"])


def test_conditional_clauses():
    template = get_template("nda")
    without = active_clauses(template, nda_values(include_non_solicit=False, exclude_public_info=False))
    with_optional = active_clauses(template, nda_values(include_non_solicit=True, exclude_public_info=True))
    assert "non_solicit" not in {clause["id"] for clause in without}
    assert "exclusions" not in {clause["id"] for clause in without}
    assert "non_solicit" in {clause["id"] for clause in with_optional}
    assert "exclusions" in {clause["id"] for clause in with_optional}
    assert clause_is_active({"has_value": "fee_amount"}, {"fee_amount": 1000})
    assert not clause_is_active({"has_value": "fee_amount"}, {"fee_amount": ""})


def test_assembler_uses_placeholders_instead_of_inventing_values():
    document = assemble_document(get_template("service_agreement"), {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Delhi",
        "client_name": "Northwind",
        "client_type": "company",
        "client_address": "Delhi",
        "provider_name": "Contoso",
        "provider_type": "individual",
        "provider_address": "Delhi",
        "purpose": "Bookkeeping",
        "effective_date": "2026-08-20",
    })
    bodies = "\n".join(section["body"] for section in document["sections"])
    assert "Northwind" in bodies
    assert "John Doe" not in bodies
    assert "[FEE AMOUNT REQUIRED]" not in bodies
    assert "fees" not in {section["id"] for section in document["sections"]}
    assert document["jurisdiction_region"] == "Delhi"


def test_missing_optional_payment_keeps_placeholder_out_by_skipping_clause():
    generated = generate_structured_document("service_agreement", {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Delhi",
        "client_name": "Northwind",
        "client_type": "company",
        "client_address": "Delhi",
        "provider_name": "Contoso",
        "provider_type": "individual",
        "provider_address": "Delhi",
        "purpose": "Bookkeeping",
        "effective_date": "2026-08-20",
        "termination_notice_days": 30,
    }, searcher=None, generator=None)
    ids = {section["id"] for section in generated["document"]["sections"]}
    assert "termination" in ids
    assert "fees" not in ids
    assert generated["generation"]["used"] is False


def test_placeholder_protection_and_invalid_citation_mapping():
    def generator(prompt):
        return SimpleNamespace(answer='{"sections":[{"id":"governing_law","body":"Governed by invented Section 99 of a fake Act [SOURCE 99]. Party: John Doe.","citation_ids":[99],"review_required":false}]}', model="mock", latency_seconds=0.01)

    generated = generate_structured_document("nda", nda_values(), searcher=FakeService([fake_result()]), generator=generator)
    section = next(item for item in generated["document"]["sections"] if item["id"] == "governing_law")
    assert "99" not in section["citation_ids"]
    assert all(item["id"] != 99 for item in generated["document"]["citations"])
    assert generated["invalid_citations"] == [99]


def test_verified_citation_is_retained():
    def generator(prompt):
        return SimpleNamespace(answer='{"sections":[{"id":"governing_law","body":"Consideration and competence are discussed in the retrieved source [SOURCE 1].","citation_ids":[1],"review_required":false}]}', model="mock", latency_seconds=0.01)

    generated = generate_structured_document("nda", nda_values(), searcher=FakeService([fake_result()]), generator=generator)
    section = next(item for item in generated["document"]["sections"] if item["id"] == "governing_law")
    assert section["citation_ids"] == [1]
    assert section["legal_basis"][0]["section"] == "10"


def test_no_context_marks_jurisdiction_review_without_inventing_sources():
    generated = generate_structured_document("rent_lease", {
        "jurisdiction_country": "IN",
        "jurisdiction_region": "Tamil Nadu",
        "property_use": "residential",
        "landlord_name": "Owner",
        "landlord_type": "individual",
        "landlord_address": "Chennai",
        "tenant_name": "Tenant",
        "tenant_type": "individual",
        "tenant_address": "Chennai",
        "property_address": "T Nagar",
        "effective_date": "2026-08-20",
        "end_date": "2027-08-19",
    }, searcher=FakeService(), generator=None)
    assert generated["retrieval"]["no_relevant_context"] is True
    assert generated["document"]["citations"] == []
    governing = next(item for item in generated["document"]["sections"] if item["id"] == "governing_law")
    assert governing["review_required"] is True
    assert any(warning["code"] == "no_legal_context" for warning in generated["document"]["warnings"])


def test_section_regeneration_returns_only_requested_clause():
    generated = generate_structured_document("nda", nda_values(), searcher=None, generator=None, section_ids=["term"])
    assert [section["id"] for section in generated["document"]["sections"]] == ["term"]


def test_api_requires_auth_for_document_generation():
    with TestClient(app) as client:
        response = client.post("/api/documents/generate", json={"template_id": "nda", "values": nda_values()})
    assert response.status_code == 401


def test_api_generate_and_regenerate_with_mock(monkeypatch):
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            missing = client.post("/api/documents/generate", json={"template_id": "nda", "values": {}, "use_model": False}, headers=AUTH)
            assert missing.status_code == 422
            created = client.post("/api/documents/generate", json={"template_id": "nda", "values": nda_values(), "use_model": False}, headers=AUTH)
            assert created.status_code == 200
            assert created.json()["document"]["template_id"] == "nda"
            regenerated = client.post("/api/documents/regenerate", json={"template_id": "nda", "values": nda_values(), "section_id": "term", "use_model": False}, headers=AUTH)
            assert regenerated.status_code == 200
            assert regenerated.json()["document"]["sections"][0]["id"] == "term"
            unknown = client.post("/api/documents/generate", json={"template_id": "power_of_attorney", "values": nda_values(), "use_model": False}, headers=AUTH)
            assert unknown.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_templates_endpoint_lists_implemented_types():
    with TestClient(app) as client:
        response = client.get("/api/documents/templates", headers=AUTH)
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["templates"]} == {
        "nda",
        "service_agreement",
        "rent_lease",
        "rental_agreement_tamil_nadu",
        "affidavit",
        "legal_notice",
        "authorization_letter",
        "consumer_complaint",
        "complaint",
        "employment_agreement",
        "partnership_agreement",
        "sale_agreement",
        "mou",
        "sale_deed",
        "general_power_of_attorney",
        "special_power_of_attorney",
        "gift_deed",
        "release_deed",
        "commercial_lease",
        "leave_license",
        "loan_agreement",
        "rti_application",
        "legal_aid_application",
        "payment_demand_notice",
        "eviction_notice",
        "founder_agreement",
        "name_change_affidavit",
        "indemnity_bond",
    }


def test_revise_applies_section_patch_without_stripping_required_body():
    assembled = assemble_document(get_template("nda"), nda_values())
    sections = assembled["sections"]

    def fake_generator(prompt: str):
        return SimpleNamespace(answer='{"sections":[{"id":"term","body":"","review_required":false}],"notes":"cleared"}', model="fake", latency_seconds=0.01)

    from generation.document_edit import revise_structured_document
    result = revise_structured_document(
        "nda", nda_values(), sections, "Clear the term clause",
        searcher=FakeService(), generator=fake_generator,
    )
    assert result["ok"] is True
    term = next(item for item in result["document"]["sections"] if item["id"] == "term")
    assert term["body"].strip()  # empty body rejected; original restored
    assert any(warning["code"] == "required_clause_empty" for warning in result["warnings"])


def test_selection_edit_explain_returns_no_suggestion():
    from generation.document_edit import edit_document_selection

    def fake_generator(prompt: str):
        return SimpleNamespace(
            answer='{"suggestion":"should be ignored","explanation":"This sets the term.","preserves_citations":true}',
            model="fake",
            latency_seconds=0.01,
        )

    result = edit_document_selection(
        selected_text="The term is 24 months.",
        action="explain",
        surrounding_section={"id": "term", "title": "Term", "body": "The term is 24 months.", "required": True},
        document_title="NDA",
        jurisdiction="India — Karnataka",
        generator=fake_generator,
    )
    assert result["ok"] is True
    assert result["suggestion"] == ""
    assert "term" in result["explanation"].lower() or result["explanation"]


def test_api_revise_and_selection_edit(monkeypatch):
    def fake_generator(prompt: str):
        if "SELECTED TEXT" in prompt:
            return SimpleNamespace(
                answer='{"suggestion":"The confidentiality period is thirty days.","explanation":"Simplified.","preserves_citations":true}',
                model="fake",
                latency_seconds=0.01,
            )
        return SimpleNamespace(
            answer='{"sections":[{"id":"term","body":"Confidentiality lasts 30 days after the last disclosure.","review_required":false}],"notes":"Updated term"}',
            model="fake",
            latency_seconds=0.01,
        )

    service = FakeService(generator=fake_generator)
    app.dependency_overrides[get_service] = lambda: service
    assembled = assemble_document(get_template("nda"), nda_values())
    try:
        with TestClient(app) as client:
            revised = client.post("/api/documents/revise", json={
                "template_id": "nda",
                "values": nda_values(),
                "sections": assembled["sections"],
                "instruction": "Make the termination period 30 days.",
            }, headers=AUTH)
            assert revised.status_code == 200
            assert revised.json()["proposal_only"] is True
            term = next(item for item in revised.json()["document"]["sections"] if item["id"] == "term")
            assert "30" in term["body"]

            selection = client.post("/api/documents/selection-edit", json={
                "selected_text": "Confidentiality lasts 24 months.",
                "action": "simplify",
                "surrounding_section": {"id": "term", "title": "Term", "body": "Confidentiality lasts 24 months.", "required": True},
                "document_title": "NDA",
                "jurisdiction": "India — Karnataka",
            }, headers=AUTH)
            assert selection.status_code == 200
            assert "thirty" in selection.json()["suggestion"].lower() or "30" in selection.json()["suggestion"]
    finally:
        app.dependency_overrides.clear()
