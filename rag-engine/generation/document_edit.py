"""Instruction-based revise and selection-scoped edits for structured documents."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Mapping

from context.builder import build_context
from documents.assembler import DISCLAIMER
from documents.templates import get_template
from generation.document import (
    _flag_ungrounded_claims,
    _merge_model_sections,
    _parse_model_json,
    _restore_supplied_values,
    validate_generated_document,
)
from generation.document_edit_prompt import (
    SELECTION_ACTIONS,
    build_revise_prompt,
    build_selection_prompt,
)
from verification.evidence import Evidence

SOURCE_MARK_RE = re.compile(r"\[SOURCE\s+\d+\]", re.IGNORECASE)


def _citation_markers(text: str) -> set[str]:
    return {match.group(0).upper() for match in SOURCE_MARK_RE.finditer(text or "")}


def _guard_required_sections(
    current_sections: list[dict[str, Any]],
    proposed_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for section in current_sections:
        if not section.get("required"):
            continue
        proposed = proposed_by_id.get(section["id"])
        if proposed is None:
            continue
        body = (proposed.get("body") or "").strip()
        if not body:
            warnings.append({
                "code": "required_clause_empty",
                "message": f"Required clause “{section.get('title') or section['id']}” cannot be emptied by AI revise.",
            })
            proposed["body"] = section.get("body") or ""
            continue
        before = _citation_markers(section.get("body") or "")
        after = _citation_markers(body)
        removed = before - after
        if removed and section.get("needs_legal_context"):
            warnings.append({
                "code": "citations_stripped",
                "message": (
                    f"AI revise tried to remove citation markers from “{section.get('title') or section['id']}”. "
                    "Original markers were restored."
                ),
            })
            # Re-append missing markers at end rather than inventing new ones.
            suffix = " ".join(sorted(removed))
            proposed["body"] = f"{body.rstrip()} {suffix}".strip()
    return warnings


def revise_structured_document(
    template_id: str,
    values: Mapping[str, Any],
    sections: list[dict[str, Any]],
    instruction: str,
    *,
    searcher=None,
    generator: Callable[[str], Any] | None = None,
    top_k: int = 8,
    min_similarity: float = 0.6,
    target_section_ids: list[str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    instruction = (instruction or "").strip()
    if not instruction:
        return {"ok": False, "status": "missing_instruction", "document": None, "warnings": [
            {"code": "missing_instruction", "message": "An instruction is required to revise the document."}
        ]}
    if not sections:
        return {"ok": False, "status": "missing_sections", "document": None, "warnings": [
            {"code": "missing_sections", "message": "Current document sections are required."}
        ]}

    template = get_template(template_id)
    current = {
        "template_id": template_id,
        "title": values.get("document_title") or template["document_type"],
        "document_type": template["document_type"],
        "jurisdiction_country": values.get("jurisdiction_country") or "IN",
        "jurisdiction_region": values.get("jurisdiction_region") or "",
        "sections": [dict(section) for section in sections],
        "signatures": [],
        "warnings": [{"code": "ai_generated", "message": DISCLAIMER}],
        "citations": [],
        "disclaimer": DISCLAIMER,
    }
    if isinstance(current["title"], str) and not str(current["title"]).strip():
        current["title"] = template["document_type"]

    evidence: tuple[Evidence, ...] = ()
    context_text = ""
    retrieval_meta = {"top_k": top_k, "results_used": 0, "no_relevant_context": True}
    needs_context = any(
        section.get("needs_legal_context") or section.get("required")
        for section in sections
        if target_section_ids is None or section["id"] in target_section_ids
    )
    if needs_context and searcher is not None:
        query = f"{template['legal_query']} {instruction}"
        region = values.get("jurisdiction_region")
        if isinstance(region, str) and region.strip():
            query = f"{query} {region.strip()}"
        retrieval = searcher.search(query, top_k=top_k, min_similarity=min_similarity)
        retrieval_meta = {
            "top_k": top_k,
            "results_used": 0 if retrieval.no_relevant_context else len(retrieval.results),
            "no_relevant_context": retrieval.no_relevant_context,
        }
        if not retrieval.no_relevant_context:
            built = build_context(retrieval.results)
            evidence = built.sources
            context_text = built.text

    if generator is None:
        return {
            "ok": False,
            "status": "model_unavailable",
            "document": None,
            "warnings": [{"code": "model_unused", "message": "Document revise requires the language model."}],
            "retrieval": retrieval_meta,
            "total_latency_seconds": time.perf_counter() - started,
        }

    jurisdiction = f"India — {values.get('jurisdiction_region') or '[STATE REQUIRED]'}"
    prompt = build_revise_prompt(
        template["title"],
        jurisdiction,
        dict(values),
        current["sections"],
        instruction,
        context_text,
        target_section_ids,
    )
    generated = generator(prompt)
    payload = _parse_model_json(getattr(generated, "answer", "") or getattr(generated, "text", "") or str(generated))
    generation_meta = {
        "model": getattr(generated, "model", None),
        "latency_seconds": getattr(generated, "latency_seconds", 0.0),
        "used": True,
    }
    if payload is None:
        return {
            "ok": False,
            "status": "model_output_rejected",
            "document": current,
            "warnings": [{
                "code": "model_output_rejected",
                "message": "The language model did not return usable revise output. No changes were applied.",
            }],
            "retrieval": retrieval_meta,
            "generation": generation_meta,
            "total_latency_seconds": time.perf_counter() - started,
            "proposal_only": True,
        }

    proposed = {section["id"]: dict(section) for section in current["sections"]}
    # Seed merge helpers expect assembled sections list.
    assembled = dict(current)
    assembled["sections"] = [dict(section) for section in current["sections"]]
    assembled, invalid_citations = _merge_model_sections(assembled, payload, evidence, template, values)
    for section in assembled["sections"]:
        original = next((item for item in sections if item["id"] == section["id"]), None)
        if original is None:
            continue
        section["body"] = _restore_supplied_values(
            section["body"], template, values, original.get("body") or ""
        )
        if _flag_ungrounded_claims(section["body"], section.get("citation_ids") or []):
            section["review_required"] = True
        proposed[section["id"]] = section

    guard_warnings = _guard_required_sections(sections, proposed)
    assembled["sections"] = [proposed[section["id"]] for section in sections if section["id"] in proposed]
    assembled["warnings"] = list(current["warnings"]) + guard_warnings
    if payload.get("notes"):
        assembled["warnings"].append({
            "code": "revise_notes",
            "message": str(payload["notes"]),
        })
    assembled["disclaimer"] = DISCLAIMER
    output_validation = validate_generated_document(template, values, assembled, evidence)
    if not output_validation["passed"]:
        assembled["warnings"].append({
            "code": "validation_failed",
            "message": "Revise proposal has issues: " + "; ".join(output_validation["issues"]),
        })

    return {
        "ok": True,
        "status": "proposal",
        "document": assembled,
        "notes": payload.get("notes"),
        "warnings": assembled["warnings"],
        "citations": assembled.get("citations") or [],
        "evidence": [source.citation_dict() for source in evidence],
        "invalid_citations": invalid_citations,
        "retrieval": retrieval_meta,
        "generation": generation_meta,
        "validation": {"output": output_validation},
        "proposal_only": True,
        "total_latency_seconds": time.perf_counter() - started,
    }


def edit_document_selection(
    *,
    selected_text: str,
    action: str,
    surrounding_section: Mapping[str, Any],
    document_title: str,
    jurisdiction: str,
    custom_instruction: str = "",
    language: str = "en",
    generator: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    text = (selected_text or "").strip()
    action = (action or "").strip().lower()
    if not text:
        return {"ok": False, "status": "missing_selection", "suggestion": "", "explanation": "No text was selected."}
    if action not in SELECTION_ACTIONS:
        return {"ok": False, "status": "invalid_action", "suggestion": "", "explanation": "Unsupported selection action."}
    if action == "custom" and not (custom_instruction or "").strip():
        return {"ok": False, "status": "missing_instruction", "suggestion": "", "explanation": "Custom edits need an instruction."}
    if generator is None:
        return {"ok": False, "status": "model_unavailable", "suggestion": "", "explanation": "Selection edit requires the language model."}

    prompt = build_selection_prompt(
        action=action,
        selected_text=text,
        surrounding_section=dict(surrounding_section),
        document_title=document_title,
        jurisdiction=jurisdiction,
        custom_instruction=custom_instruction,
        language=language,
    )
    generated = generator(prompt)
    payload = _parse_model_json(getattr(generated, "answer", "") or getattr(generated, "text", "") or str(generated))
    generation_meta = {
        "model": getattr(generated, "model", None),
        "latency_seconds": getattr(generated, "latency_seconds", 0.0),
        "used": True,
    }
    if payload is None:
        return {
            "ok": False,
            "status": "model_output_rejected",
            "suggestion": "",
            "explanation": "The model did not return usable selection output.",
            "generation": generation_meta,
            "total_latency_seconds": time.perf_counter() - started,
        }

    suggestion = payload.get("suggestion") if isinstance(payload.get("suggestion"), str) else ""
    explanation = payload.get("explanation") if isinstance(payload.get("explanation"), str) else ""
    if action == "explain":
        suggestion = ""
    before = _citation_markers(text)
    after = _citation_markers(suggestion)
    stripped = bool(before - after) if suggestion else False
    if stripped and surrounding_section.get("needs_legal_context"):
        # Restore markers rather than silently drop them.
        suggestion = f"{suggestion.rstrip()} {' '.join(sorted(before - after))}".strip()
        stripped = False
        explanation = (explanation + " Citation markers were preserved.").strip()

    return {
        "ok": True,
        "status": "proposal",
        "suggestion": suggestion,
        "explanation": explanation,
        "preserves_citations": not stripped,
        "proposal_only": True,
        "generation": generation_meta,
        "total_latency_seconds": time.perf_counter() - started,
    }
