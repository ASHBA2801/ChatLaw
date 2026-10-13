"""Tests for the Research tab backend: law references, link verification, discovery, caching."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research import verification
from research.discovery import CandidateCase, CaseDiscovery, candidates_from_payload, parse_json_payload
from research.law_reference import base_section, extract_law_references
from research.service import ResearchService, query_key, valid_law_keys
from research.store import StoredCase
from research.verification import (
    LinkVerification,
    is_official_url,
    normalize_official_url,
    parties_match,
    url_variants,
    verify_judgment_link,
)


def keys(query: str) -> list[str]:
    return [ref.law_key for ref in extract_law_references(query)]


# --------------------------------------------------------------- law references

@pytest.mark.parametrize("query, expected", [
    ("Section 103 BNS murder", ["BNS2023:103"]),
    ("divorce under section 13(1)(ia) of the Hindu Marriage Act", ["HMA1955:13"]),
    ("s. 2(7) Consumer Protection Act, 2019", ["CPA2019:2"]),
    ("BNS 64 and BNSS section 183", ["BNS2023:64", "BNSS2023:183"]),
    ("The Bharatiya Nyaya Sanhita, 2023 section 64", ["BNS2023:64"]),
    ("Constitution of India — Articles 14, 15, 19, 21",
     ["CONSTITUTION:14", "CONSTITUTION:15", "CONSTITUTION:19", "CONSTITUTION:21"]),
    ("Article 21 right to privacy", ["CONSTITUTION:21"]),
    ("compensation under section 124A railways act", ["RAILWAYS1989:124A"]),
    ("Code on Wages minimum wage", ["COW2019"]),
    ("landlord refuses to return my security deposit", []),
])
def test_extracts_law_keys(query, expected):
    assert keys(query) == expected


def test_repealed_codes_map_to_new_sanhitas():
    ref = extract_law_references("IPC 498A cruelty by husband")[0]
    assert ref.law_key == "BNS2023:85"
    assert ref.translated_from == "IPC 498A"
    assert keys("anticipatory bail 438 CrPC") == ["BNSS2023:482"]
    assert keys("section 65B evidence act electronic record") == ["BSA:63"]
    # An unmapped section falls back to the whole new code rather than a wrong section.
    assert keys("IPC 323 voluntarily causing hurt") == ["BNS2023"]


def test_base_section_strips_subsections():
    assert base_section("13(1)(ia)") == "13"
    assert base_section("498a") == "498A"


def test_valid_law_keys_rejects_garbage():
    assert valid_law_keys(["BNS2023:103", "bad key; drop table", "HMA1955", "BNS2023:103"]) == ["BNS2023:103", "HMA1955"]


# ------------------------------------------------------------------ verification

def test_only_https_government_hosts_are_official():
    assert is_official_url("https://api.sci.gov.in/supremecourt/2012/1/1.pdf")
    assert is_official_url("https://delhihighcourt.nic.in/x")
    assert not is_official_url("http://api.sci.gov.in/x.pdf")
    assert not is_official_url("https://indiankanoon.org/doc/1/")
    assert not is_official_url("https://gov.in.example.com/x")


def test_moved_hosts_and_path_variants():
    assert normalize_official_url("https://main.sci.gov.in/supremecourt/a.pdf#x") == "https://api.sci.gov.in/supremecourt/a.pdf"
    assert url_variants("https://api.sci.gov.in/jonew/judgments/40084.pdf") == [
        "https://api.sci.gov.in/jonew/judgments/40084.pdf",
        "https://api.sci.gov.in/jonew/judis/40084.pdf",
    ]


def test_parties_match_requires_each_distinctive_side():
    text = "IN THE SUPREME COURT OF INDIA ... SAMAR GHOSH ... APPELLANT VERSUS JAYA GHOSH ... RESPONDENT"
    assert parties_match(text, "Samar Ghosh v. Jaya Ghosh")
    assert not parties_match(text, "Shobha Rani v. Madhukar Reddi")
    # "State of Rajasthan" is all generic words, so only the petitioner side is checked.
    assert parties_match("VISHAKA AND OTHERS ... VERSUS STATE OF RAJASTHAN", "Vishaka v. State of Rajasthan")
    assert not parties_match("STATE OF KERALA v. UNION OF INDIA", "State of Kerala v. Union of India")


def test_verification_ignores_cases_cited_in_the_body(monkeypatch):
    body = "A" * verification.CAUSE_TITLE_CHARS + " as held in Samar Ghosh v. Jaya Ghosh "
    monkeypatch.setattr(verification, "fetch_document_text", lambda url, max_pages=4: ("application/pdf", body))
    result = verify_judgment_link("https://api.sci.gov.in/x.pdf", title="Samar Ghosh v. Jaya Ghosh")
    assert not result.verified


def test_verification_tries_known_path_variant(monkeypatch):
    def fake_fetch(url, max_pages=4):
        if "/judis/" in url:
            return "application/pdf", "K. SRINIVAS RAO ... APPELLANT VERSUS D.A. DEEPA ... RESPONDENT"
        raise ValueError("empty document")
    monkeypatch.setattr(verification, "fetch_document_text", fake_fetch)
    result = verify_judgment_link("https://main.sci.gov.in/jonew/judgments/40084.pdf", title="K. Srinivas Rao v. D.A. Deepa")
    assert result.verified
    assert result.url == "https://api.sci.gov.in/jonew/judis/40084.pdf"


# --------------------------------------------------------------------- discovery

def test_parse_json_payload_tolerates_fences_and_prose():
    assert parse_json_payload('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert parse_json_payload('Here you go: [{"a": 2}] thanks') == [{"a": 2}]


def test_candidates_require_title_court_and_holding():
    cases = candidates_from_payload([
        {"title": "A v. B", "court": "High Court of Delhi", "holding": "Held X", "judgment_date": "2020",
         "official_url": "null"},
        {"title": "No holding", "court": "Supreme Court of India"},
    ])
    assert len(cases) == 1
    assert cases[0].court_level == "HIGH_COURT"
    assert cases[0].judgment_date == "2020-01-01"
    assert cases[0].official_url is None


class _FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate_content(self, *, model, contents, config):
        self.prompts.append(contents)
        return SimpleNamespace(text=self.responses.pop(0), candidates=[])


def _discovery(responses, verified_urls):
    def fake_verify(url, *, title, petitioner=None, respondent=None):
        ok = url in verified_urls
        return LinkVerification(url, ok, "ok" if ok else "document does not name the parties")
    client = SimpleNamespace(models=_FakeModels(responses))
    return CaseDiscovery(client, model="test-model", verify=fake_verify, resolve_redirect=lambda uri: None), client


def test_discovery_returns_only_verified_cases_and_searches_missing_links():
    payload = """[
      {"title": "Good v. Case", "court": "Supreme Court of India", "court_level": "SUPREME_COURT",
       "holding": "h", "official_url": "https://api.sci.gov.in/good.pdf"},
      {"title": "Found v. Later", "court": "Supreme Court of India", "court_level": "SUPREME_COURT",
       "holding": "h", "official_url": null},
      {"title": "Fake v. Case", "court": "Supreme Court of India", "court_level": "SUPREME_COURT",
       "holding": "h", "official_url": "https://api.sci.gov.in/made-up.pdf"}
    ]"""
    discovery, client = _discovery(
        [payload, "https://api.sci.gov.in/later.pdf", "NONE"],
        {"https://api.sci.gov.in/good.pdf", "https://api.sci.gov.in/later.pdf"},
    )
    result = discovery.discover(topic="t", court_levels=["SUPREME_COURT"], link_budget_seconds=5)
    assert sorted(case.title for case in result.cases) == ["Found v. Later", "Good v. Case"]
    assert [case.title for case in result.rejected] == ["Fake v. Case"]
    assert len(client.models.prompts) == 3  # discovery + one link search per unverified case


def test_discovery_drops_courts_outside_the_filter():
    payload = '[{"title": "A v. B", "court": "High Court of Bombay", "court_level": "HIGH_COURT", "holding": "h", "official_url": "https://bombayhighcourt.nic.in/a.pdf"}]'
    discovery, _ = _discovery([payload], {"https://bombayhighcourt.nic.in/a.pdf"})
    assert discovery.discover(topic="t", court_levels=["SUPREME_COURT"]).cases == []


# ----------------------------------------------------------------------- caching

def _stored(case_id: str, law_keys: list[str], landmark: bool = False) -> StoredCase:
    return StoredCase(
        id=case_id, title=f"{case_id} v. X", court="Supreme Court of India", court_level="SUPREME_COURT",
        jurisdiction="NATIONAL", judgment_date="2020-01-01", case_number=None, citation=None,
        petitioner=None, respondent=None, source_url=f"https://api.sci.gov.in/{case_id}.pdf",
        source_authority="SC", summary="s", holding="h", primary_issue="p", metadata={"origin": "SEED"},
        law_keys=law_keys, is_landmark=landmark,
    )


class _FakeStore:
    def __init__(self, library, fresh=None):
        self.library = library
        self.fresh = fresh or {}
        self.queries = {}
        self.lookups = []

    def get_query(self, key):
        return self.queries.get(key)

    def cases_by_ids(self, ids):
        return [case for case in self.library if case.id in ids]

    def cases_for_law_keys(self, keys, *, court_levels, limit):
        return [case for case in self.library if set(case.law_keys) & set(keys)]

    def similar_cases(self, *args, **kwargs):
        return []

    def fresh_lookups(self, keys, max_age):
        return {k: v for k, v in self.fresh.items() if k in keys}

    def statute_section(self, act_id, section):
        return None

    def record_lookup(self, key, **kwargs):
        self.lookups.append((key, kwargs["status"]))

    def save_query(self, key, query, **kwargs):
        self.queries[key] = {"caseIds": list(kwargs.get("case_ids") or []), "discoveredAt": None}

    def count_hits(self, keys):
        pass

    def commit(self):
        pass


class _ExplodingDiscovery:
    def discover(self, **kwargs):
        raise AssertionError("discovery must not run when the library already covers this law")


def _service(store, discovery_factory):
    searcher = SimpleNamespace(_get_embedding=lambda text: [0.0] * 768,
                               search=lambda *a, **k: SimpleNamespace(results=()))
    service = ResearchService(SimpleNamespace(), SimpleNamespace(), discovery_factory=discovery_factory,
                              searcher=searcher)
    service.store = store
    return service


def test_repeat_research_on_a_law_is_served_from_the_library():
    store = _FakeStore([_stored("case_a", ["BNS2023:103"], landmark=True)], fresh={"BNS2023:103": "FOUND"})
    result = _service(store, _ExplodingDiscovery).cases("Section 103 BNS murder", law_keys=["BNS2023:103"])
    assert result.source == "library"
    assert not result.discovery_ran
    assert [case["id"] for case in result.cases] == ["case_a"]
    assert result.cases[0]["is_landmark"] is True


def test_unsearched_law_with_few_cases_triggers_official_search(monkeypatch):
    store = _FakeStore([])
    found = CandidateCase(title="New v. Case", court="Supreme Court of India", court_level="SUPREME_COURT",
                          judgment_date="2021-01-01", citation=None, case_number=None, petitioner=None,
                          respondent=None, official_url="https://api.sci.gov.in/new.pdf", summary="s",
                          holding="h", relevance="r", provisions=("Section 85, BNS",),
                          verification=LinkVerification("https://api.sci.gov.in/new.pdf", True, "ok"))
    discovery = SimpleNamespace(discover=lambda **kwargs: SimpleNamespace(cases=[found], rejected=[], model="m"))
    service = _service(store, lambda: discovery)

    def fake_save(case, **kwargs):
        store.library.append(_stored("case_new", ["BNS2023:85"]))
        return "case_new", {"BNS2023:85"}
    monkeypatch.setattr(service, "save_discovered", fake_save)

    result = service.cases("IPC 498A cruelty", law_keys=["BNS2023:85"])
    assert result.discovery_ran
    assert result.source == "official_search"
    assert result.cases[0]["is_new"] is True
    assert ("BNS2023:85", "FOUND") in store.lookups


def test_unsearched_semantic_neighbours_do_not_trigger_search_for_a_named_section():
    store = _FakeStore([_stored("case_a", ["BNS2023:103"])], fresh={"BNS2023:103": "FOUND"})
    result = _service(store, _ExplodingDiscovery).cases(
        "Section 103 BNS murder", law_keys=["BNS2023:103", "BNS2023:101"])
    assert not result.discovery_ran
    assert result.source == "library"


def test_law_already_searched_with_no_results_is_not_searched_again():
    store = _FakeStore([], fresh={"HMA1955:13": "NONE_FOUND"})
    result = _service(store, _ExplodingDiscovery).cases("section 13 HMA", law_keys=["HMA1955:13"])
    assert result.source == "none"
    assert not result.discovery_ran


def test_gazette_furniture_is_removed_from_statute_text():
    from research.store import clean_statute_text
    raw = "(c) dealing with matters.\nSec. 1]\nTHE GAZETTE OF INDIA EXTRAORDINARY\n23\n__________\n\n(5) For the purposes"
    assert clean_statute_text(raw) == "(c) dealing with matters.\n\n(5) For the purposes"


def test_query_key_ignores_case_and_punctuation():
    assert query_key("Section 103, BNS!") == query_key("section 103 bns")
    assert query_key("a", "x") != query_key("a", "y")
