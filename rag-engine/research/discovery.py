"""Find judgments with Gemini + Google Search grounding, then keep only verified ones.

The official search portals (sci.gov.in, judgments.ecourts.gov.in) sit behind
CAPTCHAs, so discovery uses grounded web search instead of scraping them. The
model proposes cases; nothing is returned unless an official government copy
of the judgment is downloaded and names the parties (see verification.py).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Sequence

from .verification import LinkVerification, is_official_url, verify_judgment_link

logger = logging.getLogger(__name__)

COURT_LEVELS = ("SUPREME_COURT", "HIGH_COURT", "DISTRICT_COURT", "TRIBUNAL")
_COURT_LEVEL_LABELS = {
    "SUPREME_COURT": "the Supreme Court of India",
    "HIGH_COURT": "the High Courts",
    "DISTRICT_COURT": "District and Sessions Courts",
    "TRIBUNAL": "national tribunals and commissions (NCDRC, NCLAT, ITAT, NGT)",
}
_MAX_GROUNDED_URLS = 8
# Where official judgment copies actually live today. digiscr.sci.gov.in no
# longer resolves and main.sci.gov.in has moved to api.sci.gov.in.
_OFFICIAL_URL_GUIDE = (
    "Supreme Court judgments are published at https://api.sci.gov.in/supremecourt/<year>/<diary no>/<file>.pdf "
    "(about 2009 onwards) and https://api.sci.gov.in/jonew/judis/<id>.pdf (older judgments). "
    "Do not use digiscr.sci.gov.in or main.sci.gov.in links; those hosts no longer work. "
    "High Court judgments are on the High Court's own *.nic.in or *.gov.in website or judgments.ecourts.gov.in."
)


@dataclass(frozen=True)
class CandidateCase:
    title: str
    court: str
    court_level: str
    judgment_date: str | None
    citation: str | None
    case_number: str | None
    petitioner: str | None
    respondent: str | None
    official_url: str | None
    summary: str
    holding: str
    relevance: str
    provisions: tuple[str, ...] = ()
    predecessor_provision: str | None = None
    verification: LinkVerification | None = None

    @property
    def verified(self) -> bool:
        return bool(self.verification and self.verification.verified)


@dataclass
class DiscoveryResult:
    cases: list[CandidateCase]
    rejected: list[CandidateCase] = field(default_factory=list)
    model: str | None = None
    latency_seconds: float = 0.0


def parse_json_payload(text: str) -> Any:
    """Parse the JSON a model returned, tolerating code fences and stray prose."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


def _clean(value: Any, limit: int = 2000) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text or text.lower() in {"null", "none", "unknown", "n/a", "not available"}:
        return None
    return text[:limit]


def _normalize_date(value: Any) -> str | None:
    text = _clean(value, 40)
    if not text:
        return None
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return match.group(0)
    match = re.match(r"(\d{4})$", text)
    return f"{match.group(1)}-01-01" if match else None


def candidates_from_payload(payload: Any) -> list[CandidateCase]:
    items = payload.get("cases", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    candidates: list[CandidateCase] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = _clean(item.get("title"), 300)
        court = _clean(item.get("court"), 200)
        holding = _clean(item.get("holding"))
        if not title or not court or not holding:
            continue
        level = (_clean(item.get("court_level"), 40) or "").upper().replace(" ", "_")
        if level not in COURT_LEVELS:
            level = "SUPREME_COURT" if "supreme" in court.lower() else (
                "HIGH_COURT" if "high court" in court.lower() else "DISTRICT_COURT")
        provisions = item.get("provisions") or []
        candidates.append(CandidateCase(
            title=title,
            court=court,
            court_level=level,
            judgment_date=_normalize_date(item.get("judgment_date")),
            citation=_clean(item.get("citation"), 200),
            case_number=_clean(item.get("case_number"), 200),
            petitioner=_clean(item.get("petitioner"), 300),
            respondent=_clean(item.get("respondent"), 300),
            official_url=_clean(item.get("official_url"), 1000),
            summary=_clean(item.get("summary")) or holding,
            holding=holding,
            relevance=_clean(item.get("relevance")) or "",
            provisions=tuple(p for p in (_clean(x, 120) for x in provisions if x) if p)[:8]
            if isinstance(provisions, list) else (),
            predecessor_provision=_clean(item.get("predecessor_provision"), 120),
        ))
    return candidates


_CASE_SCHEMA = (
    '{"title": "Petitioner v. Respondent", "court": "full court name", '
    '"court_level": "SUPREME_COURT|HIGH_COURT|DISTRICT_COURT|TRIBUNAL", '
    '"judgment_date": "YYYY-MM-DD", "citation": "neutral or reporter citation", '
    '"case_number": "e.g. Civil Appeal No. 123 of 2020", "petitioner": "...", "respondent": "...", '
    '"official_url": "URL of the judgment on an official government website, or null", '
    '"provisions": ["Section ... of ..."], "predecessor_provision": "IPC/CrPC/Evidence Act section if the case was decided under it, else null", '
    '"summary": "2-3 sentences: facts and question decided", '
    '"holding": "what the court held, 1-3 sentences", '
    '"relevance": "one sentence on why it matters for the research topic"}'
)


def build_discovery_prompt(*, topic: str, provisions_context: str, court_levels: Sequence[str],
                           max_cases: int, landmark: bool) -> str:
    courts = ", ".join(_COURT_LEVEL_LABELS[level] for level in court_levels if level in _COURT_LEVEL_LABELS)
    goal = (
        "the landmark and most frequently cited judgments that interpret this provision"
        if landmark else
        "the judgments most useful for researching this question"
    )
    return f"""You are an Indian legal research assistant. Use Google Search to find {goal}.

Research topic:
{topic}

Statutory text (from the official Act):
{provisions_context or "(not available)"}

Rules:
- Find up to {max_cases} real judgments from {courts}.
- Every case must be a real, reported judgment you found in search results. Never invent a case, citation, date or URL.
- The Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita and Bharatiya Sakshya Adhiniyam replaced the IPC, CrPC and Indian Evidence Act in July 2024. Judgments under the corresponding old provision are acceptable when the principle carries over; record the old provision in predecessor_provision.
- official_url must point to the judgment itself (PDF or judgment page) on an official Indian government website. {_OFFICIAL_URL_GUIDE} Use null if you did not find one. Do not use indiankanoon, scconline, livelaw, casemine or other private sites.
- Prefer authoritative and recent judgments; include older landmark judgments when they are still the leading authority.

Return ONLY a JSON array (no prose) of objects shaped like:
{_CASE_SCHEMA}
"""


def build_link_prompt(case: CandidateCase) -> str:
    details = ", ".join(x for x in (case.court, case.judgment_date, case.citation, case.case_number) if x)
    return (
        f"Find the official copy of the Indian judgment {case.title} ({details}). {_OFFICIAL_URL_GUIDE} "
        "Reply with only the direct URL of the judgment PDF or page on an official government website, "
        "or NONE if you cannot find it. Never guess a URL."
    )


_URL_RE = re.compile(r"https://[^\s)\]\"'<>]+")


class CaseDiscovery:
    """Grounded case search. `client` is a google-genai Client (injectable for tests)."""

    link_budget_seconds = 45.0

    def __init__(self, client: Any = None, *, model: str | None = None,
                 verify: Callable[..., LinkVerification] = verify_judgment_link,
                 resolve_redirect: Callable[[str], str | None] | None = None):
        self.model = model or os.getenv("GEMINI_RESEARCH_MODEL", "").strip() or os.getenv(
            "GEMINI_GENERATION_MODEL", "").strip()
        if not self.model:
            raise ValueError("GEMINI_GENERATION_MODEL is required for case discovery")
        if client is None:
            client = _default_client()
        self._client = client
        self._verify = verify
        self._resolve_redirect = resolve_redirect or _resolve_grounding_redirect

    def _generate(self, prompt: str) -> tuple[str, list[str]]:
        from google.genai import types  # type: ignore

        config: dict[str, Any] = {
            "tools": [types.Tool(google_search=types.GoogleSearch())],
            "temperature": 0.0,
        }
        thinking = os.getenv("GEMINI_RESEARCH_THINKING_LEVEL", "low").strip()
        if thinking and self.model.startswith("gemini-3"):
            config["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)
        response = self._client.models.generate_content(
            model=self.model, contents=prompt, config=types.GenerateContentConfig(**config),
        )
        return response.text or "", self._official_grounding_urls(response)

    def _official_grounding_urls(self, response: Any) -> list[str]:
        """Official pages Google actually returned while grounding the answer."""
        urls: list[str] = []
        try:
            chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
        except (AttributeError, IndexError, TypeError):
            return urls
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            title = (getattr(web, "title", "") or "").lower()
            uri = getattr(web, "uri", None)
            if not uri or not title.endswith((".gov.in", ".nic.in")):
                continue
            resolved = uri if is_official_url(uri) else self._resolve_redirect(uri)
            if resolved and is_official_url(resolved) and resolved not in urls:
                urls.append(resolved)
            if len(urls) >= _MAX_GROUNDED_URLS:
                break
        return urls

    def verify_case(self, case: CandidateCase, fallback_urls: Sequence[str] = ()) -> CandidateCase:
        """Check the case's own link, then each fallback URL; keep the first verified one."""
        attempts: list[LinkVerification] = []
        for url in ([case.official_url] if case.official_url else []) + list(fallback_urls):
            result = self._verify(url, title=case.title, petitioner=case.petitioner,
                                  respondent=case.respondent)
            attempts.append(result)
            if result.verified:
                return replace(case, official_url=result.url, verification=result)
        return replace(case, verification=attempts[0] if attempts else None)

    def _verify_all(self, cases: Sequence[CandidateCase], fallback_urls: Sequence[str]) -> list[CandidateCase]:
        if not cases:
            return []
        with ThreadPoolExecutor(max_workers=min(6, len(cases))) as pool:
            return list(pool.map(lambda case: self.verify_case(case, fallback_urls), cases))

    def discover(self, *, topic: str, provisions_context: str = "",
                 court_levels: Sequence[str] = COURT_LEVELS, max_cases: int = 6,
                 landmark: bool = False, link_budget_seconds: float | None = None) -> DiscoveryResult:
        started = time.perf_counter()
        levels = [level for level in court_levels if level in COURT_LEVELS] or list(COURT_LEVELS)
        text, grounded = self._generate(build_discovery_prompt(
            topic=topic, provisions_context=provisions_context[:6000], court_levels=levels,
            max_cases=max_cases, landmark=landmark,
        ))
        try:
            candidates = candidates_from_payload(parse_json_payload(text))
        except (json.JSONDecodeError, ValueError):
            logger.warning("[RESEARCH] discovery returned unparseable output")
            candidates = []
        candidates = [case for case in candidates if case.court_level in levels][:max_cases]

        checked = self._verify_all(candidates, grounded)
        unresolved = [case for case in checked if not case.verified]
        if unresolved:
            checked = [case for case in checked if case.verified] + self._resolve_links(
                unresolved, link_budget_seconds)

        verified = [case for case in checked if case.verified]
        rejected = [case for case in checked if not case.verified]
        logger.info("[RESEARCH] discovery: %d proposed, %d verified (%.1fs)",
                    len(candidates), len(verified), time.perf_counter() - started)
        return DiscoveryResult(verified, rejected, self.model, time.perf_counter() - started)

    def _resolve_links(self, cases: Sequence[CandidateCase],
                       budget: float | None = None) -> list[CandidateCase]:
        """Search for each case's official copy separately; give up when the budget runs out."""
        if budget is None:
            budget = float(os.getenv("RESEARCH_LINK_SEARCH_BUDGET_SECONDS", str(self.link_budget_seconds)))
        pool = ThreadPoolExecutor(max_workers=min(6, len(cases)))
        futures = [pool.submit(self.find_official_copy, case) for case in cases]
        done, _ = wait(futures, timeout=budget)
        pool.shutdown(wait=False, cancel_futures=True)
        resolved = []
        for case, future in zip(cases, futures):
            if future in done and future.exception() is None:
                resolved.append(future.result())
            else:
                resolved.append(case)
        return resolved

    def find_official_copy(self, case: CandidateCase) -> CandidateCase:
        """Run a grounded search for this one judgment's official copy and verify what it finds."""
        text, grounded = self._generate(build_link_prompt(case))
        proposed = [url for url in _URL_RE.findall(text) if is_official_url(url)]
        return self.verify_case(replace(case, official_url=None), [*proposed, *grounded])


def _default_client() -> Any:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for case discovery")
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    timeout = float(os.getenv("GEMINI_RESEARCH_TIMEOUT_SECONDS", "90"))
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout * 1000)))


def _resolve_grounding_redirect(uri: str) -> str | None:
    """Grounding chunks point at a Google redirect; read its Location without following it."""
    import httpx

    try:
        response = httpx.get(uri, follow_redirects=False, timeout=10.0)
        return response.headers.get("location")
    except httpx.HTTPError:
        return None
