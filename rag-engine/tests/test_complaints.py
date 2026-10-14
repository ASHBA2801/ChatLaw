"""Tests for the Cases tab filing agent: taxonomy, templates, contacts, geo, analysis, drafting, API."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from complaints import geo  # noqa: E402
from complaints.analysis import analyze_facts  # noqa: E402
from complaints.contacts import (  # noqa: E402
    ContactFinder,
    candidate_pages,
    curated_contacts,
    deobfuscate,
    emails_in,
    is_official_host,
    lookup_key,
    verify_email,
)
from complaints.drafting import check_citations, draft_filing, placeholders_in  # noqa: E402
from complaints.service import FilingService  # noqa: E402
from complaints.taxonomy import (  # noqa: E402
    AUTHORITY_KINDS,
    COURT_KINDS,
    KINDS,
    high_court_for,
    read_facts,
    recommend,
)
from complaints.templates import TemplateLibrary, load_templates, parse_template  # noqa: E402

AUTH = {"Authorization": "Bearer test-secret"}


def kinds_of(recs):
    return [r.kind for r in recs]


# ------------------------------------------------------------------ taxonomy

def test_every_office_and_court_has_a_template():
    templates = load_templates()
    assert set(templates) == set(KINDS)
    for kind, template in templates.items():
        assert template.forum == KINDS[kind].forum
        assert template.sources, kind
        assert any(s.heading.lower() == "filing notes" for s in template.sections), kind


def test_offices_and_courts_requested_by_the_product_exist():
    for kind in ("police_station", "police_superior", "collector", "vigilance", "cm_cell", "cbi", "pmo"):
        assert kind in AUTHORITY_KINDS
    for kind in ("magistrate", "civil_court", "family_court", "consumer_commission", "high_court", "supreme_court"):
        assert kind in COURT_KINDS


def test_bribe_by_state_official_goes_to_vigilance_not_cbi():
    reading = read_facts("The village administrative officer demanded a bribe of Rs 5000 to issue my patta.")
    assert reading.flags["corruption"] and reading.flags["public_servant"]
    assert reading.severity == "serious"
    recs = recommend(reading.flags, reading.severity, reading.court_subjects)
    assert recs[0].kind in {"vigilance", "collector"}
    assert "vigilance" in kinds_of(recs) and "cbi" not in kinds_of(recs)


def test_central_government_corruption_recommends_cbi():
    flags = dict(read_facts("The bank manager demanded a bribe to sanction my loan").flags)
    flags["central_government"] = True
    recs = recommend(flags, "grave")
    assert recs[0].kind == "cbi"
    assert next(r for r in recs if r.kind == "cbi").priority == "primary"


def test_police_refusal_escalates_to_sp_and_magistrate():
    reading = read_facts("My phone was stolen and the police refused to register my FIR.")
    recs = recommend(reading.flags, reading.severity, reading.court_subjects)
    primary = [r.kind for r in recs if r.priority == "primary"]
    assert "police_superior" in primary
    assert "magistrate" in kinds_of(recs)
    assert "police_station" not in primary


def test_cyber_fraud_and_consumer_and_family():
    cyber = read_facts("Someone called pretending to be from my bank and took Rs 40,000 through UPI after I shared the OTP.")
    assert cyber.flags["cyber"] and "cyber_crime" in kinds_of(recommend(cyber.flags, cyber.severity))
    consumer = read_facts("The online store sold me a defective washing machine and refuses a refund.")
    assert consumer.severity == "low"
    assert kinds_of(recommend(consumer.flags, consumer.severity, consumer.court_subjects))[0] == "consumer_commission"
    family = read_facts("My husband left and is not paying maintenance for our two children.")
    assert "family_court" in kinds_of(recommend(family.flags, family.severity, family.court_subjects))


def test_custodial_violence_is_grave():
    reading = read_facts("My brother was picked up by the police and beaten in the lock-up overnight.")
    assert reading.severity == "grave"
    recs = recommend(reading.flags, reading.severity, reading.court_subjects)
    assert recs[0].kind == "human_rights"
    assert "high_court" in kinds_of(recs)


def test_high_court_mapping():
    assert high_court_for("Tamil Nadu")[0] == "Madras High Court"
    assert high_court_for("Puducherry")[0] == "Madras High Court"
    assert high_court_for("Orissa")[0] == "Orissa High Court"
    assert high_court_for("Haryana")[0].startswith("High Court of Punjab and Haryana")
    assert high_court_for("Atlantis") is None


# ----------------------------------------------------------------- templates

def test_parse_template_requires_front_matter():
    with pytest.raises(ValueError):
        parse_template("bad", "## Heading\ntext")
    tpl = parse_template("x", "---\nkind: x\nforum: authority\ntitle: X\nsources:\n- A\n- B\n---\n## One\nbody\n## Two\nmore")
    assert tpl.sources == ("A", "B")
    assert [c["heading"] for c in tpl.chunks()] == ["One", "Two"]


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, rows=()):
        self.cursor_obj = FakeCursor(list(rows))

    def cursor(self):
        return self.cursor_obj

    def rollback(self):
        pass

    def commit(self):
        pass


def test_template_library_adds_related_sections_from_vectors():
    rows = [("cyber_crime", "Cyber crime complaint", "Transaction details", "UTR, amount...", 0.81),
            ("cyber_crime", "Cyber crime complaint", "Incident details", "low", 0.4)]
    provider = SimpleNamespace(embed=lambda text: [0.1] * 768)
    library = TemplateLibrary(FakeConnection(rows), provider)
    match = library.match("police_station", "UPI fraud of Rs 40,000")
    assert match.source == "vector"
    assert [r.heading for r in match.related] == ["Transaction details"]
    assert "Related format guidance" in match.exemplar()


def test_template_library_falls_back_to_file_without_db():
    match = TemplateLibrary().match("high_court", "anything")
    assert match.source == "file" and match.template.kind == "high_court"


# ------------------------------------------------------------------ contacts

def test_deobfuscates_government_style_emails():
    text = "Email : sp-cbe[at]tnpolice[dot]gov[dot]in, Collector: collrcbe (at) nic (dot) in, plain dvac@nic.in"
    found = emails_in(text)
    assert {"sp-cbe@tnpolice.gov.in", "collrcbe@nic.in", "dvac@nic.in"} <= found
    assert "@" in deobfuscate("abc [ at ] xyz [ dot ] in")


def test_official_hosts_only():
    assert is_official_host("http://cbe.tnpolice.gov.in/contact")
    assert is_official_host("https://coimbatore.nic.in/")
    assert not is_official_host("https://justdial.com/x")
    assert not is_official_host("ftp://x.gov.in")


def test_verify_email_requires_presence_on_official_page():
    pages = {"https://coimbatore.nic.in/contact": "Collector email: collrcbe[at]nic[dot]in"}
    fetch = lambda url: pages[url]  # noqa: E731
    assert verify_email("collrcbe@nic.in", ["https://coimbatore.nic.in/contact"], fetch) == \
        "https://coimbatore.nic.in/contact"
    assert verify_email("invented@nic.in", ["https://coimbatore.nic.in/contact"], fetch) is None
    assert verify_email("collrcbe@nic.in", ["https://example.com/contact"], fetch) is None


def test_candidate_pages_add_contact_pages_on_official_hosts():
    pages = candidate_pages("https://coimbatore.nic.in/directory/district-collector/", None, "https://blog.example.com/x",
                            "https://coimbatore.nic.in")
    assert pages[0] == "https://coimbatore.nic.in/directory/district-collector/"
    assert "https://coimbatore.nic.in/whos-who/" in pages
    assert not any("example.com" in p for p in pages)


def test_curated_directory_has_no_unsourced_emails():
    for kind in KINDS:
        for state in (None, "Tamil Nadu"):
            for office in curated_contacts(kind, state):
                for email in office.emails:
                    assert email.source_url and is_official_host(email.source_url), (kind, email)
    dvac = curated_contacts("vigilance", "Tamil Nadu")
    assert dvac and dvac[0].emails[0].address == "dvac@nic.in"
    assert curated_contacts("vigilance", "Kerala") == []
    assert curated_contacts("pmo")[0].emails == ()


class FakeGenAI:
    def __init__(self, text, urls=()):
        chunks = [SimpleNamespace(web=SimpleNamespace(title="coimbatore.nic.in", uri=u)) for u in urls]
        self.response = SimpleNamespace(text=text, candidates=[SimpleNamespace(
            grounding_metadata=SimpleNamespace(grounding_chunks=chunks))])
        self.models = self

    def generate_content(self, **_):
        return self.response


def test_contact_finder_keeps_only_verified_emails(monkeypatch):
    pytest.importorskip("google.genai")
    payload = {"offices": [
        {"name": "District Collectorate, Coimbatore", "designation": "District Collector",
         "email": "collrcbe@nic.in", "source_url": "https://coimbatore.nic.in/contact"},
        {"name": "Made-up office", "email": "guess@gmail.com", "source_url": "https://blog.example.com/"},
    ]}
    pages = {"https://coimbatore.nic.in/contact": "mail collrcbe[at]nic[dot]in"}
    finder = ContactFinder(FakeGenAI(json.dumps(payload)), model="test", fetch=lambda u: pages.get(u, ""),
                           resolve_redirect=lambda u: None)
    offices = finder.find("collector", "the District Collector of Coimbatore")
    assert len(offices) == 1
    assert offices[0].emails[0].address == "collrcbe@nic.in"
    assert offices[0].emails[0].verified


def test_lookup_key_is_stable_and_scoped():
    assert lookup_key("collector", "Tamil Nadu", "Coimbatore", "Gandhipuram") == \
        lookup_key("collector", "tamil nadu", "coimbatore", "R.S. Puram")  # locality ignored for district offices
    assert lookup_key("police_station", "TN", "Coimbatore", "Gandhipuram") != \
        lookup_key("police_station", "TN", "Coimbatore", "Peelamedu")


# ----------------------------------------------------------------------- geo

def test_nearby_parses_overpass_and_sorts(monkeypatch):
    geo._cache.clear()
    data = {"elements": [
        {"type": "node", "id": 1, "lat": 11.02, "lon": 76.96, "tags": {"name": "Traffic Police Booth"}},
        {"type": "node", "id": 2, "lat": 11.05, "lon": 76.99, "tags": {"name": "Race Course Police Station",
                                                                         "phone": "0422-000"}},
        {"type": "way", "id": 3, "center": {"lat": 11.01, "lon": 76.95}, "tags": {"name": "All Women Police Station"}},
        {"type": "node", "id": 4, "lat": 11.0, "lon": 76.9, "tags": {}},
    ]}
    offices = geo.nearby("police", 11.0168, 76.9558, http_get=lambda url, params: data)
    names = [o.name for o in offices]
    assert names[-1] == "Traffic Police Booth"
    assert "All Women Police Station" in names and len(names) == 3
    assert offices[0].distance_km <= offices[1].distance_km
    assert next(o for o in offices if o.name.startswith("All Women")).kind_hint == "women police station"


def test_nearby_falls_back_to_nominatim_when_overpass_fails(monkeypatch):
    geo._cache.clear()
    monkeypatch.setattr(geo, "_nominatim_throttle", lambda: None)

    def get(url, params):
        if "interpreter" in url:
            raise RuntimeError("504")
        return [{"category": "amenity", "type": "police", "name": "C-3 Saibaba Colony Police Station",
                 "lat": "11.03", "lon": "76.95", "osm_type": "node", "osm_id": 9, "extratags": {"phone": "100"},
                 "address": {"road": "Mettupalayam Road"}},
                {"category": "amenity", "type": "bank", "name": "SBI", "lat": "11.0", "lon": "76.9"}]

    offices = geo.nearby("police", 11.0168, 76.9558, http_get=get)
    assert [o.name for o in offices] == ["C-3 Saibaba Colony Police Station"]
    assert offices[0].phone == "100" and "Mettupalayam Road" in offices[0].address


def test_geo_failures_return_nothing(monkeypatch):
    monkeypatch.setattr(geo, "_nominatim_throttle", lambda: None)
    geo._cache.clear()
    def boom(url, params):
        raise RuntimeError("down")
    assert geo.nearby("courthouse", 10.0, 77.0, http_get=boom) == []


# ------------------------------------------------------------------ analysis

class FakeResearch:
    def __init__(self):
        self.queries = []

    def law(self, query, articulate=False):
        self.queries.append(query)
        provision = SimpleNamespace(
            law_key="BNS2023:318", act_id="BNS2023", act_title="The Bharatiya Nyaya Sanhita, 2023",
            short_title="BNS, 2023", section="318", label="Section 318, BNS, 2023",
            text="Whoever cheats ... shall be punished", source_url=None, translated_from=None)
        return SimpleNamespace(provisions=[provision], notes=[])


FACTS = ("On 3 October 2026 a caller claiming to be from SBI asked for my OTP and Rs 45,000 was taken from my "
         "account through UPI. I went to Peelamedu police station but they refused to register an FIR.")


def test_analysis_merges_model_and_rules():
    model = {"summary": "UPI fraud", "category": "Online financial fraud", "severity": "moderate",
             "flags": {"cyber": True, "central_government": False}, "law_search_queries": ["cheating online"],
             "missing_information": ["Transaction ID"], "accused": [{"name": None, "description": "caller"}]}
    research = FakeResearch()
    result = analyze_facts(FACTS, location={"city": "Coimbatore", "state": "Tamil Nadu"},
                           generate=lambda prompt: json.dumps(model), research=research)
    assert result["model_used"]
    assert result["severity"] == "serious"  # rules see police refusal + cyber, model said moderate
    assert result["flags"]["police_inaction"] and result["flags"]["cyber"]
    assert result["provisions"][0]["law_key"] == "BNS2023:318"
    kinds = [r["kind"] for r in result["recommendations"]]
    assert "cyber_crime" in kinds and "police_superior" in kinds
    assert any("1930" in step for step in result["urgent_steps"])
    assert research.queries == ["cheating online"]


def test_analysis_without_model_uses_rules():
    result = analyze_facts(FACTS, generate=None, research=None)
    assert not result["model_used"] and result["provisions"] == []
    with pytest.raises(ValueError):
        analyze_facts("too short")


# ------------------------------------------------------------------ drafting

PROVISIONS = [{"id": 1, "law_key": "BNS2023:318", "label": "Section 318, BNS, 2023", "section": "318",
               "act_title": "The Bharatiya Nyaya Sanhita, 2023", "text": "cheating", "source_url": None}]


def test_check_citations_strips_markers_and_flags_unsupported_sections():
    sections, used, warnings = check_citations(
        [{"heading": "Offences", "text": "Section 318(4) of the BNS [1] and Section 420 IPC [7] apply."}],
        PROVISIONS, procedural_text="Section 173 BNSS")
    assert used == [1]
    assert "[1]" not in sections[0]["text"] and "[7]" not in sections[0]["text"]
    assert any("420" in w for w in warnings)
    assert any("did not match" in w for w in warnings)
    _, _, ok = check_citations([{"heading": "", "text": "register an FIR under Section 173 BNSS"}],
                               PROVISIONS, procedural_text="Section 173 BNSS")
    assert ok == []


def test_placeholders_detected():
    assert placeholders_in("On [DATE OF INCIDENT] at [PLACE]; see [1]") == ["[DATE OF INCIDENT]", "[PLACE]"]


def test_draft_with_model_output():
    analysis = {"summary": "UPI fraud", "provisions": PROVISIONS}
    output = {"title": "Complaint", "subject": "Online fraud of Rs 45,000", "addressee": "To\nThe SHO",
              "sections": [{"heading": "Facts", "text": "1. On 3 October 2026 ... [ACCUSED PHONE NUMBER]"},
                           {"heading": "Offences", "text": "Section 318 of the BNS, 2023 [1]."}],
              "enclosures": ["Bank statement"], "email_cover_note": "Sir, please find my complaint."}
    template = TemplateLibrary().match("police_station", FACTS)
    result = draft_filing(kind="police_station", template=template, facts=FACTS, analysis=analysis,
                          complainant={"name": "R. Kumar"}, generate=lambda p: json.dumps(output),
                          today=date(2026, 10, 14))
    assert result["model_used"]
    assert result["citations"][0]["law_key"] == "BNS2023:318"
    assert "[1]" not in result["text"] and "Enclosures" in result["text"]
    assert result["placeholders"] == ["[ACCUSED PHONE NUMBER]"]
    assert result["email"]["subject"] == "Online fraud of Rs 45,000"
    assert result["email"]["body"].startswith("Sir, please find")
    assert result["filing"]["notes"]


def test_draft_prompt_carries_rules_and_template():
    captured = {}

    def generate(prompt):
        captured["prompt"] = prompt
        return "not json"

    template = TemplateLibrary().match("cbi", FACTS)
    result = draft_filing(kind="cbi", template=template, facts=FACTS, analysis={"summary": "x", "provisions": []},
                          generate=generate, language="ta")
    prompt = captured["prompt"]
    assert "Write the whole document in Tamil" in prompt and "Never invent names" in prompt
    assert "translate everything else" in prompt
    assert "Central Bureau of Investigation" in prompt
    assert not result["model_used"]  # unusable output falls back to the template
    assert any("template" in w for w in result["warnings"])


def test_long_documents_switch_email_to_cover_note():
    analysis = {"summary": "x", "provisions": []}
    long_facts = ("The accused cheated me " + "again and again " * 30 + ". ") * 30
    template = TemplateLibrary().match("collector", long_facts)
    result = draft_filing(kind="collector", template=template, facts=long_facts, analysis=analysis)
    assert not result["email"]["full_text_fits"]
    assert "attached as a PDF" in result["email"]["body"]


# ------------------------------------------------------------------- service

def test_authorities_for_police_station_uses_nearby_and_verified_contacts(monkeypatch):
    monkeypatch.setattr(geo, "nearby", lambda *a, **k: [
        geo.NearbyOffice("osm-1", "Peelamedu Police Station", 11.03, 77.0, 1.2, phone="0422-1")])
    calls = []

    class Finder:
        def find(self, kind, description):
            calls.append(description)
            from complaints.contacts import ContactEmail, OfficeContact
            return [OfficeContact(kind=kind, name="Peelamedu PS", emails=(ContactEmail("ps@tnpolice.gov.in"),),
                                  source="official_search", source_url="https://tnpolice.gov.in/x")]

    service = FilingService(finder_factory=Finder)
    result = service.authorities("police_station", {"latitude": 11.02, "longitude": 76.96, "state": "Tamil Nadu",
                                                    "district": "Coimbatore"})
    assert result["nearby"][0]["name"] == "Peelamedu Police Station"
    assert "Peelamedu Police Station" in calls[0]
    assert result["offices"][0]["emails"][0]["address"] == "ps@tnpolice.gov.in"


def test_authorities_pmo_is_portal_only_and_never_searched():
    service = FilingService(finder_factory=lambda: (_ for _ in ()).throw(AssertionError("no search")))
    result = service.authorities("pmo", {"state": "Tamil Nadu", "latitude": 11.0, "longitude": 77.0,
                                         "district": "Coimbatore"})
    assert result["spec"]["channel"] == "portal"
    assert result["offices"][0]["portal_url"] == "https://pgportal.gov.in/"


def test_high_court_falls_back_to_state_mapping():
    service = FilingService()
    result = service.authorities("high_court", {"state": "Bihar", "latitude": 25.6, "longitude": 85.1,
                                                "district": "Patna"})
    assert result["offices"][0]["name"] == "Patna High Court"


# ----------------------------------------------------------------------- API

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    from api import main
    from api.routes import complaints as route

    main._rate_limit.clear()

    class Service(FilingService):
        def analyze(self, facts, **kwargs):
            return {"summary": facts[:20], "recommendations": []}

    monkeypatch.setattr(route, "create_filing_service", lambda: Service())
    with TestClient(main.app) as test_client:
        yield test_client


def test_api_kinds_and_validation(client):
    response = client.get("/api/complaints/kinds", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert {k["id"] for k in body["kinds"]} == set(KINDS)
    assert len(body["templates"]) == len(KINDS)
    assert client.post("/api/complaints/authorities", json={"kind": "nope"}, headers=AUTH).status_code == 422
    assert client.post("/api/complaints/analyze", json={"facts": "short"}, headers=AUTH).status_code == 422
    ok = client.post("/api/complaints/analyze", json={"facts": "x" * 30}, headers=AUTH)
    assert ok.status_code == 200 and ok.json()["summary"] == "x" * 20
    assert client.get("/api/complaints/kinds").status_code == 401
