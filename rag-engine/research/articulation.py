"""Model-written explanations, grounded only in text ChatLaw already holds.

`articulate_law` explains retrieved statute text; `summarize_judgment` reads
the official judgment downloaded during verification. Neither prompt lets the
model add law or facts that are not in the supplied text.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from .discovery import parse_json_payload
from .store import Provision

TextGenerator = Callable[[str], str]

_LIST_FIELDS = ("elements", "key_points", "consequences", "exceptions", "related_provisions",
                "practical_steps")


def _as_list(value: Any, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip()[:600] for item in value if str(item).strip()][:limit]


def build_articulation_prompt(question: str, provisions: Sequence[Provision]) -> str:
    sources = "\n\n".join(
        f"[{index}] {provision.label} — {provision.act_title}"
        f"{f' (corresponds to repealed {provision.translated_from})' if provision.translated_from else ''}\n"
        f"{provision.text[:4000]}"
        for index, provision in enumerate(provisions, 1)
    )
    return f"""You are an Indian legal research assistant. Explain the law below for a researcher.

Research question:
{question}

Statutory text (the only source you may rely on):
{sources}

Rules:
- Use only the statutory text above. Do not add sections, case law, or facts that are not in it.
- Cite provisions exactly as labelled above, e.g. "Section 85, BNS, 2023".
- Write in clear, plain English. Do not give personal legal advice.

Return ONLY a JSON object:
{{"overview": "3-5 sentence plain-language explanation of what the law says on the question",
  "elements": ["each ingredient or condition that must be satisfied"],
  "key_points": ["important definitions, thresholds, time limits, or procedural requirements"],
  "consequences": ["punishments, penalties, remedies or reliefs provided"],
  "exceptions": ["exceptions, defences, provisos"],
  "related_provisions": ["other sections referred to in the text"],
  "practical_steps": ["neutral next steps a person researching this would usually take"],
  "case_search_topic": "one sentence describing the legal issue to search judgments for"}}
Use [] for lists with nothing to say."""


def articulate_law(question: str, provisions: Sequence[Provision], generate: TextGenerator) -> dict[str, Any] | None:
    if not provisions:
        return None
    payload = parse_json_payload(generate(build_articulation_prompt(question, provisions)))
    if not isinstance(payload, dict) or not str(payload.get("overview", "")).strip():
        return None
    result: dict[str, Any] = {"overview": str(payload["overview"]).strip()[:2000]}
    for name in _LIST_FIELDS:
        result[name] = _as_list(payload.get(name))
    topic = str(payload.get("case_search_topic") or "").strip()
    result["case_search_topic"] = topic[:400] or None
    result["sources"] = [provision.label for provision in provisions]
    return result


def build_judgment_prompt(title: str, court: str, text: str) -> str:
    return f"""Summarize this Indian court judgment for a legal researcher.

Case: {title} — {court}

Judgment text (may be truncated):
{text}

Rules:
- Use only the judgment text above. If something is not in the text, leave it out.
- Be precise about what the court decided and why.

Return ONLY a JSON object:
{{"facts": "2-4 sentences",
  "issues": ["questions the court decided"],
  "arguments": ["main submissions, one per side if stated"],
  "held": "what the court held",
  "ratio": "the legal principle the decision stands for",
  "provisions_applied": ["statutory provisions the court applied"],
  "outcome": "final order / disposition",
  "significance": "one sentence on why this judgment matters"}}"""


def summarize_judgment(title: str, court: str, text: str, generate: TextGenerator) -> dict[str, Any] | None:
    if len(text.strip()) < 400:
        return None
    payload = parse_json_payload(generate(build_judgment_prompt(title, court, text[:60000])))
    if not isinstance(payload, dict) or not str(payload.get("held", "")).strip():
        return None
    summary: dict[str, Any] = {}
    for name in ("facts", "held", "ratio", "outcome", "significance"):
        summary[name] = str(payload.get(name) or "").strip()[:3000] or None
    for name in ("issues", "arguments", "provisions_applied"):
        summary[name] = _as_list(payload.get(name), limit=10)
    return summary
