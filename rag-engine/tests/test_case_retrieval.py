"""Tests for official case retrieval and relevance scoring engine."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cases.query_understanding import extract_legal_issues
from cases.retrieval import search_official_judgments, get_official_judgments


def test_official_catalog_has_required_metadata():
    catalog = get_official_judgments()
    assert len(catalog) >= 15
    for case in catalog:
        assert case["id"]
        assert case["title"]
        assert case["court"]
        assert case["official_source"] is True
        assert case["source_url"].startswith("https://")
        assert any(domain in case["source_url"] for domain in ["sci.gov.in", "delhihighcourt.nic.in", "hcmadras.tn.gov.in", "judgments.ecourts.gov.in", "ecourts.gov.in"])
        assert case["source_authority"]
        assert case["domain"] in ["CONSUMER", "EMPLOYMENT", "PROPERTY", "CONTRACT", "FAMILY", "CYBER", "IP", "TAX", "CRIMINAL", "ENVIRONMENT", "CONSTITUTIONAL"]
        assert case["holding"]
        assert case["primary_issue"]
        assert case["content_hash"]


def test_consumer_dispute_retrieval():
    query = "I bought a defective product from an e-commerce website and the seller refused to refund me."
    hits = search_official_judgments(query, limit=3)
    assert len(hits) > 0
    top = hits[0]
    assert any(expected in top.title for expected in ["SGS India", "Amazon", "Lucknow Development Authority"])
    assert top.relevance_score >= 70
    assert top.official_source is True


def test_tenancy_security_deposit_retrieval():
    query = "My landlord refuses to return my security deposit."
    hits = search_official_judgments(query, limit=3)
    assert len(hits) > 0
    top_titles = [h.title for h in hits]
    assert any("Thomas" in t or "Suresh Kumar" in t for t in top_titles)
    # Ensure domain isolation: must not return criminal theft
    assert not any("K.N. Mehra" in t or "Lalita" in t for t in top_titles)


def test_jurisdiction_aware_retrieval():
    query = "Can I challenge this property order in Tamil Nadu?"
    hits = search_official_judgments(query, limit=3)
    assert len(hits) > 0
    assert hits[0].jurisdiction == "TAMIL_NADU"
    assert "Madras" in hits[0].court


def test_irrelevant_query_threshold_rejection():
    query = "What is the recipe for biryani?"
    hits = search_official_judgments(query, min_threshold=60)
    assert len(hits) == 0
