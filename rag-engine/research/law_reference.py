"""Deterministic extraction of Act/section references from research queries.

A *law key* identifies the unit case law is cached against:
``"<ACT_ID>:<SECTION>"`` for a section (``"BNS2023:103"``) or ``"<ACT_ID>"``
for an Act as a whole. Section keys use the base section number only, so
``13(1)(ia)`` and ``13`` share the same cached cases.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from acts.catalog import get_catalog


@dataclass(frozen=True)
class LawReference:
    act_id: str
    section: str | None = None
    # Full provision as written, e.g. "13(1)(ia)"; display only.
    provision: str | None = None
    # Set when the reference was translated from a repealed code (IPC/CrPC/IEA).
    translated_from: str | None = None

    @property
    def law_key(self) -> str:
        return law_key(self.act_id, self.section)


def law_key(act_id: str, section: str | None = None) -> str:
    return f"{act_id}:{section}" if section else act_id


def split_law_key(key: str) -> tuple[str, str | None]:
    act_id, _, section = key.partition(":")
    return act_id, section or None


def base_section(provision: str) -> str:
    """``"13(1)(ia)"`` -> ``"13"``; ``"498A"`` -> ``"498A"``."""
    match = re.match(r"\s*(\d+[A-Za-z]{0,2})", provision)
    return match.group(1).upper() if match else provision.strip().upper()


# Repealed codes are not in the corpus, but users still search by them. These
# are the widely cited correspondences from the official comparison tables.
_REPEALED_CODES: dict[str, tuple[str, tuple[str, ...], dict[str, str]]] = {
    "IPC": ("BNS2023", ("ipc", "indian penal code", "i p c"), {
        "34": "3", "120B": "61", "124A": "152", "302": "103", "304A": "106", "304B": "80",
        "306": "108", "307": "109", "354": "74", "375": "63", "376": "64", "379": "303",
        "406": "316", "420": "318", "498A": "85", "499": "356", "500": "356",
    }),
    "CRPC": ("BNSS2023", ("crpc", "cr p c", "code of criminal procedure"), {
        "41A": "35", "125": "144", "154": "173", "156": "175", "161": "180", "164": "183",
        "313": "351", "437": "480", "438": "482", "439": "483", "482": "528",
    }),
    "IEA": ("BSA", ("indian evidence act", "evidence act 1872", "evidence act", "iea"), {
        "25": "23", "32": "26", "45": "39", "65B": "63", "113B": "118",
    }),
}

# Laws that are not in the Act catalog but are researched often enough to key
# case law against. Their text is not in the corpus.
SUPPLEMENTARY_ACTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "CONSTITUTION": ("Constitution of India", ("constitution of india", "indian constitution", "constitution")),
    "RAILWAYS1989": ("The Railways Act, 1989", ("railways act 1989", "railways act", "railway act")),
    "IDA1947": ("The Industrial Disputes Act, 1947", ("industrial disputes act 1947", "industrial disputes act")),
}


def act_display_name(act_id: str) -> str:
    entry = get_catalog().get(act_id)
    if entry:
        return entry.short_title
    return SUPPLEMENTARY_ACTS.get(act_id, (act_id,))[0]


def act_official_title(act_id: str) -> str:
    entry = get_catalog().get(act_id)
    if entry:
        return entry.official_title
    return SUPPLEMENTARY_ACTS.get(act_id, (act_id,))[0]


_SECTION_RE = re.compile(
    r"\b(?:sections?|secs?|s|u\s*/\s*s|under\s+section|articles?|art)\.?\s*"
    r"(\d+[a-z]{0,2}(?:\s*\(\s*[0-9a-z]{1,4}\s*\))*)",
    re.IGNORECASE,
)
_LIST_CONTINUATION_RE = re.compile(
    r"\s*(?:,|and|&|or)\s*(\d+[a-z]{0,2}(?:\s*\(\s*[0-9a-z]{1,4}\s*\))*)(?![\w])", re.IGNORECASE
)
_NUMBER_RE = re.compile(r"(\d+[a-z]{0,2}(?:\s*\(\s*[0-9a-z]{1,4}\s*\))*)", re.IGNORECASE)


def _normalize(text: str, *, keep_commas: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    if keep_commas:
        # Commas separate list items ("sections 14, 15 and 21").
        text = text.replace(",", " , ")
        return re.sub(r"[^\w(),]+", " ", text)
    return re.sub(r"[^\w()]+", " ", text)


@lru_cache(maxsize=1)
def _alias_patterns() -> tuple[tuple[re.Pattern[str], str, str | None], ...]:
    """(pattern, act_id, repealed_code) sorted longest alias first."""
    aliases: list[tuple[str, str, str | None]] = []
    for entry in get_catalog().all_entries():
        if entry.ingestion_status == "catalog_only":
            continue
        names = {entry.act_id, entry.short_title, entry.official_title, *entry.aliases}
        for name in names:
            norm = _normalize(name).replace("_", " ").strip()
            norm = norm[4:] if norm.startswith("the ") else norm
            if len(norm) >= 3:
                aliases.append((norm, entry.act_id, None))
    for code, (act_id, names, _) in _REPEALED_CODES.items():
        aliases.extend((name, act_id, code) for name in names)
    for act_id, (_, names) in SUPPLEMENTARY_ACTS.items():
        aliases.extend((name, act_id, None) for name in names)
    aliases.sort(key=lambda item: len(item[0]), reverse=True)
    return tuple(
        (re.compile(rf"(?<!\w){re.escape(alias).replace(r'\ ', r'\s+')}(?!\w)"), act_id, code)
        for alias, act_id, code in aliases
    )


def _find_acts(norm: str) -> list[tuple[int, int, str, str | None]]:
    """Return non-overlapping (start, end, act_id, repealed_code) matches."""
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, int, str, str | None]] = []
    for pattern, act_id, code in _alias_patterns():
        for match in pattern.finditer(norm):
            start, end = match.span()
            if any(start < t_end and end > t_start for t_start, t_end in taken):
                continue
            taken.append((start, end))
            found.append((start, end, act_id, code))
    return sorted(found)


def _translate(code: str | None, provision: str) -> tuple[str | None, str | None]:
    """Map a repealed-code section to the current one. Returns (section, note)."""
    section = base_section(provision)
    if code is None:
        return section, None
    mapped = _REPEALED_CODES[code][2].get(section)
    return mapped, f"{code} {provision.replace(' ', '').upper()}"


def extract_law_references(query: str) -> list[LawReference]:
    """Find Act and section references, pairing each section with the nearest Act."""
    norm = _normalize(query, keep_commas=True)
    acts = _find_acts(norm)
    if not acts:
        # "Article 21" on its own means the Constitution.
        article = re.search(r"\barticles?\s+\d", norm)
        if not article:
            return []
        acts = [(article.start(), article.start(), "CONSTITUTION", None)]

    sections: list[tuple[int, str]] = []
    for match in _SECTION_RE.finditer(norm):
        sections.append((match.start(), match.group(1)))
        # "sections 14, 15 and 21"
        end = match.end()
        while more := _LIST_CONTINUATION_RE.match(norm, end):
            sections.append((more.start(1), more.group(1)))
            end = more.end()
    # "BNS 103" / "498A IPC": a bare number directly beside an Act alias.
    for start, end, _, _ in acts:
        after = _NUMBER_RE.match(norm, end + 1) if norm[end:end + 1] == " " else None
        if after:
            sections.append((after.start(), after.group(1)))
        before = re.search(r"(\d+[a-z]{0,2})\s+$", norm[:start])
        if before:
            sections.append((before.start(1), before.group(1)))

    refs: list[LawReference] = []
    seen: set[str] = set()
    paired_acts: set[int] = set()
    for position, provision in sorted(sections):
        index, (start, _, act_id, code) = min(
            enumerate(acts), key=lambda item: abs(item[1][0] - position)
        )
        paired_acts.add(index)
        section, translated = _translate(code, provision)
        provision_clean = re.sub(r"\s+", "", provision).upper() if section else None
        ref = LawReference(
            act_id=act_id,
            section=section,
            provision=provision_clean if not translated else section,
            translated_from=translated,
        )
        if ref.law_key not in seen:
            seen.add(ref.law_key)
            refs.append(ref)
    for index, (_, _, act_id, code) in enumerate(acts):
        if index in paired_acts or act_id in seen:
            continue
        seen.add(act_id)
        refs.append(LawReference(act_id=act_id, translated_from=code))
    return refs
