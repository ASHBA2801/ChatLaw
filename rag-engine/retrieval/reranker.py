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
    concepts: tuple[str, ...] = ()
    domain_hints: frozenset[str] = frozenset()


STOPWORDS = frozenset(
    "a an and are as at be by can does for from how in is it made of on or the to under what which who with my me i".split()
)
LEGAL_TERMS = frozenset(
    "accused act arrest evidence offence offense punishment procedure provision section theft cheating murder hurt record records confession burden proof witness document documents electronic digital crime criminal legal law sanhita consumer defect defective goods refund refunding return replacement warranty e-commerce trader compensation redressal grievance service tenancy landlord tenant rent deposit contract breach salary employer employee".split()
)

# Built-in fallback alias table for zero-dependency execution
_BUILTIN_DOCUMENT_ALIASES = (
    ("BNS2023", ("bns", "bns 2023", "bharatiya nyaya sanhita", "bharatiya nyaya sanhita 2023", "the bharatiya nyaya sanhita, 2023")),
    ("BSA", ("bsa", "bsa 2023", "bharatiya sakshya adhiniyam", "bharatiya sakshya adhiniyam 2023", "the bharatiyasakshyaadhiniyam, 2023", "the bharatiya sakshya adhiniyam, 2023")),
    ("BNSS2023", ("bnss", "bnss 2023", "bharatiya nagarik suraksha sanhita", "bharatiya nagarik suraksha sanhita 2023", "the bharatiya nagarik suraksha sanhita, 2023", "bharatiya nagarik suraksha sanhita 2023")),
    ("POCSO2012", ("pocso", "pocso act", "pocso 2012", "protection of children from sexual offences act", "protection of children from sexual offences act 2012")),
    ("NDPS1985", ("ndps", "ndps act", "ndps 1985", "narcotic drugs and psychotropic substances act", "narcotic drugs act")),
    ("PCA1988", ("pca", "pc act", "prevention of corruption act", "prevention of corruption act 1988", "anti corruption act", "anti-corruption act", "corruption act")),
    ("CPA2019", ("cpa", "cpa 2019", "consumer protection act", "consumer protection act 2019", "the consumer protection act, 2019")),
    ("ICA1872", ("ica", "ica 1872", "indian contract act", "contract act", "the indian contract act, 1872")),
    ("ITACT2000", ("it act", "it act 2000", "information technology act", "information technology act 2000", "the information technology act, 2000")),
    ("POSH2013", ("posh", "posh act", "posh 2013", "sexual harassment of women at workplace act", "workplace harassment act")),
    ("DVACT2005", ("dv act", "domestic violence act", "pwdva", "pwdv act", "protection of women from domestic violence act")),
    ("JJACT2015", ("jj act", "jj act 2015", "juvenile justice act", "juvenile justice care and protection of children act")),
    ("SCSTPOA1989", ("sc st act", "sc st poa act", "prevention of atrocities act", "sc st prevention of atrocities act", "atrocities act")),
    ("PMLA2002", ("pmla", "pmla 2002", "prevention of money laundering act", "money laundering act")),
    ("MVA1988", ("mva", "mva 1988", "motor vehicles act", "motor vehicles act 1988", "motor vehicle act")),
    ("RAILWAYS1989", ("railways act", "railway act", "the railways act", "the railways act 1989", "railways act 1989", "railway act 1989", "indian railways act", "indian railways act 1989")),
    ("COMPANIES2013", ("companies act", "companies act 2013", "company law")),
    ("IBC2016", ("ibc", "ibc 2016", "insolvency and bankruptcy code", "insolvency and bankruptcy code 2016")),
    ("NIACT1881", ("ni act", "ni act 1881", "negotiable instruments act", "negotiable instruments act 1881", "section 138 ni act")),
    ("TPA1882", ("tpa", "tp act", "transfer of property act", "transfer of property act 1882")),
    ("SRA1963", ("sra", "specific relief act", "specific relief act 1963")),
    ("LIMITATION1963", ("limitation act", "limitation act 1963")),
    ("REGISTRATION1908", ("registration act", "registration act 1908", "indian registration act")),
    ("ARBITRATION1996", ("arbitration act", "arbitration and conciliation act", "arbitration act 1996")),
    ("RTI2005", ("rti", "rti act", "rti 2005", "right to information act", "right to information act 2005")),
    ("DPDP2023", ("dpdp", "dpdp act", "dpdp 2023", "digital personal data protection act", "data protection act")),
)

def _get_document_aliases() -> tuple[tuple[str, tuple[str, ...]], ...]:
    try:
        from acts.catalog import get_catalog
        catalog = get_catalog()
        table = catalog.get_document_aliases_table()
        if table:
            return table
    except Exception:
        pass
    return _BUILTIN_DOCUMENT_ALIASES

_DOCUMENT_ALIASES = _get_document_aliases()


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


def extract_query_signals(query: str, extra_concepts: Iterable[str] | None = None) -> QuerySignals:
    normalized = " ".join(unicodedata.normalize("NFKC", query or "").lower().split())
    sections: list[tuple[str, str | None]] = []
    patterns = (
        r"\b(?:section|sec)\s*\.?\s*(\d+[a-z]?)\s*(?:\(\s*([\w]+)\s*\))?",
        r"\b(\d+[a-z]?)\s+of\s+(?:the\s+)?(?:bns|bsa|bnss|cpa|ica)\b",
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
    
    # Extract concepts deterministically from concepts dictionary if available
    concepts: list[str] = list(extra_concepts or [])
    try:
        from scenario.concepts import extract_matching_concepts
        from scenario.domain import route_domain
        matched = extract_matching_concepts(query)
        for m in matched:
            concepts.append(m.canonical_term)
            for t in m.expanded_terms:
                words.update(re.findall(r"\b[a-z][a-z0-9-]+\b", t.lower()))
        domain_res = route_domain(query)
        domain_hints = frozenset([domain_res.primary_domain] + list(domain_res.secondary_domains))
    except ImportError:
        domain_hints = frozenset()

    keywords = frozenset(word for word in words if word not in STOPWORDS and (len(word) > 2 or word in LEGAL_TERMS))
    return QuerySignals(tuple(sections), documents, keywords, tuple(concepts), domain_hints)


def keyword_score(query_keywords: Iterable[str], content: str) -> float:
    keywords = set(query_keywords)
    if not keywords:
        return 0.0
    content_words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", normalize_text(content)))
    return len(keywords & content_words) / len(keywords)


def concept_score(signals: QuerySignals, result: RetrievalResult) -> float:
    if not signals.concepts:
        return 0.0
    content_norm = normalize_text(result.content)
    title_norm = normalize_text(result.document_title)
    hits = 0
    for concept in signals.concepts:
        norm_concept = normalize_text(concept)
        if norm_concept in content_norm or norm_concept in title_norm:
            hits += 1
    return min(1.0, hits / max(1, len(signals.concepts)))


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


def domain_score(signals: QuerySignals, result: RetrievalResult) -> float:
    if not signals.domain_hints:
        return 0.0
    meta = result.metadata if isinstance(result.metadata, dict) else {}
    chunk_domain = str(meta.get("domain") or "")
    chunk_domains = meta.get("domains") or []
    if isinstance(chunk_domains, str):
        chunk_domains = [chunk_domains]
    matched = chunk_domain in signals.domain_hints or any(d in signals.domain_hints for d in chunk_domains)
    return 1.0 if matched else 0.0


def rerank_score(signals: QuerySignals, result: RetrievalResult, weights: RerankWeights) -> RetrievalResult:
    keyword = keyword_score(signals.keywords, result.content)
    concept = concept_score(signals, result)
    section = section_score(signals, result)
    document = document_score(signals, result)
    domain = domain_score(signals, result)
    effective_keyword = max(keyword, concept * 0.85) if concept > 0 else keyword
    final = (
        result.similarity * weights.vector
        + effective_keyword * weights.keyword
        + section * weights.section
        + document * weights.document
        + domain * 0.05
    )
    return result.with_scores(
        keyword_score=keyword,
        section_score=section,
        document_score=document,
        concept_score=concept,
        rerank_score=final,
    )


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
