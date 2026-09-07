"""Hybrid retrieval, relevance scoring, and ranking for official Indian judgments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .query_understanding import (
    LegalIssueRepresentation,
    extract_legal_issues,
    STOPWORDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_DATA_PATH = REPO_ROOT / "web" / "data" / "legal" / "official-judgments.json"


@dataclass(frozen=True)
class RankedCaseResult:
    id: str
    title: str
    court: str
    court_level: str
    jurisdiction: str
    judgment_date: str
    case_number: str
    case_type: str
    citation: str
    legal_issue: str
    relevant_law: str
    why_relevant: str
    relevance_score: int
    relevance_level: str
    official_source: bool
    source_authority: str
    source_url: str
    source_type: str
    bench: str | None
    judge_names: tuple[str, ...]
    holding: str
    acts: tuple[str, ...]
    sections: tuple[str, ...]
    content_hash: str


def _stem_word(word: str) -> str:
    if len(word) <= 4:
        return word
    for suffix in ("ingly", "fully", "tions", "tion", "ments", "ment", "edly", "ing", "ed", "es", "ers", "er", "s"):
        if word.endswith(suffix):
            return word[:-len(suffix)].strip()
    return word


def _word_matches(haystack: str, word: str) -> bool:
    if word in haystack:
        return True
    stem = _stem_word(word)
    return len(stem) >= 3 and stem in haystack


def _extract_tokens(text: str) -> list[str]:
    import re
    words = [re.sub(r"[^\w]", "", w) for w in (text or "").lower().split() if w]
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def _load_official_judgments() -> list[dict[str, Any]]:
    if not OFFICIAL_DATA_PATH.exists():
        return []
    with open(OFFICIAL_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_CATALOG_CACHE: list[dict[str, Any]] | None = None


def get_official_judgments() -> list[dict[str, Any]]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        _CATALOG_CACHE = _load_official_judgments()
    return _CATALOG_CACHE


def _compute_issue_similarity(issue_rep: LegalIssueRepresentation, item: dict[str, Any]) -> float:
    query_issues = " ".join(issue_rep.issues).lower()
    holding = item.get("holding", "").lower()
    primary_issue = item.get("primary_issue", "").lower()
    topics = " ".join(item.get("legal_topics", ())).lower()

    query_tokens = _extract_tokens(query_issues)
    if not query_tokens:
        return 0.5

    matches = 0.0
    for token in query_tokens:
        if _word_matches(primary_issue, token):
            matches += 2.0
        elif _word_matches(holding, token):
            matches += 1.5
        elif _word_matches(topics, token):
            matches += 1.0

    max_possible = len(query_tokens) * 2.0
    return min(1.0, matches / max(1.0, max_possible))


def _compute_statute_match(issue_rep: LegalIssueRepresentation, item: dict[str, Any]) -> float:
    if not issue_rep.acts and not issue_rep.sections:
        return 0.5

    act_match = 0.0
    case_acts = [a.lower() for a in item.get("acts", ())]
    for q_act in issue_rep.acts:
        q_tokens = _extract_tokens(q_act)
        for ca in case_acts:
            c_tokens = _extract_tokens(ca)
            common = [t for t in q_tokens if t in c_tokens]
            if len(common) >= 2 or (len(q_tokens) == 1 and len(common) == 1):
                act_match = max(act_match, min(1.0, len(common) / max(len(q_tokens) - 1, 1)))

    sec_match = 0.0
    if issue_rep.sections:
        import re
        case_secs = [s.lower() for s in item.get("sections", ())]
        for q_sec in issue_rep.sections:
            norm = re.sub(r"[^\w]", "", q_sec.lower())
            if any(norm in re.sub(r"[^\w]", "", cs) for cs in case_secs):
                sec_match = 1.0
                break
        return act_match * 0.6 + sec_match * 0.4

    return act_match


def _compute_topic_match(issue_rep: LegalIssueRepresentation, item: dict[str, Any]) -> float:
    if issue_rep.domain == "UNKNOWN":
        return 0.5
    if issue_rep.domain != item.get("domain"):
        return 0.0

    score = 0.80
    case_topics = [t.lower() for t in item.get("legal_topics", ())]
    if any(any(_word_matches(ct, kw) for ct in case_topics) for kw in issue_rep.keywords):
        score += 0.20
    return min(1.0, score)


def _compute_fact_similarity(issue_rep: LegalIssueRepresentation, item: dict[str, Any]) -> float:
    if not issue_rep.facts:
        return 0.5

    haystack = f"{item.get('facts_summary', '')} {item.get('holding', '')}".lower()
    matches = 0.0
    for fact in issue_rep.facts:
        fact_tokens = _extract_tokens(fact)
        matched = [t for t in fact_tokens if _word_matches(haystack, t)]
        if matched:
            matches += len(matched) / max(1, len(fact_tokens))
    return min(1.0, matches / max(1, len(issue_rep.facts)))


def _compute_lexical_similarity(query_tokens: list[str], item: dict[str, Any]) -> float:
    if not query_tokens:
        return 0.5

    haystack = " ".join([
        item.get("title", ""),
        item.get("citation", "") or "",
        item.get("primary_issue", ""),
        item.get("holding", ""),
        *item.get("legal_topics", ()),
    ]).lower()

    hits = sum(1 for t in query_tokens if _word_matches(haystack, t))
    return min(1.0, hits / max(1, len(query_tokens)))


def _compute_court_authority(item: dict[str, Any], query_jurisdiction: str | None) -> float:
    if query_jurisdiction and item.get("jurisdiction") == query_jurisdiction:
        return 1.0
    level = item.get("court_level", "")
    if level == "SUPREME_COURT":
        return 1.0
    if level == "HIGH_COURT":
        return 0.88
    if level == "TRIBUNAL":
        return 0.80
    return 0.70


def _compute_recency_score(judgment_date: str) -> float:
    try:
        year = int(judgment_date[:4])
        if year >= 2020:
            return 1.0
        if year >= 2010:
            return 0.90
        if year >= 2000:
            return 0.82
        if year >= 1980:
            return 0.75
        return 0.65
    except Exception:
        return 0.75


def _classify_level(score: int) -> str:
    if score >= 90:
        return "Highly relevant"
    if score >= 75:
        return "Relevant"
    return "Potentially relevant"


def search_official_judgments(
    query: str,
    *,
    limit: int = 5,
    min_threshold: int = 60,
    filter_jurisdiction: str | None = None,
) -> list[RankedCaseResult]:
    if not query or not query.strip():
        return []

    issue_rep = extract_legal_issues(query)
    active_jurisdiction = filter_jurisdiction or issue_rep.jurisdiction
    catalog = get_official_judgments()
    query_tokens = _extract_tokens(query)

    seen = set()
    scored = []
    for item in catalog:
        chash = item.get("content_hash", item.get("id"))
        if chash in seen:
            continue
        seen.add(chash)

        issue_sim = _compute_issue_similarity(issue_rep, item)
        statute_sim = _compute_statute_match(issue_rep, item)
        topic_sim = _compute_topic_match(issue_rep, item)
        fact_sim = _compute_fact_similarity(issue_rep, item)
        lexical_sim = _compute_lexical_similarity(query_tokens, item)
        court_auth = _compute_court_authority(item, active_jurisdiction)
        recency = _compute_recency_score(item.get("judgment_date", ""))

        domain_penalty = 0.50 if (issue_rep.domain != "UNKNOWN" and item.get("domain") != issue_rep.domain) else 0.0

        raw_weighted = (
            issue_sim * 0.20
            + statute_sim * 0.15
            + topic_sim * 0.15
            + fact_sim * 0.20
            + lexical_sim * 0.10
            + court_auth * 0.10
            + recency * 0.10
            - domain_penalty
        )

        final_score = max(0, min(100, round(raw_weighted * 100)))
        if final_score >= min_threshold:
            scored.append((item, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for item, score in scored[:limit]:
        acts = tuple(item.get("acts", ()))
        sections = tuple(item.get("sections", ()))
        rel_law = " — ".join(filter(None, [", ".join(acts), ", ".join(sections)])) or "General Law"

        results.append(RankedCaseResult(
            id=item["id"],
            title=item["title"],
            court=item["court"],
            court_level=item.get("court_level", "SUPREME_COURT"),
            jurisdiction=item.get("jurisdiction", "NATIONAL"),
            judgment_date=item.get("judgment_date", ""),
            case_number=item.get("case_number", ""),
            case_type=item.get("case_type", "Civil Appeal"),
            citation=item.get("citation") or item.get("case_number", ""),
            legal_issue=item.get("primary_issue", ""),
            relevant_law=rel_law,
            why_relevant=item.get("why_relevant", ""),
            relevance_score=score,
            relevance_level=_classify_level(score),
            official_source=bool(item.get("official_source", True)),
            source_authority=item.get("source_authority", "Official Judiciary"),
            source_url=item.get("source_url", ""),
            source_type=item.get("source_type", "JUDGMENT"),
            bench=item.get("bench"),
            judge_names=tuple(item.get("judge_names", ())),
            holding=item.get("holding", ""),
            acts=acts,
            sections=sections,
            content_hash=item.get("content_hash", ""),
        ))

    return results
