"""Prompts for document revise and selection-scoped AI edits."""

from __future__ import annotations

REVISE_SYSTEM_PROMPT = """You are ChatLaw's Indian legal-document reviser.

Apply the USER INSTRUCTION to the CURRENT SECTIONS while preserving authentic Indian legal document structure.
Return JSON only:
{"sections":[{"id":"<existing section id>","body":"<revised full section body>","review_required":false}],"notes":"<short summary of changes>"}

Rules:
- Only include sections you actually change. Do not invent new section ids.
- Maintain formal legal formatting: recitals ("WHEREAS..."), testatum, numbered covenants (1.1, 1.2), prayer clauses, schedules with boundaries, and witness attestation.
- Do not invent party names, dates, amounts, statutes, case names, or authorities.
- Keep [LABEL REQUIRED] placeholders that appear in the current text.
- Preserve [SOURCE n] citation markers that already appear unless the instruction explicitly asks to remove citations.
- Do not delete required legal structure silently. If asked to remove a required clause's substance, refuse in notes and leave the body unchanged.
- Use RETRIEVED LEGAL CONTEXT only for optional legal-basis wording; cite only with [SOURCE n].
- Do not claim the document is legally valid.
"""

SELECTION_SYSTEM_PROMPT = """You are ChatLaw's legal-document selection editor.

Given SELECTED TEXT and an ACTION, return JSON only:
{"suggestion":"<replacement text or empty if explain-only>","explanation":"<brief explanation>","preserves_citations":true}

Rules:
- For action "explain", leave suggestion empty and put the explanation in explanation.
- Do not invent statutes, sections, case names, or authorities.
- Preserve [SOURCE n] markers that appear in the selected text unless the user explicitly asks to remove them; set preserves_citations false only if markers were removed.
- Keep [LABEL REQUIRED] placeholders.
- Do not claim legal validity.
- Match the language requested when translating.
"""

SELECTION_ACTIONS = {
    "improve",
    "simplify",
    "formal",
    "explain",
    "expand",
    "shorten",
    "rewrite",
    "legally_clearer",
    "alternative",
    "translate",
    "custom",
}


def build_revise_prompt(
    template_title: str,
    jurisdiction: str,
    values: dict,
    sections: list[dict],
    instruction: str,
    context: str,
    target_section_ids: list[str] | None = None,
) -> str:
    targets = target_section_ids or [section["id"] for section in sections]
    section_block = "\n\n".join(
        (
            f"SECTION {section['id']}\nTitle: {section.get('title')}\n"
            f"Required: {bool(section.get('required'))}\n"
            f"Provision class: {section.get('provision_class') or 'unknown'}\n"
            f"Body:\n{section.get('body') or ''}"
        )
        for section in sections
        if section["id"] in targets
    )
    supplied = "\n".join(f"{key}: {value}" for key, value in values.items() if value not in (None, "", False))
    context_block = context.strip() if context.strip() else "None. Do not invent legal authorities."
    return (
        f"{REVISE_SYSTEM_PROMPT}\n\nTEMPLATE\n{template_title}\n\nJURISDICTION\n{jurisdiction}\n\n"
        f"USER INPUTS\n{supplied or 'None'}\n\nUSER INSTRUCTION\n{instruction.strip()}\n\n"
        f"CURRENT SECTIONS\n{section_block}\n\nRETRIEVED LEGAL CONTEXT\n{context_block}"
    )


def build_selection_prompt(
    *,
    action: str,
    selected_text: str,
    surrounding_section: dict,
    document_title: str,
    jurisdiction: str,
    custom_instruction: str = "",
    language: str = "en",
) -> str:
    action_line = action
    if action == "custom" and custom_instruction.strip():
        action_line = f"custom: {custom_instruction.strip()}"
    elif action == "translate":
        action_line = f"translate to language code {language}"
    section_meta = (
        f"Section id: {surrounding_section.get('id')}\n"
        f"Section title: {surrounding_section.get('title')}\n"
        f"Required: {bool(surrounding_section.get('required'))}\n"
        f"Full section body:\n{surrounding_section.get('body') or ''}"
    )
    return (
        f"{SELECTION_SYSTEM_PROMPT}\n\nDOCUMENT\n{document_title}\n\nJURISDICTION\n{jurisdiction}\n\n"
        f"ACTION\n{action_line}\n\nSELECTED TEXT\n{selected_text}\n\nSURROUNDING SECTION\n{section_meta}"
    )
