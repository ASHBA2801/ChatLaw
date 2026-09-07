"""Domain-scoped retrieval helpers for cross-domain legal search."""

from __future__ import annotations

from typing import Sequence

try:
    from acts.catalog import get_catalog
except ImportError:
    get_catalog = None

from scenario.domain import route_domain


def resolve_search_domains(query: str) -> tuple[str, tuple[str, ...], float]:
    routing = route_domain(query)
    return routing.primary_domain, routing.secondary_domains, routing.confidence


def domain_act_ids(domains: Sequence[str]) -> frozenset[str]:
    if not get_catalog:
        return frozenset()
    catalog = get_catalog()
    act_ids: set[str] = set()
    for domain in domains:
        for entry in catalog.get_by_domain(domain):
            act_ids.add(entry.act_id)
    return frozenset(act_ids)


def build_domain_filter_sql(domains: Sequence[str]) -> tuple[str, list]:
    """Filter chunks whose metadata domain/domains overlap routed domains."""
    if not domains:
        return "", []
    placeholders = " OR ".join(
        [
            "c.metadata->>'domain' = %s",
            "c.metadata->'domains' ? %s",
        ]
        * len(domains)
    )
    params: list[str] = []
    for domain in domains:
        params.extend([domain, domain])
    return f" AND ({placeholders}) ", params
