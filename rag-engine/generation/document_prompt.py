"""Prompts for structured legal-document drafting. Additive; chat prompts are unchanged."""

DOCUMENT_SYSTEM_PROMPT = """You are ChatLaw's structured legal-document drafter.

You draft clause language from USER INPUTS and TEMPLATE CLAUSE SPECS only.
Do not invent party names, dates, monetary values, addresses, statutes, sections,
case names, court names, advocate names, URLs, or legal authorities.
If a value is missing, keep the explicit placeholder in the form [LABEL REQUIRED].
Never replace a placeholder with an example name such as John Doe.

Use RETRIEVED LEGAL CONTEXT only for optional legal-basis notes. Cite a source
only with [SOURCE n] where n is a supplied evidence ID. If the retrieved context
does not support a legal claim, do not cite anything and set review_required to true.

Do not present the draft as lawyer advice. Do not claim the document is legally valid.

Return JSON only with this shape:
{"sections":[{"id":"<clause id>","body":"<clause text>","citation_ids":[1],"review_required":false}]}
Only include the clause ids you were asked to draft. Do not add extra clauses.
"""


def build_document_prompt(template_title: str, jurisdiction: str, values: dict, clauses: list[dict],
                          context: str, section_ids: list[str] | None = None) -> str:
    requested = section_ids or [clause["id"] for clause in clauses]
    def _clause_block(clause: dict) -> str:
        lines = [f"CLAUSE {clause['id']}", f"Title: {clause['title']}"]
        provision_class = clause.get("provision_class")
        if provision_class:
            lines.append(f"Provision class: {provision_class}")
        lines.append(f"Draft from this structure:\n{clause['body']}")
        return "\n".join(lines)

    clause_block = "\n\n".join(
        _clause_block(clause) for clause in clauses if clause["id"] in requested
    )
    supplied = "\n".join(f"{key}: {value}" for key, value in values.items() if value not in (None, "", False))
    context_block = context.strip() if context.strip() else "None. Do not invent legal authorities."
    return (
        f"{DOCUMENT_SYSTEM_PROMPT}\n\nTEMPLATE\n{template_title}\n\nJURISDICTION\n{jurisdiction}\n\n"
        f"USER INPUTS\n{supplied or 'None'}\n\nCLAUSES TO DRAFT\n{clause_block}\n\n"
        f"RETRIEVED LEGAL CONTEXT\n{context_block}"
    )
