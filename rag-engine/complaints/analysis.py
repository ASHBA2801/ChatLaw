"""Read a person's facts into the structure the filing agent works from.

The model reads the facts (who, what, when, where, which official, how much)
and proposes statute searches; the keyword rules in taxonomy.py read the same
facts independently. Flags are OR-ed and the higher severity wins, so a model
miss never hides an escalation route. Statutes come from the embedded corpus
via ResearchService.law — the model never supplies a section number itself.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Sequence

from .taxonomy import (
    FLAG_KEYS,
    KINDS,
    SEVERITIES,
    court_subjects_for,
    merge_severity,
    read_facts,
    recommend,
)

logger = logging.getLogger(__name__)

TextGenerator = Callable[[str], str]
MAX_FACTS_CHARS = 14000
MAX_PROVISIONS = 10


def build_analysis_prompt(facts: str, *, location: str, case_title: str | None) -> str:
    flags = ", ".join(FLAG_KEYS)
    return f"""You help Indian citizens prepare complaints to the police and other authorities.
Read the person's account and return a structured reading of it. Do not give legal advice.

Case title: {case_title or "(none)"}
Location: {location or "(not given)"}

The person's account (and text from their documents):
\"\"\"
{facts[:MAX_FACTS_CHARS]}
\"\"\"

Rules:
- Use only what the account says. Never invent names, dates, amounts or events. Use null when unknown.
- "flags" uses exactly these keys, each true or false: {flags}.
  central_government is true only when the official or body involved belongs to the Central Government,
  a central public sector undertaking, or a nationalised/public sector bank.
- severity is one of {", ".join(SEVERITIES)}:
  low = civil/service grievance; moderate = an ordinary cognizable offence;
  serious = police refusal, bribe demand, violence, cyber fraud, offences against women or children;
  grave = custodial violence, threat to life, murder/rape/kidnapping, corruption by central officials, large inter-State fraud.
- law_search_queries: up to 3 short searches that would find the Indian statutory provisions
  (Bharatiya Nyaya Sanhita 2023, BNSS 2023, special Acts) for the wrongs described — describe the wrong, e.g.
  "cheating by impersonation online", "criminal intimidation threat to kill". Do not write section numbers.
- missing_information: questions whose answers a complaint would need and the account does not give
  (e.g. exact date, accused's address, transaction ID). At most 6, plain language.

Return ONLY a JSON object:
{{"summary": "2-3 sentence neutral summary of what happened",
  "category": "short label, e.g. Online financial fraud",
  "severity": "low|moderate|serious|grave",
  "severity_reason": "one sentence",
  "flags": {{"cognizable_offence": true, "...": false}},
  "incident": {{"date": "as stated or null", "time": "as stated or null", "place": "as stated or null"}},
  "accused": [{{"name": "as stated or null", "description": "role / designation / relationship", "address": "or null"}}],
  "public_servants": [{{"name": "or null", "designation": "...", "department": "..."}}],
  "amount_involved": "e.g. Rs. 45,000 or null",
  "wrongs": ["plain description of each wrong done"],
  "law_search_queries": ["..."],
  "missing_information": ["..."],
  "urgent": "one sentence if immediate action is needed (danger, money just lost), else null"}}"""


def _as_list(value: Any, limit: int = 8, item_limit: int = 400) -> list[Any]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        if isinstance(item, dict):
            out.append({k: (str(v)[:item_limit] if v is not None else None) for k, v in item.items()})
        elif item is not None and str(item).strip():
            out.append(str(item).strip()[:item_limit])
    return out


def _clean(value: Any, limit: int = 600) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:limit] if text and text.lower() not in {"null", "none", "unknown", "n/a"} else None


def provision_dict(provision: Any, citation_id: int) -> dict[str, Any]:
    return {
        "id": citation_id,
        "law_key": provision.law_key,
        "act_id": provision.act_id,
        "act_title": provision.act_title,
        "short_title": provision.short_title,
        "section": provision.section,
        "label": provision.label,
        "text": provision.text[:2500],
        "source_url": provision.source_url,
        "translated_from": provision.translated_from,
    }


def find_provisions(research: Any, queries: Sequence[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Statutory provisions for the wrongs described, from the embedded corpus only."""
    if research is None:
        return [], []
    seen: set[str] = set()
    found: list[Any] = []
    notes: list[str] = []
    for query in [q for q in queries if q and q.strip()][:4]:
        try:
            result = research.law(query, articulate=False)
        except Exception:
            logger.exception("[FILINGS] statute search failed for %r", query)
            continue
        notes.extend(result.notes)
        for provision in result.provisions[:4]:
            if provision.law_key in seen:
                continue
            # A provision without a section number is only useful as context, not as a citation.
            if not provision.section:
                continue
            seen.add(provision.law_key)
            found.append(provision)
    found = found[:MAX_PROVISIONS]
    return [provision_dict(p, index) for index, p in enumerate(found, 1)], list(dict.fromkeys(notes))


def analyze_facts(facts: str, *, location: dict[str, Any] | None = None, case_title: str | None = None,
                  generate: TextGenerator | None = None, research: Any = None) -> dict[str, Any]:
    facts = (facts or "").strip()
    if len(facts) < 20:
        raise ValueError("Describe what happened in a few sentences before drafting a complaint.")
    location = location or {}
    location_text = ", ".join(str(location[k]) for k in ("locality", "city", "district", "state")
                              if location.get(k))
    rules = read_facts(facts)
    model: dict[str, Any] = {}
    model_used = False
    if generate is not None:
        try:
            from research.discovery import parse_json_payload

            payload = parse_json_payload(generate(build_analysis_prompt(facts, location=location_text,
                                                                        case_title=case_title)))
            if isinstance(payload, dict):
                model, model_used = payload, True
        except Exception:
            logger.exception("[FILINGS] analysis model failed; using rule-based reading")

    model_flags = model.get("flags") if isinstance(model.get("flags"), dict) else {}
    flags = {key: bool(rules.flags.get(key)) or model_flags.get(key) is True for key in FLAG_KEYS}
    # The rules are deliberately conservative about Central Government involvement;
    # only the model's reading (which saw the whole account) can add it.
    flags["central_government"] = bool(model_flags.get("central_government")) if model_used \
        else rules.flags["central_government"]
    severity = merge_severity(rules.severity, model.get("severity") if model.get("severity") in SEVERITIES else None)
    subjects = court_subjects_for(flags)
    recommendations = recommend(flags, severity, subjects)

    queries = [q for q in _as_list(model.get("law_search_queries"), 3) if isinstance(q, str)]
    if not queries:
        queries = [f"{rules.category}: {facts[:300]}"]
    provisions, notes = find_provisions(research, queries)

    urgent_steps: list[str] = []
    if flags["threat_to_life"] or severity == "grave":
        urgent_steps.append("If anyone is in immediate danger, call 112 (emergency) now.")
    if flags["cyber"]:
        urgent_steps.append("If money was lost online, call 1930 immediately so the bank can freeze it.")
    if flags["women"]:
        urgent_steps.append("Women's helpline: 181. NCW helpline: 14490.")
    if flags["child"]:
        urgent_steps.append("Childline: 1098.")
    urgent = _clean(model.get("urgent"), 300)
    if urgent:
        urgent_steps.insert(0, urgent)

    return {
        "summary": _clean(model.get("summary"), 800) or facts[:400],
        "category": _clean(model.get("category"), 120) or rules.category,
        "severity": severity,
        "severity_reason": _clean(model.get("severity_reason"), 300),
        "flags": flags,
        "court_subjects": subjects,
        "incident": model.get("incident") if isinstance(model.get("incident"), dict) else {},
        "accused": _as_list(model.get("accused"), 6),
        "public_servants": _as_list(model.get("public_servants"), 6),
        "amount_involved": _clean(model.get("amount_involved"), 120),
        "wrongs": _as_list(model.get("wrongs"), 8),
        "missing_information": _as_list(model.get("missing_information"), 6),
        "law_search_queries": queries,
        "provisions": provisions,
        "law_notes": notes,
        "recommendations": [r.as_dict() for r in recommendations],
        "urgent_steps": list(dict.fromkeys(urgent_steps)),
        "model_used": model_used,
    }


def recommended_kinds(analysis: dict[str, Any]) -> list[str]:
    return [r["kind"] for r in analysis.get("recommendations", []) if r.get("kind") in KINDS]
