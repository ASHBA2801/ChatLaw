"""ChatLaw scenario analysis, legal concept mapping, and deterministic query expansion."""

from .analyzer import ScenarioAnalysis, ScenarioFacts, analyze_scenario, is_direct_lookup, is_scenario_query
from .concepts import CONCEPT_MAPPINGS, ConceptMapping, extract_matching_concepts, get_synonyms_for_term
from .domain import DOMAINS_REGISTRY, DomainDefinition, DomainRoutingResult, route_domain
from .expansion import ExpandedQuery, expand_query

__all__ = [
    "CONCEPT_MAPPINGS",
    "ConceptMapping",
    "DOMAINS_REGISTRY",
    "DomainDefinition",
    "DomainRoutingResult",
    "ExpandedQuery",
    "ScenarioAnalysis",
    "ScenarioFacts",
    "analyze_scenario",
    "expand_query",
    "extract_matching_concepts",
    "get_synonyms_for_term",
    "is_direct_lookup",
    "is_scenario_query",
    "route_domain",
]
