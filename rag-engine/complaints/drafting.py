"""Write the complaint or petition for one office or court.

Inputs: the chosen office/court kind, the recipient, the complainant, the
facts, the analysis (with provisions retrieved from the statute corpus) and
the matching format from the drafting-template library.

Guarantees, enforced after generation rather than trusted to the prompt:
- statutory citations must point at a retrieved provision ([n] markers are
  checked and then removed from the printed text); uncited section numbers
  are reported as warnings;
- facts the person did not give stay as [PLACEHOLDERS] for them to fill in;
- with no model configured, the template is filled deterministically.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Callable, Sequence

from .taxonomy import KINDS, high_court_for
from .templates import TemplateMatch

logger = logging.getLogger(__name__)

TextGenerator = Callable[[str], str]
DISCLAIMER = ("Prepared with ChatLaw from the information you gave. This is informational assistance only — "
              "not a substitute for a lawyer or court. Check every fact before you sign and file it.")
LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "ml": "Malayalam",
    "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi", "or": "Odia", "as": "Assamese",
    "ur": "Urdu",
}
_CITATION_RE = re.compile(r"\[(\d{1,2})\]")
_SECTION_RE = re.compile(r"\b(?:section|sec\.|s\.)\s*(\d{1,3}[A-Z]?)(?:\(\d+\))*", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"\[([A-Z][A-Z0-9 ,./'&()-]{2,80})\]")
EMAIL_BODY_LIMIT = 6000


def _value(data: dict[str, Any] | None, key: str) -> str:
    if not data:
        return ""
    value = data.get(key)
    return str(value).strip() if value not in (None, "") else ""


def complainant_block(complainant: dict[str, Any] | None) -> str:
    c = complainant or {}
    name = _value(c, "name") or "[COMPLAINANT NAME]"
    parts = [name]
    if _value(c, "relation_name"):
        parts.append(f"{_value(c, 'relation') or 'S/o, D/o or W/o'} {_value(c, 'relation_name')}")
    if _value(c, "age"):
        parts.append(f"aged about {_value(c, 'age')} years")
    if _value(c, "occupation"):
        parts.append(_value(c, "occupation"))
    parts.append(f"residing at {_value(c, 'address') or '[COMPLAINANT ADDRESS]'}")
    contact = ", ".join(x for x in (
        f"mobile {_value(c, 'phone')}" if _value(c, "phone") else "mobile [PHONE NUMBER]",
        f"email {_value(c, 'email')}" if _value(c, "email") else "",
    ) if x)
    return ", ".join(parts) + f" ({contact})"


def recipient_block(kind: str, recipient: dict[str, Any] | None, location: dict[str, Any] | None) -> str:
    r = recipient or {}
    loc = location or {}
    lines = []
    if _value(r, "designation"):
        lines.append(_value(r, "designation"))
    if _value(r, "name") and _value(r, "name") != _value(r, "designation"):
        lines.append(_value(r, "name"))
    if _value(r, "address"):
        lines.append(_value(r, "address"))
    if lines:
        return "\n".join(lines)
    district = _value(loc, "district") or _value(loc, "city") or "[DISTRICT]"
    state = _value(loc, "state") or "[STATE]"
    hc = high_court_for(state)
    defaults = {
        "police_station": "The Station House Officer,\n[NAME OF POLICE STATION] Police Station,\n" + district,
        "police_superior": f"The Superintendent of Police / Commissioner of Police,\n{district}, {state}",
        "collector": f"The District Collector and District Magistrate,\n{district} District, {state}",
        "vigilance": f"The Director,\nState Vigilance and Anti-Corruption Department, {state}",
        "cm_cell": f"The Hon'ble Chief Minister of {state},\nChief Minister's Special Cell, Secretariat",
        "cbi": "The Superintendent of Police,\nCentral Bureau of Investigation, [BRANCH]",
        "pmo": "The Prime Minister's Office (Public Wing),\nSouth Block, Raisina Hill, New Delhi - 110011",
        "women_commission": f"The Chairperson,\nState Commission for Women, {state} / National Commission for Women",
        "human_rights": f"The Registrar (Law),\nState Human Rights Commission, {state} / National Human Rights Commission",
        "cyber_crime": f"The Inspector of Police,\nCyber Crime Police Station, {district}",
        "magistrate": f"In the Court of the Judicial Magistrate, {district}",
        "civil_court": f"In the Court of the District Judge / Civil Judge, {district}",
        "family_court": f"In the Family Court, {district}",
        "consumer_commission": f"Before the District Consumer Disputes Redressal Commission, {district}",
        "high_court": f"In the {hc[0] if hc else 'High Court of ' + state}",
        "supreme_court": "In the Supreme Court of India",
    }
    return defaults.get(kind, "[ADDRESSEE]")


def build_draft_prompt(*, kind: str, template: TemplateMatch, facts: str, analysis: dict[str, Any],
                       complainant: dict[str, Any] | None, recipient_text: str, location: dict[str, Any] | None,
                       language: str, instructions: str | None, today: str) -> str:
    spec = KINDS[kind]
    provisions = analysis.get("provisions") or []
    sources = "\n\n".join(
        f"[{p['id']}] {p['label']} — {p['act_title']}"
        f"{' (replaces ' + p['translated_from'] + ')' if p.get('translated_from') else ''}\n{p['text'][:1800]}"
        for p in provisions
    ) or "(no statutory text was retrieved — do not cite any section)"
    loc = ", ".join(str(location[k]) for k in ("locality", "city", "district", "state", "pincode")
                    if location and location.get(k))
    language_name = LANGUAGE_NAMES.get(language, "English")
    analysis_view = {k: analysis.get(k) for k in ("summary", "category", "severity", "incident", "accused",
                                                   "public_servants", "amount_involved", "wrongs")}
    court = spec.forum == "court"
    return f"""You draft documents for Indian citizens to file with the police, government offices and courts.
Write the {spec.label} document below for this person.

DOCUMENT: {template.template.title}
WHERE IT GOES: {spec.label} — {spec.description}
{('IMPORTANT LIMIT: ' + spec.caveat) if spec.caveat else ''}

ADDRESSEE:
{recipient_text}

COMPLAINANT / PETITIONER: {complainant_block(complainant)}
LOCATION: {loc or '(not given)'}
TODAY'S DATE: {today}

THE PERSON'S ACCOUNT (the only source of facts):
\"\"\"
{facts[:12000]}
\"\"\"

STRUCTURED READING OF THE ACCOUNT:
{analysis_view}

STATUTORY TEXT YOU MAY CITE (numbered sources; nothing else):
{sources}

FORMAT TO FOLLOW (from ChatLaw's template library; keep its parts and order, adapt the wording):
{template.exemplar()}

RULES:
1. Facts: use only the person's account. Never invent names, dates, places, amounts, ages, phone numbers,
   acknowledgment numbers or events. Where the format needs a fact the account does not give, write a
   placeholder in capitals inside square brackets, e.g. [DATE OF INCIDENT], [ACCUSED ADDRESS].
2. Law: you may only name statutory provisions from the numbered sources. Name the provision in words and add
   its source number right after it, e.g. "Section 318(4) of the Bharatiya Nyaya Sanhita, 2023 [2]".
   Do not name any other section, Act or case. If no source fits, describe the wrong without a section.
3. Write the whole document in {language_name} — headings, subject line, addressee block, facts, prayer and the
   covering email included. {'' if language_name == 'English' else 'Keep only the names of Acts and section numbers in English (e.g. "Section 318 of the Bharatiya Nyaya Sanhita, 2023"); translate everything else, including the template headings.'}
4. Tone: formal, respectful, factual. Numbered paragraphs for facts, in date order. No legal advice to the reader.
5. {'This is a court document: include the cause title, verification and the prayer in the court format.' if court else 'This is a letter/complaint to an office: include the addressee block, subject line, salutation, facts, request and closing.'}
6. Do not include the "Filing notes" section of the template in the document.
{('7. Additional instructions from the person: ' + instructions.strip()) if instructions and instructions.strip() else ''}

Return ONLY a JSON object:
{{"title": "short document title",
  "subject": "subject line (for a court document: the nature of the petition)",
  "addressee": "addressee / cause-title block as it should appear at the top",
  "sections": [{{"heading": "heading or empty string", "text": "section text"}}],
  "enclosures": ["documents to attach; add ' (if available)' to any the account does not say the person has"],
  "email_cover_note": "4-6 line covering email that introduces the attached complaint"}}"""


def _sections(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    sections = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
            sections.append({"heading": str(item.get("heading") or "").strip()[:200],
                             "text": item["text"].strip()[:12000]})
    return sections[:30]


def check_citations(sections: list[dict[str, Any]], provisions: Sequence[dict[str, Any]],
                    procedural_text: str = "") -> tuple[list[dict[str, Any]], list[int], list[str]]:
    """Validate [n] markers, strip them from the text, and flag section numbers nothing supports.

    Procedural provisions named by the format itself (e.g. Section 173 BNSS in the
    police-complaint template, checked by hand) are allowed via `procedural_text`.
    """
    allowed = {str(p["section"]).upper() for p in provisions if p.get("section")}
    allowed |= {m.group(1).upper() for m in _SECTION_RE.finditer(procedural_text)}
    known = {int(p["id"]): p for p in provisions}
    used: list[int] = []
    warnings: list[str] = []
    invalid: set[int] = set()
    cleaned = []
    for section in sections:
        text = section["text"]
        ids = [int(m) for m in _CITATION_RE.findall(text)]
        valid_ids = [i for i in ids if i in known]
        invalid.update(i for i in ids if i not in known)
        used.extend(i for i in valid_ids if i not in used)
        stripped = _CITATION_RE.sub("", text)
        stripped = re.sub(r"[ \t]+([,.;:)])", r"\1", stripped)
        stripped = re.sub(r"[ \t]{2,}", " ", stripped)
        for match in _SECTION_RE.finditer(text):
            if match.group(1).upper() not in allowed:
                warnings.append(f"\"{match.group(0).strip()}\" is not backed by a retrieved provision — "
                                "check it before filing.")
        cleaned.append({**section, "text": stripped.strip(), "citation_ids": valid_ids})
    if invalid:
        warnings.append("Some citations did not match retrieved statutory text and were removed.")
    return cleaned, used, list(dict.fromkeys(warnings))


def placeholders_in(text: str) -> list[str]:
    return list(dict.fromkeys(f"[{m}]" for m in _PLACEHOLDER_RE.findall(text)))


# Template part names that structure the draft but are not printed in a letter.
_UNPRINTED_HEADINGS = {"body", "text", "introduction", "salutation and introduction", "salutation", "closing",
                       "addressee", "subject", "signature", "declaration and closing", "title", "cause title"}


def assemble_text(addressee: str, subject: str, sections: Sequence[dict[str, Any]], enclosures: Sequence[str],
                  *, court: bool, language: str = "en") -> str:
    parts = [addressee.strip()]
    if subject:
        # A translated subject carries its own label (e.g. "பொருள்:"); only English gets "Subject:" added.
        labelled = court or language != "en" or subject.lower().startswith("subject")
        parts.append(subject if labelled else f"Subject: {subject}")
    for section in sections:
        heading = section.get("heading", "").strip()
        printed = heading and heading.lower() not in _UNPRINTED_HEADINGS
        parts.append(f"{heading}\n{section['text']}" if printed else section["text"])
    if enclosures:
        parts.append("Enclosures:\n" + "\n".join(f"{i}. {e}" for i, e in enumerate(enclosures, 1)))
    return "\n\n".join(p for p in parts if p.strip())


def fallback_sections(template: TemplateMatch, facts: str, complainant: dict[str, Any] | None,
                      analysis: dict[str, Any], today: str) -> list[dict[str, Any]]:
    """Deterministic draft from the template when no model is configured."""
    sections: list[dict[str, Any]] = []
    skip = {"addressee", "subject", "filing notes", "cause title"}
    provisions = analysis.get("provisions") or []
    for section in template.template.sections:
        heading = section.heading
        if heading.lower() in skip:
            continue
        lowered = heading.lower()
        if "fact" in lowered or "grievance" in lowered or "incident" in lowered:
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", facts) if p.strip()]
            text = "\n".join(f"{i}. {p}" for i, p in enumerate(paragraphs[:25], 1))
        elif "offence" in lowered or lowered.startswith("offences") or "deficiency" in lowered:
            if provisions:
                text = ("The facts stated above disclose the following, among other provisions as the authority "
                        "may find applicable:\n" + "\n".join(f"- {p['label']}" for p in provisions[:6]))
            else:
                text = section.body
        elif "introduction" in lowered:
            text = f"I, {complainant_block(complainant)}, submit as follows."
        elif "closing" in lowered:
            text = (f"Place: {_value(complainant, 'place') or '[PLACE]'}\nDate: {today}\n\nYours faithfully,\n\n"
                    f"{_value(complainant, 'name') or '[COMPLAINANT NAME]'}")
        else:
            text = section.body
        sections.append({"heading": heading, "text": text, "citation_ids": []})
    return sections


def default_cover_note(kind: str, subject: str, complainant: dict[str, Any] | None) -> str:
    name = _value(complainant, "name") or "[YOUR NAME]"
    phone = _value(complainant, "phone") or "[PHONE NUMBER]"
    return (f"Respected Sir/Madam,\n\nPlease find below my complaint regarding: {subject}.\n"
            "I request you to kindly take action on it in accordance with law and acknowledge receipt.\n\n"
            f"Yours faithfully,\n{name}\nMobile: {phone}")


def draft_filing(*, kind: str, template: TemplateMatch, facts: str, analysis: dict[str, Any],
                 complainant: dict[str, Any] | None = None, recipient: dict[str, Any] | None = None,
                 location: dict[str, Any] | None = None, language: str = "en", instructions: str | None = None,
                 generate: TextGenerator | None = None, today: date | None = None) -> dict[str, Any]:
    if kind not in KINDS:
        raise KeyError(kind)
    spec = KINDS[kind]
    today_text = (today or date.today()).strftime("%d.%m.%Y")
    recipient_text = recipient_block(kind, recipient, location)
    provisions = analysis.get("provisions") or []
    warnings: list[str] = []
    payload: dict[str, Any] | None = None
    model_used = False
    if generate is not None:
        try:
            from research.discovery import parse_json_payload

            parsed = parse_json_payload(generate(build_draft_prompt(
                kind=kind, template=template, facts=facts, analysis=analysis, complainant=complainant,
                recipient_text=recipient_text, location=location, language=language,
                instructions=instructions, today=today_text,
            )))
            if isinstance(parsed, dict) and _sections(parsed.get("sections")):
                payload, model_used = parsed, True
            else:
                warnings.append("The language model did not return a usable draft; the template was filled instead.")
        except Exception:
            logger.exception("[FILINGS] drafting model failed")
            warnings.append("The language model was unavailable; the template was filled instead.")

    if payload:
        procedural = "\n".join([template.template.text, *template.template.sources])
        sections, used, citation_warnings = check_citations(_sections(payload["sections"]), provisions, procedural)
        warnings.extend(citation_warnings)
        subject = str(payload.get("subject") or "").strip()[:400]
        addressee = str(payload.get("addressee") or recipient_text).strip()[:1200]
        title = str(payload.get("title") or template.template.title).strip()[:200]
        enclosures = [str(e).strip()[:300] for e in payload.get("enclosures") or [] if str(e).strip()][:15]
        cover = str(payload.get("email_cover_note") or "").strip()[:2000]
    else:
        sections = fallback_sections(template, facts, complainant, analysis, today_text)
        used = []
        subject = analysis.get("summary", "")[:200] or template.template.title
        addressee, title, enclosures, cover = recipient_text, template.template.title, [], ""
        warnings.append("Drafted from the template without a language model — review every paragraph.")

    if not provisions:
        warnings.append("No statutory text was retrieved for these facts, so the draft names no sections.")
    text = assemble_text(addressee, subject, sections, enclosures, court=spec.forum == "court", language=language)
    placeholders = placeholders_in(text)
    if placeholders:
        warnings.append(f"Fill in {len(placeholders)} missing detail{'s' if len(placeholders) != 1 else ''} "
                        "marked in [BRACKETS] before filing.")
    cover = cover or default_cover_note(kind, subject, complainant)
    email_body = f"{cover}\n\n{'-' * 40}\n\n{text}"
    if len(email_body) > EMAIL_BODY_LIMIT:
        email_body = f"{cover}\n\n(The complete complaint is attached as a PDF.)"
    citations = [{"id": p["id"], "label": p["label"], "act_title": p["act_title"], "law_key": p["law_key"],
                  "source_url": p.get("source_url")} for p in provisions if p["id"] in used]
    return {
        "kind": kind,
        "forum": spec.forum,
        "title": title,
        "subject": subject,
        "addressee": addressee,
        "sections": sections,
        "enclosures": enclosures,
        "text": text,
        "citations": citations,
        "placeholders": placeholders,
        "warnings": list(dict.fromkeys(warnings)),
        "email": {"subject": re.sub(r"^\s*subject\s*:\s*", "", subject, flags=re.IGNORECASE)[:250] or title, "body": email_body, "cover_note": cover,
                  "full_text_fits": len(f"{cover}\n\n{text}") <= EMAIL_BODY_LIMIT},
        "filing": {"channel": spec.channel, "portal_url": spec.portal_url, "portal_label": spec.portal_label,
                   "helpline": spec.helpline, "caveat": spec.caveat,
                   "notes": next((s.body for s in template.template.sections if s.heading.lower() == "filing notes"),
                                 None)},
        "template": template.audit(),
        "language": language,
        "model_used": model_used,
        "disclaimer": DISCLAIMER,
    }
