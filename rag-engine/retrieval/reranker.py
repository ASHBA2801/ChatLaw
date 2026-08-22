"""Deterministic legal-aware reranking for vector-search candidates."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from .models import RetrievalResult


@dataclass(frozen=True)
class RerankWeights:
    vector: float = 0.70
    keyword: float = 0.15
    section: float = 0.10
    document: float = 0.05

    def __post_init__(self) -> None:
        values = (self.vector, self.keyword, self.section, self.document)
        if any(value < 0 for value in values) or sum(values) <= 0:
            raise ValueError("rerank weights must be non-negative and not all zero")


@dataclass(frozen=True)
class QuerySignals:
    sections: tuple[tuple[str, str | None], ...]
    documents: frozenset[str]
    keywords: frozenset[str]


STOPWORDS = frozenset(
    "a an and are as at be by can does for from how in is it made of on or the to under what which who with".split()
)
LEGAL_TERMS = frozenset(
    "accused act arrest evidence offence offense punishment procedure provision section theft cheating murder hurt record records confession burden proof witness document documents electronic digital crime criminal legal law sanhita".split()
)

_DOCUMENT_ALIASES = (
    ("BNS2023", ("bns", "bns 2023", "bharatiya nyaya sanhita", "bharatiya nyaya sanhita 2023")),
    ("BSA", ("bsa", "bsa 2023", "bharatiya sakshya adhiniyam", "bharatiya sakshya adhiniyam 2023")),
    ("BNSS2023", ("bnss", "bnss 2023", "bharatiya nagarik suraksha sanhita", "bharatiya nagarik suraksha sanhita 2023")),
)


def normalize_text(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)


def normalize_document_alias(value: str | None) -> str | None:
    normalized = " ".join(normalize_text(value).replace("_", " ").split())
    if normalized.startswith("the "):
        normalized = normalized[4:]
    for canonical, aliases in _DOCUMENT_ALIASES:
        if normalized == normalize_text(canonical):
            return canonical
        if normalized in aliases:
            return canonical
    if normalized:
        return normalized
    return None


def document_alias_matches(value: str | None, canonical: str) -> bool:
    normalized = " ".join(normalize_text(value).replace("_", " ").split())
    if normalized.startswith("the "):
        normalized = normalized[4:]
    target = normalize_text(canonical)
    if normalized == target or normalized == target.replace("2023", " 2023"):
        return True
    return normalize_document_alias(value) == canonical


def extract_query_signals(query: str) -> QuerySignals:
    normalized = " ".join(unicodedata.normalize("NFKC", query or "").lower().split())
    sections: list[tuple[str, str | None]] = []
    patterns = (
        r"\b(?:section|sec)\s*\.?\s*(\d+[a-z]?)\s*(?:\(\s*([\w]+)\s*\))?",
        r"\b(\d+[a-z]?)\s+of\s+(?:the\s+)?(?:bns|bsa|bnss)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            section = match.group(1)
            subsection = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            item = (section, f"({subsection})" if subsection else None)
            if item not in sections:
                sections.append(item)
    documents = frozenset(
        canonical for canonical, aliases in _DOCUMENT_ALIASES
        if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases)
    )
    words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", normalized))
    keywords = frozenset(word for word in words if word not in STOPWORDS and (len(word) > 2 or word in LEGAL_TERMS))
    return QuerySignals(tuple(sections), documents, keywords)


def keyword_score(query_keywords: Iterable[str], content: str) -> float:
    keywords = set(query_keywords)
    if not keywords:
        return 0.0
    content_words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", normalize_text(content)))
    return len(keywords & content_words) / len(keywords)


def section_score(signals: QuerySignals, result: RetrievalResult) -> float:
    if not signals.sections:
        return 0.0
    result_section = normalize_text(result.section_number).replace(" ", "")
    for section, subsection in signals.sections:
        if result_section != section:
            continue
        candidate_subsection = re.sub(r"[^a-z0-9]", "", normalize_text(result.subsection))
        requested_subsection = re.sub(r"[^a-z0-9]", "", normalize_text(subsection))
        if subsection and candidate_subsection == requested_subsection:
            return 1.0
        return 0.85 if subsection else 1.0
    return 0.0


def document_score(signals: QuerySignals, result: RetrievalResult) -> float:
    if not signals.documents:
        return 0.0
    if any(document_alias_matches(result.metadata.get("source_document_id"), document) for document in signals.documents):
        return 1.0
    return 1.0 if any(document_alias_matches(result.document_title, document) for document in signals.documents) else 0.0


def rerank_score(signals: QuerySignals, result: RetrievalResult, weights: RerankWeights) -> RetrievalResult:
    keyword = keyword_score(signals.keywords, result.content)
    section = section_score(signals, result)
    document = document_score(signals, result)
    final = result.similarity * weights.vector + keyword * weights.keyword + section * weights.section + document * weights.document
    return result.with_scores(keyword_score=keyword, section_score=section, document_score=document, rerank_score=final)


def deduplicate(results: Iterable[RetrievalResult]) -> list[RetrievalResult]:
    selected: list[RetrievalResult] = []
    seen_content: set[str] = set()
    for result in results:
        content_key = " ".join(normalize_text(result.content).split())
        if content_key and content_key in seen_content:
            continue
        seen_content.add(content_key)
        selected.append(result)
    return selected


def rerank(results: Iterable[RetrievalResult], query: str, weights: RerankWeights | None = None) -> list[RetrievalResult]:
    resolved_weights = weights or RerankWeights()
    signals = extract_query_signals(query)
    scored = [rerank_score(signals, result, resolved_weights) for result in results]
    scored.sort(key=lambda result: (result.rerank_score, result.similarity, -result.chunk_index), reverse=True)
    return deduplicate(scored)
