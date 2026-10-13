"""Verify that a judgment link is official and actually contains the named case.

A link is accepted only when it is HTTPS on an Indian government domain and
the downloaded document (PDF or HTML) mentions the parties. A reachable URL
alone is not enough: api.sci.gov.in, for example, answers 200 with an empty
body for paths that do not exist.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
# Parties are matched only in the cause title at the top of the judgment, so a
# judgment that merely cites the case is not mistaken for it.
CAUSE_TITLE_CHARS = 4000
REQUEST_TIMEOUT_SECONDS = 25.0
USER_AGENT = "Mozilla/5.0 (compatible; ChatLawResearch/1.0; +https://chatlaw.in)"

# Hosts that moved; the same paths are served from the replacement host.
_HOST_REWRITES = {"main.sci.gov.in": "api.sci.gov.in"}

# Words that appear in many cause titles and say nothing about which case it is.
_GENERIC_PARTY_WORDS = frozenset({
    "state", "union", "india", "government", "govt", "others", "other", "anr", "ors", "and",
    "the", "of", "ltd", "limited", "pvt", "private", "co", "company", "corporation", "corp",
    "shri", "smt", "sri", "mr", "mrs", "ms", "dr", "through", "thr", "its", "by", "appellant",
    "respondent", "petitioner", "versus", "vs", "commissioner", "officer", "secretary",
    "director", "authority", "board", "bank", "council", "municipal", "district", "high",
    "court", "supreme", "public", "prosecutor", "central", "bureau", "investigation", "police",
    "station", "inspector", "superintendent", "collector", "tax", "income", "deputy",
    "assistant", "chief", "general", "manager", "national", "development", "pradesh", "uttar",
    "madhya", "andhra", "himachal", "arunachal", "tamil", "nadu", "west", "bengal", "kerala",
    "karnataka", "maharashtra", "gujarat", "rajasthan", "punjab", "haryana", "bihar", "delhi",
    "goa", "assam", "odisha", "orissa", "telangana", "jharkhand", "chhattisgarh", "uttarakhand",
    "nct", "retd", "kumar", "singh", "devi", "lal",
})


@dataclass(frozen=True)
class LinkVerification:
    url: str
    verified: bool
    reason: str
    content_type: str | None = None
    # First pages of judgment text, kept for summaries and case embeddings.
    excerpt: str = ""


def is_official_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and any(host.endswith(suffix) for suffix in OFFICIAL_SUFFIXES)


def normalize_official_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    host = _HOST_REWRITES.get(host, host)
    return urlunsplit(("https", host, parts.path, parts.query, ""))


def url_variants(url: str) -> list[str]:
    """The normalized URL plus known alternate paths for the same file."""
    normalized = normalize_official_url(url)
    variants = [normalized]
    # Older Supreme Court judgments live under /jonew/judis/; models often write /jonew/judgments/.
    for old, new in (("/jonew/judgments/", "/jonew/judis/"), ("/jonew/judis/", "/jonew/judgments/")):
        if old in normalized:
            variants.append(normalized.replace(old, new))
    return variants


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text)


def distinctive_tokens(name: str | None) -> set[str]:
    return {
        token for token in _fold(name or "").split()
        if len(token) >= 4 and token not in _GENERIC_PARTY_WORDS and not token.isdigit()
    }


def split_parties(title: str) -> tuple[str, str]:
    parts = re.split(r"\s+(?:v\.?|vs\.?|versus)\s+", title, maxsplit=1, flags=re.IGNORECASE)
    return (parts[0], parts[1]) if len(parts) == 2 else (title, "")


def parties_match(text: str, title: str, petitioner: str | None = None,
                  respondent: str | None = None) -> bool:
    """True when the document names the parties of this case.

    Each side with distinctive words must have at least one of them in the
    text. A side made only of generic words ("State of Kerala") is skipped,
    but at least one side must be checkable.
    """
    folded = f" {_fold(text)} "
    first, second = split_parties(title)
    sides = [
        distinctive_tokens(petitioner) | distinctive_tokens(first),
        distinctive_tokens(respondent) | distinctive_tokens(second),
    ]
    checkable = [side for side in sides if side]
    if not checkable:
        return False
    return all(any(f" {token} " in folded for token in side) for side in checkable)


def _extract_pdf_text(data: bytes, max_pages: int = 4) -> str:
    import pymupdf  # type: ignore

    with pymupdf.open(stream=io.BytesIO(data), filetype="pdf") as document:
        return "\n".join(document[i].get_text() for i in range(min(max_pages, document.page_count)))


def _extract_html_text(data: bytes) -> str:
    html = data.decode("utf-8", errors="ignore")
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html))


@lru_cache(maxsize=256)
def fetch_document_text(url: str, max_pages: int = 4) -> tuple[str | None, str]:
    """Download a judgment and return (content_type, text of the first pages). Cached per process."""
    import httpx

    with httpx.Client(follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS,
                      headers={"User-Agent": USER_AGENT}) as client:
        with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            final_url = str(response.url)
            if not is_official_url(final_url):
                raise ValueError("redirected off an official domain")
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_DOCUMENT_BYTES:
                    raise ValueError("document too large")
                chunks.append(chunk)
    data = b"".join(chunks)
    if not data.strip():
        raise ValueError("empty document")
    if content_type == "application/pdf" or data[:5] == b"%PDF-":
        return "application/pdf", _extract_pdf_text(data, max_pages)
    if content_type in {"text/html", "application/xhtml+xml", "text/plain"}:
        return content_type, _extract_html_text(data)
    raise ValueError(f"unsupported content type {content_type or 'unknown'}")


def verify_judgment_link(url: str | None, *, title: str, petitioner: str | None = None,
                         respondent: str | None = None) -> LinkVerification:
    if not url or not is_official_url(url):
        return LinkVerification(url or "", False, "not an official government URL")
    failure: LinkVerification | None = None
    for candidate in url_variants(url):
        result = _verify_one(candidate, title, petitioner, respondent)
        if result.verified:
            return result
        failure = failure or result
    return failure  # type: ignore[return-value]


def _verify_one(normalized: str, title: str, petitioner: str | None,
                respondent: str | None) -> LinkVerification:
    try:
        content_type, text = fetch_document_text(normalized)
    except Exception as exc:  # network errors, bad PDFs, oversized files
        return LinkVerification(normalized, False, f"unreachable: {exc}"[:200])
    # HTML pages carry site navigation before the judgment, so look further down.
    window = CAUSE_TITLE_CHARS if content_type == "application/pdf" else CAUSE_TITLE_CHARS * 3
    if not parties_match(text[:window], title, petitioner, respondent):
        return LinkVerification(normalized, False, "document does not name the parties", content_type)
    return LinkVerification(normalized, True, "parties found in official document", content_type,
                            excerpt=re.sub(r"\s+", " ", text)[:6000])
