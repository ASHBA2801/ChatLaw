"""Structured legal-document generation using existing retrieval and evidence."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Mapping

from context.builder import build_context
from documents.assembler import DISCLAIMER, assemble_document
from documents.templates import get_template
from documents.validation import (
    active_clauses,
    placeholder_for,
    unresolved_critical_placeholders,
    validate_values,
)
from generation.document_prompt import build_document_prompt
from verification.evidence import Evidence, validate_citations

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
STATUTE_CLAIM_RE = re.compile(r"\b(?:section|sec\.?)\s+[0-9]+[a-z]?\b", re.IGNORECASE)
COURT_CLAIM_RE = re.compile(r"\b(?:Supreme Court|High Court|District Court|Sessions Court)\b")


def _parse_model_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = JSON_RE.search(text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _legal_basis(source: Evidence) -> dict[str, Any]:
    label = source.document_title
    if source.section_number:
        label = f"{source.document_title} — Section {source.section_number}"
    return {
        "citation_id": source.citation_id,
        "label": label,
        "document": source.document_title,
        "section": source.section_number,
        "chunk_id": source.chunk_id,
    }


def _apply_citations(body: str, evidence: tuple[Evidence, ...]) -> tuple[str, list[int], list[int]]:
    validation = validate_citations(body, evidence)
    return validation.normalized_answer.strip(), list(validation.valid_ids), list(validation.invalid_ids)


def _flag_ungrounded_claims(body: str, valid_ids: list[int]) -> bool:
    if valid_ids:
        return False
    return bool(STATUTE_CLAIM_RE.search(body) or COURT_CLAIM_RE.search(body))


def _restore_supplied_values(body: str, template, values: Mapping[str, Any], assembled_body: str) -> str:
    """Reject invented replacements of known placeholders."""
    for field in template["fields"]:
        placeholder = placeholder_for(field)
        supplied = values.get(field["id"])
        empty = supplied in (None, "", False)
        if empty and placeholder in assembled_body and placeholder not in body:
            body = f"{body.rstrip()}\n\n{placeholder}"
        if not empty and isinstance(supplied, str) and supplied.strip() and supplied.strip() not in body:
            if placeholder in assembled_body:
                continue
    return body


def _merge_model_sections(assembled: dict[str, Any], model_payload: dict[str, Any], evidence: tuple[Evidence, ...],
                          template, values: Mapping[str, Any]) -> tuple[dict[str, Any], list[int]]:
    by_id = {section["id"]: section for section in assembled["sections"]}
    invalid_all: list[int] = []
    for item in model_payload.get("sections") or []:
        section_id = item.get("id")
        if section_id not in by_id or not isinstance(item.get("body"), str):
            continue
        body, valid_ids, invalid_ids = _apply_citations(item["body"], evidence)
        invalid_all.extend(invalid_ids)
        original = by_id[section_id]
        body = _restore_supplied_values(body, template, values, original["body"])
        review = bool(item.get("review_required")) or original["needs_legal_context"]
        if _flag_ungrounded_claims(body, valid_ids):
            review = True
        original["body"] = body
        original["citation_ids"] = valid_ids
        original["legal_basis"] = [_legal_basis(source) for source in evidence if source.citation_id in valid_ids]
        original["review_required"] = review or not valid_ids and original["needs_legal_context"]
    assembled["citations"] = [source.citation_dict() for source in evidence
                              if any(source.citation_id in section["citation_ids"]
                                     for section in assembled["sections"])]
    return assembled, list(dict.fromkeys(invalid_all))


def _attach_empty_legal_review(assembled: dict[str, Any]) -> None:
    for section in assembled["sections"]:
        if section["needs_legal_context"]:
            section["review_required"] = True


def validate_generated_document(template, values: Mapping[str, Any], assembled: dict[str, Any],
                                evidence: tuple[Evidence, ...]) -> dict[str, Any]:
    issues: list[str] = []
    active = {clause["id"] for clause in active_clauses(template, values)}
    present = {section["id"] for section in assembled["sections"]}
    missing_required = [
        clause["id"] for clause in template["clauses"]
        if clause.get("required") and clause["id"] in active and clause["id"] not in present
    ]
    if missing_required:
        issues.append("Missing required clauses: " + ", ".join(missing_required))
    placeholders = unresolved_critical_placeholders(template, values, assembled["sections"])
    if placeholders:
        issues.append("Unresolved required placeholders: " + ", ".join(placeholders))
    known_ids = {source.citation_id for source in evidence}
    fabricated = []
    for section in assembled["sections"]:
        for citation_id in section.get("citation_ids") or []:
            if citation_id not in known_ids:
                fabricated.append(citation_id)
    if fabricated:
        issues.append("Citations do not map to retrieved evidence.")
    order = [clause["id"] for clause in active_clauses(template, values)]
    actual = [section["id"] for section in assembled["sections"] if section["id"] in order]
    expected = [clause_id for clause_id in order if clause_id in actual]
    if actual != expected:
        issues.append("Section order does not match the template.")
    return {"passed": not issues, "issues": issues, "placeholders": placeholders}


def generate_structured_document(
    template_id: str,
    values: Mapping[str, Any],
    *,
    searcher=None,
    generator: Callable[[str], Any] | None = None,
    top_k: int = 8,
    min_similarity: float = 0.6,
    section_ids: list[str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    template = get_template(template_id)
    input_validation = validate_values(template, values)
    if not input_validation["can_generate"]:
        return {
            "ok": False,
            "status": "missing_required_fields",
            "validation": input_validation,
            "document": None,
        }
    assembled = assemble_document(template, values)
    evidence: tuple[Evidence, ...] = ()
    retrieval_meta = {"top_k": top_k, "results_used": 0, "no_relevant_context": True}
    context_text = ""
    needs_context = any(section["needs_legal_context"] for section in assembled["sections"]
                        if section_ids is None or section["id"] in section_ids)
    if needs_context and searcher is not None:
        query = template["legal_query"]
        region = values.get("jurisdiction_region")
        if isinstance(region, str) and region.strip():
            query = f"{query} {region.strip()}"
        retrieval = searcher.search(query, top_k=top_k, min_similarity=min_similarity)
        retrieval_meta = {
            "top_k": top_k,
            "results_used": 0 if retrieval.no_relevant_context else len(retrieval.results),
            "no_relevant_context": retrieval.no_relevant_context,
            "embedding_latency_seconds": retrieval.embedding_latency_seconds,
            "database_latency_seconds": retrieval.database_latency_seconds,
        }
        if not retrieval.no_relevant_context:
            built = build_context(retrieval.results)
            evidence = built.sources
            context_text = built.text
            assembled["warnings"].append({
                "code": "legal_context_attached",
                "message": "Verified legal sources were retrieved for jurisdiction-sensitive clauses. Uncited statutory claims are not treated as authority.",
            })
        else:
            assembled["warnings"].append({
                "code": "no_legal_context",
                "message": "No verified legal sources were retrieved. Jurisdiction-specific clauses are marked for review. No statute or case was invented.",
            })
            _attach_empty_legal_review(assembled)
    else:
        _attach_empty_legal_review(assembled)

    generation_meta: dict[str, Any] = {"model": None, "latency_seconds": 0.0, "used": False}
    invalid_citations: list[int] = []
    if generator is not None:
        clauses = [clause for clause in active_clauses(template, values)
                   if section_ids is None or clause["id"] in section_ids]
        filled = []
        by_id = {section["id"]: section for section in assembled["sections"]}
        for clause in clauses:
            filled.append({**clause, "body": by_id[clause["id"]]["body"]})
        jurisdiction = f"India — {values.get('jurisdiction_region')}"
        prompt = build_document_prompt(template["title"], jurisdiction, dict(values), filled, context_text,
                                       section_ids)
        generated = generator(prompt)
        generation_meta = {
            "model": getattr(generated, "model", None),
            "latency_seconds": getattr(generated, "latency_seconds", 0.0),
            "used": True,
        }
        payload = _parse_model_json(getattr(generated, "answer", "") or getattr(generated, "text", "") or str(generated))
        if payload is None:
            assembled["warnings"].append({
                "code": "model_output_rejected",
                "message": "The language model did not return usable structured output. The template draft was kept.",
            })
        else:
            assembled, invalid_citations = _merge_model_sections(assembled, payload, evidence, template, values)
            assembled["model_used"] = True
    else:
        assembled["warnings"].append({
            "code": "model_unused",
            "message": "Clause language was assembled from the selected template. A language model was not used for this draft.",
        })

    if section_ids:
        keep = set(section_ids)
        assembled["sections"] = [section for section in assembled["sections"] if section["id"] in keep]

    output_validation = validate_generated_document(template, values, assembled, evidence)
    if not output_validation["passed"]:
        assembled["warnings"].append({
            "code": "validation_failed",
            "message": "The draft is not marked valid: " + "; ".join(output_validation["issues"]),
        })
    assembled["disclaimer"] = DISCLAIMER
    return {
        "ok": True,
        "status": "generated" if output_validation["passed"] else "generated_with_issues",
        "validation": {"input": input_validation, "output": output_validation},
        "document": assembled,
        "citations": assembled["citations"],
        "evidence": [source.citation_dict() for source in evidence],
        "invalid_citations": invalid_citations,
        "retrieval": retrieval_meta,
        "generation": generation_meta,
        "total_latency_seconds": time.perf_counter() - started,
    }
