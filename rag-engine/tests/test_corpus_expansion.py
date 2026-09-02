"""Tests for corpus expansion architecture."""

import json
from pathlib import Path

import pytest

from acts.catalog import get_catalog, reset_catalog_cache as reset_catalog
from retrieval.domain_search import resolve_search_domains
from retrieval.version_filter import chunk_applicable_on, parse_as_of_date
from scenario.domain import route_domain


@pytest.fixture(autouse=True)
def _fresh_catalog():
    reset_catalog()
    yield
    reset_catalog()


def test_catalog_v2_has_domains_and_by_domain_index():
    catalog_path = Path(__file__).resolve().parents[2] / "legal_corpus" / "acts" / "catalog.json"
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert data["version"] == "2.0"
    assert "by_domain" in data
    assert len(data["acts"]) >= 60
    entry = next(a for a in data["acts"] if a["act_id"] == "BSA")
    assert "evidence" in entry.get("domains", [])


def test_get_by_domain_matches_secondary_domains():
    catalog = get_catalog()
    env_acts = catalog.get_by_domain("environment")
    assert any(e.act_id == "EPA1986" for e in env_acts)


def test_route_environment_query():
    result = route_domain("A factory discharged effluent into the river")
    assert result.primary_domain in ("environment", "general_legal", "criminal_law")


def test_route_gst_query():
    result = route_domain("Can I claim input tax credit on office rent?")
    assert result.primary_domain == "tax"


def test_version_filter_repealed_income_tax_1961_after_2026():
    as_of = parse_as_of_date("What is the income tax rate today?")
    assert as_of.year >= 2026
    meta_repealed = {
        "status": "repealed",
        "effective_from": "1962-04-01",
        "effective_to": "2026-03-31",
    }
    assert chunk_applicable_on(as_of, meta_repealed) is False


def test_version_filter_historical_query_includes_1961():
    as_of = parse_as_of_date("income tax act 1961 assessment year 2024-25")
    meta_repealed = {
        "status": "repealed",
        "effective_from": "1962-04-01",
        "effective_to": "2026-03-31",
    }
    assert chunk_applicable_on(as_of, meta_repealed) is True


def test_inventory_file_exists():
    inventory = Path(__file__).resolve().parents[2] / "data" / "evaluation" / "legal_corpus_inventory.json"
    assert inventory.is_file()
    data = json.loads(inventory.read_text(encoding="utf-8"))
    assert data["summary"]["total_catalog_acts"] >= 60


def test_multi_domain_eval_dataset():
    path = Path(__file__).resolve().parents[2] / "data" / "evaluation" / "multi_domain_questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["questions"]) >= 15
