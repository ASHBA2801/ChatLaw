"""Tests for Act Catalog and Act-aware metadata and routing."""

import pytest
from pathlib import Path

from acts.catalog import ActCatalog, ActCatalogEntry, get_catalog, load_catalog
from retrieval.reranker import (
    _DOCUMENT_ALIASES,
    document_alias_matches,
    extract_query_signals,
    normalize_document_alias,
)


def test_catalog_loads_successfully():
    catalog = get_catalog()
    assert len(catalog.all_entries()) >= 20
    assert catalog.get("BNS2023") is not None
    assert catalog.get("POCSO2012") is not None
    assert catalog.get("NDPS1985") is not None
    assert catalog.get("PCA1988") is not None


def test_catalog_find_by_alias():
    catalog = get_catalog()
    # Direct alias
    assert catalog.find_by_alias("pocso").act_id == "POCSO2012"
    assert catalog.find_by_alias("ndps").act_id == "NDPS1985"
    assert catalog.find_by_alias("pc act").act_id == "PCA1988"
    assert catalog.find_by_alias("posh").act_id == "POSH2013"
    assert catalog.find_by_alias("bns 2023").act_id == "BNS2023"
    assert catalog.find_by_alias("Bharatiya_Nagarik_Suraksha_Sanhita_2023").act_id == "BNSS2023"


def test_catalog_ingested_acts_count():
    catalog = get_catalog()
    ingested = catalog.get_ingested()
    assert len(ingested) == 3
    ingested_ids = {e.act_id for e in ingested}
    assert ingested_ids == {"BNS2023", "BNSS2023", "BSA"}


def test_catalog_priority_tiers():
    catalog = get_catalog()
    tier_1 = catalog.get_by_priority("tier_1")
    assert len(tier_1) >= 12
    tier_1_ids = {e.act_id for e in tier_1}
    assert "POCSO2012" in tier_1_ids
    assert "NDPS1985" in tier_1_ids
    assert "PCA1988" in tier_1_ids
    assert "ITACT2000" in tier_1_ids


def test_reranker_extracts_expanded_act_signals():
    # POCSO query
    signals_pocso = extract_query_signals("What is Section 4 of POCSO?")
    assert "POCSO2012" in signals_pocso.documents
    assert signals_pocso.sections == (("4", None),)

    # NDPS query
    signals_ndps = extract_query_signals("What is the punishment under NDPS act for contraband?")
    assert "NDPS1985" in signals_ndps.documents

    # PCA query
    signals_pca = extract_query_signals("prevention of corruption act section 7")
    assert "PCA1988" in signals_pca.documents
    assert signals_pca.sections == (("7", None),)


def test_existing_bns_signals_continue_working():
    signals = extract_query_signals("under Sec. 303(2) of BNS")
    assert signals.sections == (("303", "(2)"),)
    assert "BNS2023" in signals.documents
