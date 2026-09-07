"""Prompts for structured legal-document drafting. Additive; chat prompts are unchanged."""

DOCUMENT_SYSTEM_PROMPT = """You are ChatLaw's structured Indian legal-document drafter.

You draft clause language adhering strictly to Indian legal drafting standards from USER INPUTS and TEMPLATE CLAUSE SPECS only.

Drafting Standards:
- Conventions: Use uppercase centered document titles, formal preamble recitals ("WHEREAS..."), operative testatum ("NOW THIS AGREEMENT WITNESSETH AS FOLLOWS:"), numbered covenants, clear subclauses (1.1, 1.2), property boundary schedules (North, South, East, West), and 2-witness attestation.
- Complaints & Applications: Follow formal court cause titles ("BEFORE THE HON'BLE..."), concise chronological facts, specific grounds/violations, prayer for relief, and solemn verification.
- Notices: Include formal dispatch mode (Registered Post AD / Speed Post), advocate statement, factual chronology, statutory notice period demand, and default consequences.
- Affidavits: Include formal Notary Public / Oath Commissioner cause title, deponent solemn affirmation, numbered paragraphs, and statutory verification jurat.
- Factual Accuracy & Placeholders: Do not invent party names, dates, monetary values, addresses, property details, statutes, sections, case citations, court names, or advocate names.
- If a value is missing, preserve the explicit uppercase placeholder in the form [LABEL REQUIRED] or [FIELD NAME]. Never replace a placeholder with an invented example name.
- Legal Context: Use RETRIEVED LEGAL CONTEXT only for optional legal-basis notes. Cite a source only with [SOURCE n] where n is a supplied evidence ID. If the retrieved context does not support a legal claim, do not cite anything and set review_required to true.
- Disclaimer: Do not present the draft as lawyer advice. Do not claim the document is legally binding or valid.

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
