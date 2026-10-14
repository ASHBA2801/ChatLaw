"""Official contact details for the office a complaint is addressed to.

Order of lookup:
1. the curated directory (complaints/data/authorities.json), checked by hand;
2. the authority_contacts cache (90 days, including "none found");
3. Gemini with Google Search grounding, restricted to official sites.

A discovered email is used only when the official page it came from — or one
of the official pages Google returned while grounding — is downloaded and
actually contains the address. Indian government sites often write emails as
"sp-cbe[at]tn[dot]gov[dot]in", so the page text is de-obfuscated first.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import urlsplit

from .taxonomy import KINDS, high_court_for, normalize_state

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(days=int(os.getenv("CONTACT_CACHE_DAYS", "90")))
# Lookups that found no verified email are retried sooner; sites get updated.
NO_EMAIL_CACHE_TTL = timedelta(days=int(os.getenv("CONTACT_NO_EMAIL_CACHE_DAYS", "7")))
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
MAX_PAGE_BYTES = 6 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (compatible; ChatLawFilings/1.0; +https://chatlaw.in)"
EMAIL_RE = re.compile(r"[a-z0-9][a-z0-9._%+-]{0,63}@[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.IGNORECASE)


@dataclass(frozen=True)
class ContactEmail:
    address: str
    label: str | None = None
    source_url: str | None = None
    verified: bool = True


@dataclass(frozen=True)
class OfficeContact:
    kind: str
    name: str
    designation: str | None = None
    address: str | None = None
    phone: str | None = None
    emails: tuple[ContactEmail, ...] = ()
    website: str | None = None
    portal_url: str | None = None
    notes: str | None = None
    source: str = "curated"  # "curated" | "official_search" | "osm"
    source_url: str | None = None
    distance_km: float | None = None
    latitude: float | None = None
    longitude: float | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["emails"] = [asdict(e) for e in self.emails]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficeContact":
        emails = tuple(ContactEmail(**{k: v for k, v in e.items() if k in ContactEmail.__dataclass_fields__})
                       for e in data.get("emails") or [] if isinstance(e, dict) and e.get("address"))
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "emails"}
        return cls(**fields, emails=emails)


# ------------------------------------------------------------------ curated

@lru_cache(maxsize=1)
def _directory() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "data" / "authorities.json"
    return json.loads(path.read_text(encoding="utf-8"))


def curated_contacts(kind: str, state: str | None = None) -> list[OfficeContact]:
    data = _directory()
    state_key = normalize_state(state)
    rows = [row for row in data.get("national", []) if row.get("kind") == kind]
    rows += [row for row in data.get("state", []) if row.get("kind") == kind and row.get("state") == state_key]
    contacts = []
    for row in rows:
        clean = {k: v for k, v in row.items() if k != "state"}
        contacts.append(replace(OfficeContact.from_dict(clean), source="curated"))
    return contacts


# ------------------------------------------------------------- verification

def is_official_host(url: str | None) -> bool:
    if not url:
        return False
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return parts.scheme in {"https", "http"} and any(host.endswith(s) for s in OFFICIAL_SUFFIXES)


_OBFUSCATIONS = (
    (r"\s*[\[\(\{<]\s*at\s*[\]\)\}>]\s*", "@"),
    (r"\s*[\[\(\{<]\s*dot\s*[\]\)\}>]\s*", "."),
    (r"\s+at\s+(?=[a-z0-9-]+\s*(?:\[|\(|\s)dot)", "@"),
    (r"\s+dot\s+(?=[a-z]{2,6}\b)", "."),
    (r"\s*@\s*", "@"),
)


def deobfuscate(text: str) -> str:
    out = text.lower()
    for pattern, replacement in _OBFUSCATIONS:
        out = re.sub(pattern, replacement, out)
    return out


def emails_in(text: str) -> set[str]:
    return {match.group(0).lower().rstrip(".") for match in EMAIL_RE.finditer(deobfuscate(text))}


def _html_text(data: bytes) -> str:
    html = data.decode("utf-8", errors="ignore")
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    # keep mailto targets: some sites show "Email" as the link text only
    html = re.sub(r'(?i)href\s*=\s*["\']mailto:([^"\'?]+)', r" \1 ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html))


@lru_cache(maxsize=512)
def fetch_page_text(url: str) -> str:
    """Text of an official page (HTML or PDF). Raises on non-official redirects or errors."""
    import httpx

    with httpx.Client(follow_redirects=True, timeout=20.0, headers={"User-Agent": USER_AGENT},
                      verify=True) as client:
        with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            if not is_official_host(str(response.url)):
                raise ValueError("redirected off an official domain")
            content_type = (response.headers.get("content-type") or "").split(";")[0].lower()
            data = b""
            for chunk in response.iter_bytes():
                data += chunk
                if len(data) > MAX_PAGE_BYTES:
                    raise ValueError("page too large")
    if content_type == "application/pdf" or data[:5] == b"%PDF-":
        import pymupdf  # type: ignore

        with pymupdf.open(stream=io.BytesIO(data), filetype="pdf") as document:
            return "\n".join(document[i].get_text() for i in range(min(12, document.page_count)))
    return _html_text(data)


def verify_email(email: str, urls: Sequence[str], fetch: Callable[[str], str] = fetch_page_text) -> str | None:
    """Return the official URL whose text contains the email, or None."""
    target = email.strip().lower()
    if not EMAIL_RE.fullmatch(target):
        return None
    for url in dict.fromkeys(u for u in urls if is_official_host(u)):
        try:
            text = fetch(url)
        except Exception as exc:
            logger.info("[FILINGS] contact page unreachable %s: %s", url, exc)
            continue
        if target in emails_in(text):
            return url
    return None


# NIC district websites (S3WaaS) share these paths; the who's-who page lists
# officers' emails, so it is a reliable second place to confirm an address.
_CONTACT_PATHS = ("/whos-who/", "/contact-us/", "/directory/", "/contact/")


def candidate_pages(*urls: str | None, limit: int = 8) -> list[str]:
    """Official pages to check an email against: the given pages, then contact pages on the same hosts."""
    pages: list[str] = []
    hosts: list[str] = []
    for url in urls:
        if not url or not is_official_host(url):
            continue
        pages.append(url)
        parts = urlsplit(url)
        root = f"{parts.scheme}://{parts.hostname}"
        if root not in hosts:
            hosts.append(root)
    for root in hosts:
        pages.extend(f"{root}{path}" for path in _CONTACT_PATHS)
    return list(dict.fromkeys(pages))[:limit]


# ----------------------------------------------------------------- discovery

def office_description(kind: str, *, locality: str | None, city: str | None, district: str | None,
                       state: str | None, office_name: str | None = None) -> str:
    place = ", ".join(p for p in (locality, city, district, state) if p)
    district_name = district or city or locality or "the district"
    state_name = state or "the State"
    hc = high_court_for(state)
    descriptions = {
        "police_station": (f"the police station '{office_name}'" if office_name else
                           f"the law-and-order police station with jurisdiction over {place}")
                          + f" in {district_name} district, {state_name}, and its Station House Officer (SHO)",
        "police_superior": f"the Commissioner of Police if {city or district_name} is a police commissionerate, "
                           f"otherwise the Superintendent of Police of {district_name} district, {state_name}",
        "collector": f"the District Collector / District Magistrate of {district_name} district, {state_name}",
        "vigilance": f"the {state_name} State anti-corruption agency (Directorate of Vigilance and Anti-Corruption, "
                     f"Anti-Corruption Bureau or Vigilance Bureau) — its {district_name} unit and its headquarters",
        "cm_cell": f"the Chief Minister's Special Cell / Chief Minister's public grievance cell of {state_name}",
        "cyber_crime": f"the cyber crime police station for {district_name}, {state_name}",
        "women_commission": f"the State Commission for Women of {state_name}",
        "human_rights": f"the State Human Rights Commission of {state_name}",
        "magistrate": f"the Chief Judicial Magistrate court of {district_name} district, {state_name}",
        "civil_court": f"the District Court (Principal District Judge) of {district_name} district, {state_name}",
        "family_court": f"the Family Court for {district_name}, {state_name}",
        "consumer_commission": f"the District Consumer Disputes Redressal Commission, {district_name}, {state_name}",
        "high_court": f"the {hc[0]} (registry / registrar general)" if hc else f"the High Court for {state_name}",
    }
    return descriptions.get(kind, KINDS[kind].label if kind in KINDS else kind)


def build_contact_prompt(description: str) -> str:
    return f"""Use Google Search to find the official contact details of {description}, India.

Rules:
- Use only information published on official Indian government websites (domains ending in .gov.in or .nic.in).
- Never guess or construct an email address. If you did not see an email on an official page, use null.
- source_url must be the exact official page where you saw the details.
- Prefer the office's own page (district police / district administration / commission website) over directories.

Return ONLY a JSON object:
{{"offices": [{{"name": "office name", "designation": "head of office, e.g. Superintendent of Police",
  "address": "postal address or null", "phone": "phone or null", "email": "email or null",
  "website": "official website or null", "source_url": "official page with these details"}}]}}
List at most 3 offices, most relevant first."""


def _clean(value: Any, limit: int = 400) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:limit] if text and text.lower() not in {"null", "none", "n/a", "unknown"} else None


def _parse_offices(text: str) -> list[dict[str, Any]]:
    from research.discovery import parse_json_payload

    try:
        payload = parse_json_payload(text)
    except (json.JSONDecodeError, ValueError):
        return []
    items = payload.get("offices", []) if isinstance(payload, dict) else payload
    return [item for item in items if isinstance(item, dict)][:3] if isinstance(items, list) else []


class ContactFinder:
    """Grounded discovery of office contacts. `client` is a google-genai Client (injectable)."""

    def __init__(self, client: Any = None, *, model: str | None = None,
                 fetch: Callable[[str], str] = fetch_page_text,
                 resolve_redirect: Callable[[str], str | None] | None = None):
        self.model = model or os.getenv("GEMINI_RESEARCH_MODEL", "").strip() or os.getenv(
            "GEMINI_GENERATION_MODEL", "").strip()
        if not self.model:
            raise ValueError("GEMINI_GENERATION_MODEL is required for contact discovery")
        if client is None:
            from research.discovery import _default_client
            client = _default_client()
        self._client = client
        self._fetch = fetch
        if resolve_redirect is None:
            from research.discovery import _resolve_grounding_redirect
            resolve_redirect = _resolve_grounding_redirect
        self._resolve_redirect = resolve_redirect

    def _generate(self, prompt: str) -> tuple[str, list[str]]:
        from google.genai import types  # type: ignore

        config: dict[str, Any] = {"tools": [types.Tool(google_search=types.GoogleSearch())], "temperature": 0.0}
        if self.model.startswith("gemini-3"):
            config["thinking_config"] = types.ThinkingConfig(thinking_level="low")
        response = self._client.models.generate_content(model=self.model, contents=prompt,
                                                        config=types.GenerateContentConfig(**config))
        return response.text or "", self._grounding_urls(response)

    def _grounding_urls(self, response: Any) -> list[str]:
        urls: list[str] = []
        try:
            chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
        except (AttributeError, IndexError, TypeError):
            return urls
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            title = (getattr(web, "title", "") or "").lower()
            uri = getattr(web, "uri", None)
            if not uri or not title.endswith(OFFICIAL_SUFFIXES):
                continue
            resolved = uri if is_official_host(uri) else self._resolve_redirect(uri)
            if resolved and is_official_host(resolved) and resolved not in urls:
                urls.append(resolved)
            if len(urls) >= 6:
                break
        return urls

    def find(self, kind: str, description: str) -> list[OfficeContact]:
        text, grounded = self._generate(build_contact_prompt(description))
        offices = _parse_offices(text)
        results: list[OfficeContact] = []

        def check(item: dict[str, Any]) -> OfficeContact | None:
            name = _clean(item.get("name"), 200)
            if not name:
                return None
            source_url = _clean(item.get("source_url"), 1000)
            website = _clean(item.get("website"), 500)
            pages = candidate_pages(source_url, *grounded, website)
            emails: list[ContactEmail] = []
            email = _clean(item.get("email"), 200)
            if email:
                for candidate in re.split(r"[,;/\s]+", email):
                    candidate = candidate.strip().lower()
                    found_on = verify_email(candidate, pages, self._fetch) if candidate else None
                    if found_on:
                        emails.append(ContactEmail(candidate, "Found on official page", found_on, True))
            official_source = source_url if is_official_host(source_url) else next(iter(grounded), None)
            if not emails and not official_source:
                return None  # nothing we can stand behind
            return OfficeContact(
                kind=kind, name=name, designation=_clean(item.get("designation"), 200),
                address=_clean(item.get("address"), 400), phone=_clean(item.get("phone"), 120),
                emails=tuple(emails), website=website if is_official_host(website) else None,
                source="official_search", source_url=emails[0].source_url if emails else official_source,
            )

        if offices:
            with ThreadPoolExecutor(max_workers=min(3, len(offices))) as pool:
                for contact in pool.map(check, offices):
                    if contact:
                        results.append(contact)
        logger.info("[FILINGS] contact discovery %s: %d proposed, %d kept, %d with verified email",
                    kind, len(offices), len(results), sum(1 for r in results if r.emails))
        return results


# --------------------------------------------------------------------- cache

def lookup_key(kind: str, state: str | None, district: str | None, locality: str | None,
               office_name: str | None = None) -> str:
    parts = [kind, normalize_state(state) or (state or "").lower(), (district or "").lower(),
             (locality or "").lower() if kind in {"police_station", "cyber_crime"} else "",
             (office_name or "").lower()]
    normalized = "|".join(" ".join(re.sub(r"[^\w]+", " ", p).split()) for p in parts)
    return hashlib.sha256(normalized.encode()).hexdigest()


class ContactStore:
    def __init__(self, connection: Any):
        self.connection = connection

    def get(self, key: str) -> tuple[list[OfficeContact], str] | None:
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT "offices", "status", "checkedAt" FROM "authority_contacts" WHERE "lookupKey" = %s',
                           (key,))
            row = cursor.fetchone()
        except Exception:
            logger.warning("[FILINGS] authority_contacts unavailable", exc_info=True)
            self._rollback()
            return None
        if not row:
            return None
        offices, status, checked = (row["offices"], row["status"], row["checkedAt"]) if isinstance(row, dict) else row
        if isinstance(offices, str):
            offices = json.loads(offices)
        contacts = [OfficeContact.from_dict(o) for o in offices or []]
        if isinstance(checked, datetime):
            stamp = checked if checked.tzinfo else checked.replace(tzinfo=timezone.utc)
            ttl = CACHE_TTL if any(c.emails for c in contacts) else NO_EMAIL_CACHE_TTL
            if datetime.now(timezone.utc) - stamp > ttl:
                return None
        return contacts, status

    def put(self, key: str, *, kind: str, state: str | None, district: str | None, locality: str | None,
            offices: Sequence[OfficeContact], status: str) -> None:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                '''INSERT INTO "authority_contacts" ("lookupKey", "kind", "state", "district", "locality", "status",
                       "offices", "checkedAt", "createdAt", "updatedAt")
                   VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, NOW(), NOW(), NOW())
                   ON CONFLICT ("lookupKey") DO UPDATE SET "status" = EXCLUDED."status",
                       "offices" = EXCLUDED."offices", "checkedAt" = NOW(), "updatedAt" = NOW()''',
                (key, kind, state, district, locality, status, json.dumps([o.as_dict() for o in offices])),
            )
            self.connection.commit()
        except Exception:
            logger.warning("[FILINGS] could not cache contacts", exc_info=True)
            self._rollback()

    def _rollback(self) -> None:
        try:
            self.connection.rollback()
        except Exception:
            pass


@dataclass
class ContactResult:
    offices: list[OfficeContact] = field(default_factory=list)
    status: str = "NONE_FOUND"  # FOUND | NONE_FOUND | FAILED | CURATED
    cached: bool = False
