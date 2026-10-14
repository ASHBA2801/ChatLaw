"""Filing agent orchestration: analyse → find recipients → draft."""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

from . import geo
from .analysis import analyze_facts, find_provisions
from .contacts import (
    ContactFinder,
    ContactResult,
    ContactStore,
    OfficeContact,
    curated_contacts,
    lookup_key,
    office_description,
)
from .drafting import draft_filing
from .taxonomy import KINDS, high_court_for
from .templates import TemplateLibrary

logger = logging.getLogger(__name__)

TextGenerator = Callable[[str], str]
_COURT_HINTS = {
    "magistrate": ("magistrate", "district court", "sessions court"),
    "civil_court": ("civil court", "district court"),
    "family_court": ("family court", "district court"),
    "consumer_commission": ("consumer commission",),
}


def _location_value(location: dict[str, Any] | None, key: str) -> str | None:
    value = (location or {}).get(key)
    return str(value).strip() if value not in (None, "") else None


class FilingService:
    def __init__(self, *, connection: Any = None, embedding_provider: Any = None,
                 generator: TextGenerator | None = None, research: Any = None,
                 finder_factory: Callable[[], ContactFinder] | None = None,
                 library: TemplateLibrary | None = None):
        self.connection = connection
        self.generator = generator
        self.research = research
        self.finder_factory = finder_factory
        self.library = library or TemplateLibrary(connection, embedding_provider)
        self.contacts = ContactStore(connection) if connection is not None else None

    # ---------------------------------------------------------------- analysis

    def analyze(self, facts: str, *, location: dict[str, Any] | None = None,
                case_title: str | None = None) -> dict[str, Any]:
        return analyze_facts(facts, location=location, case_title=case_title, generate=self.generator,
                             research=self.research)

    # -------------------------------------------------------------- recipients

    def resolve_location(self, location: dict[str, Any] | None) -> dict[str, Any]:
        """Fill in coordinates or district/state so both nearby search and contact lookup can run."""
        loc = dict(location or {})
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            if not loc.get("state") or not loc.get("district"):
                place = geo.reverse_geocode(float(lat), float(lon))
                if place:
                    for key in ("locality", "city", "district", "state", "pincode"):
                        if not loc.get(key):
                            loc[key] = getattr(place, key)
            return loc
        text = ", ".join(str(loc[k]) for k in ("locality", "city", "district", "state", "pincode") if loc.get(k))
        if text:
            place = geo.geocode(text)
            if place:
                loc["latitude"], loc["longitude"] = place.latitude, place.longitude
                for key in ("city", "district", "state", "pincode"):
                    if not loc.get(key) and getattr(place, key):
                        loc[key] = getattr(place, key)
        return loc

    def _discover(self, kind: str, loc: dict[str, Any], *, office_name: str | None = None,
                  refresh: bool = False) -> ContactResult:
        state, district = _location_value(loc, "state"), _location_value(loc, "district") or _location_value(loc, "city")
        locality = _location_value(loc, "locality")
        key = lookup_key(kind, state, district, locality, office_name)
        if self.contacts is not None and not refresh:
            cached = self.contacts.get(key)
            if cached is not None:
                return ContactResult(cached[0], cached[1], cached=True)
        if self.finder_factory is None or not (state or district):
            return ContactResult([], "NONE_FOUND")
        description = office_description(kind, locality=locality, city=_location_value(loc, "city"),
                                         district=district, state=state, office_name=office_name)
        try:
            offices = self.finder_factory().find(kind, description)
        except Exception:
            logger.exception("[FILINGS] contact discovery failed for %s", kind)
            return ContactResult([], "FAILED")
        status = "FOUND" if offices else "NONE_FOUND"
        if self.contacts is not None:
            self.contacts.put(key, kind=kind, state=state, district=district, locality=locality,
                              offices=offices, status=status)
        return ContactResult(offices, status)

    def authorities(self, kind: str, location: dict[str, Any] | None, *, office_name: str | None = None,
                    radius_km: float = 10.0, refresh: bool = False) -> dict[str, Any]:
        if kind not in KINDS:
            raise KeyError(kind)
        spec = KINDS[kind]
        loc = self.resolve_location(location)
        offices: list[OfficeContact] = curated_contacts(kind, _location_value(loc, "state"))
        nearby: list[dict[str, Any]] = []
        notes: list[str] = []
        lat, lon = loc.get("latitude"), loc.get("longitude")
        has_point = isinstance(lat, (int, float)) and isinstance(lon, (int, float))

        if spec.lookup in {"nearby_police", "nearby_court"} and has_point:
            amenity = "police" if spec.lookup == "nearby_police" else "courthouse"
            found = geo.nearby(amenity, float(lat), float(lon), radius_km=radius_km)
            if spec.lookup == "nearby_court":
                hints = _COURT_HINTS.get(kind, ())
                found = sorted(found, key=lambda o: (not (o.kind_hint in hints), o.distance_km))
            nearby = [o.as_dict() for o in found]
            if not found:
                notes.append(f"No {'police stations' if amenity == 'police' else 'courts'} were found on "
                             f"OpenStreetMap within {radius_km:g} km.")
        elif spec.lookup in {"nearby_police", "nearby_court"}:
            notes.append("Add your location to list the nearest offices.")

        if kind == "high_court" and not offices:
            hc = high_court_for(_location_value(loc, "state"))
            if hc:
                offices.append(OfficeContact(kind=kind, name=hc[0], address=hc[1], source="curated",
                                             portal_url=spec.portal_url))
        if kind == "police_station" and not office_name and nearby:
            # The nearest law-and-order station is the most useful default to look up.
            office_name = next((n["name"] for n in nearby if n.get("kind_hint") != "traffic police"), None)

        status = "CURATED" if offices else "NONE_FOUND"
        cached = False
        needs_search = spec.lookup != "curated" or not offices
        if kind in {"cbi", "pmo", "supreme_court"}:
            needs_search = False
        if needs_search:
            result = self._discover(kind, loc, office_name=office_name, refresh=refresh)
            cached = result.cached
            names = {o.name.lower() for o in offices}
            known_emails = {e.address for o in offices for e in o.emails}
            for office in result.offices:
                emails = {e.address for e in office.emails}
                # Skip a discovered duplicate of a curated office (same name, or nothing new to add).
                if office.name.lower() in names or (emails and emails <= known_emails):
                    continue
                offices.append(office)
                names.add(office.name.lower())
                known_emails |= emails
            status = "CURATED" if status == "CURATED" else result.status
            if result.status == "FAILED":
                notes.append("The official-site search could not be completed. Try again shortly.")

        if not any(o.emails for o in offices) and spec.channel == "email":
            notes.append("No email address could be verified on an official website for this office. You can "
                         "type one you know, print the document and hand it in, or send it by registered post.")
        return {
            "kind": kind,
            "spec": spec.as_dict(),
            "location": {k: loc.get(k) for k in ("locality", "city", "district", "state", "pincode",
                                                  "latitude", "longitude")},
            "offices": [o.as_dict() for o in offices],
            "nearby": nearby,
            "status": status,
            "cached": cached,
            "notes": notes,
        }

    # ------------------------------------------------------------------ draft

    def draft(self, kind: str, *, facts: str, analysis: dict[str, Any] | None = None,
              complainant: dict[str, Any] | None = None, recipient: dict[str, Any] | None = None,
              location: dict[str, Any] | None = None, language: str = "en",
              instructions: str | None = None) -> dict[str, Any]:
        if kind not in KINDS:
            raise KeyError(kind)
        if not facts or len(facts.strip()) < 20:
            raise ValueError("Describe what happened before drafting.")
        analysis = dict(analysis or {})
        if not analysis.get("summary"):
            analysis = self.analyze(facts, location=location)
        elif not analysis.get("provisions") and analysis.get("law_search_queries"):
            analysis["provisions"], _ = find_provisions(self.research, analysis["law_search_queries"])
        template = self.library.match(kind, facts)
        if template is None:
            raise KeyError(kind)
        return draft_filing(kind=kind, template=template, facts=facts, analysis=analysis,
                            complainant=complainant, recipient=recipient, location=location,
                            language=language, instructions=instructions, generate=self.generator)

    def close(self) -> None:
        if self.connection is None:
            return
        try:
            self.connection.rollback()
        except Exception:
            pass
        finally:
            self.connection.close()


def create_filing_service() -> FilingService:
    from embeddings.provider import create_embedding_provider
    from research.service import ResearchService
    from retrieval.vector_search import connect_from_environment

    connection = connect_from_environment()
    try:
        provider = create_embedding_provider()
    except Exception:
        connection.close()
        raise
    has_model = bool(os.getenv("GEMINI_API_KEY", "").strip() and os.getenv("GEMINI_GENERATION_MODEL", "").strip())

    def generate(prompt: str) -> str:
        from generation.gemini import GeminiGenerator
        return GeminiGenerator().generate_text(prompt, thinking_level="low").answer

    research = ResearchService(connection, provider, generator=None)
    return FilingService(connection=connection, embedding_provider=provider,
                         generator=generate if has_model else None, research=research,
                         finder_factory=ContactFinder if has_model else None)

