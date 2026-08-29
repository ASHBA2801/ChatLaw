"""Deterministic legal query expansion for scenario-based questions.

Enriches natural-language queries with statutory terminology, domain concepts,
and legal synonyms while preserving the user's original factual context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from .analyzer import ScenarioAnalysis, ScenarioFacts, analyze_scenario
from .concepts import extract_matching_concepts, get_synonyms_for_term
from .domain import DOMAINS_REGISTRY


@dataclass(frozen=True)
class ExpandedQuery:
    original_query: str
    expanded_query: str
    legal_concepts: tuple[str, ...]
    concept_keywords: frozenset[str]
    primary_domain: str
    primary_domain_name: str
    secondary_domains: tuple[str, ...]
    scenario_facts: ScenarioFacts
    is_scenario: bool
    is_legal_query: bool


def expand_query(query: str, analysis: ScenarioAnalysis | None = None) -> ExpandedQuery:
    """Expand a query deterministically with legal terminology and domain concepts."""
    actual_analysis = analysis or analyze_scenario(query)
    original = actual_analysis.original_query

    if not actual_analysis.is_legal_query or not original:
        return ExpandedQuery(
            original_query=original,
            expanded_query=original,
            legal_concepts=(),
            concept_keywords=frozenset(),
            primary_domain="general_legal",
            primary_domain_name="General Legal",
            secondary_domains=(),
            scenario_facts=ScenarioFacts(),
            is_scenario=False,
            is_legal_query=actual_analysis.is_legal_query,
        )

    # If it's a direct legal query (e.g., "What is Section 303 of BNS?"), keep query clean with minimal statutory hints
    if not actual_analysis.is_scenario:
        matched = extract_matching_concepts(original)
        concept_terms: list[str] = []
        for m in matched:
            concept_terms.extend(m.expanded_terms)
        words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", " ".join(concept_terms).lower()))
        return ExpandedQuery(
            original_query=original,
            expanded_query=original,
            legal_concepts=actual_analysis.matched_concepts,
            concept_keywords=frozenset(words),
            primary_domain=actual_analysis.domain_routing.primary_domain,
            primary_domain_name=actual_analysis.domain_routing.primary_domain_name,
            secondary_domains=actual_analysis.domain_routing.secondary_domains,
            scenario_facts=actual_analysis.facts,
            is_scenario=False,
            is_legal_query=True,
        )

    # For scenario queries: build deterministic legal expansion
    expansion_parts: list[str] = []

    # 1. Primary domain display name and legal theme
    domain_id = actual_analysis.domain_routing.primary_domain
    domain_def = DOMAINS_REGISTRY.get(domain_id)
    if domain_def:
        expansion_parts.append(domain_def.display_name.lower())
        expansion_parts.extend(list(domain_def.acts_and_statutes))

    # 2. Matched concept canonical terms and expanded legal synonyms
    matched_mappings = extract_matching_concepts(original)
    concept_terms: list[str] = []
    for mapping in matched_mappings:
        expansion_parts.append(mapping.canonical_term)
        for term in mapping.expanded_terms:
            expansion_parts.append(term)
            concept_terms.append(term)

    # 3. Secondary domain hints if confidence is shared
    for sec_id in actual_analysis.domain_routing.secondary_domains:
        sec_def = DOMAINS_REGISTRY.get(sec_id)
        if sec_def:
            expansion_parts.append(sec_def.display_name.lower())

    # 4. Dedup and build clean expanded query text
    seen: set[str] = set()
    deduped_expansion: list[str] = []
    for item in expansion_parts:
        norm = " ".join(item.strip().lower().split())
        if norm and norm not in seen:
            seen.add(norm)
            deduped_expansion.append(norm)

    expansion_string = " ".join(deduped_expansion)
    # Combined representation: Original natural language + deterministic legal concepts
    combined_expanded_query = f"{original} {expansion_string}".strip()

    # Build concept keywords for hybrid lexical/keyword scoring
    all_expansion_text = f"{original} {expansion_string}".lower()
    words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", all_expansion_text))
    # Exclude common stopwords
    stopwords = frozenset("a an and are as at be by can does for from how in is it made of on or the to under what which who with my me i".split())
    concept_keywords = frozenset(w for w in words if len(w) > 2 and w not in stopwords)

    return ExpandedQuery(
        original_query=original,
        expanded_query=combined_expanded_query,
        legal_concepts=actual_analysis.matched_concepts,
        concept_keywords=concept_keywords,
        primary_domain=actual_analysis.domain_routing.primary_domain,
        primary_domain_name=actual_analysis.domain_routing.primary_domain_name,
        secondary_domains=actual_analysis.domain_routing.secondary_domains,
        scenario_facts=actual_analysis.facts,
        is_scenario=True,
        is_legal_query=True,
    )
