"""Cases tab: complaints to authorities and petitions to courts."""

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from complaints.service import FilingService, create_filing_service
from complaints.taxonomy import KINDS, kinds_payload
from complaints.templates import load_templates, template_summaries

router = APIRouter(prefix="/api/complaints", tags=["complaints"])
logger = logging.getLogger(__name__)


class Location(BaseModel):
    locality: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=160)
    district: str | None = Field(default=None, max_length=160)
    state: str | None = Field(default=None, max_length=120)
    pincode: str | None = Field(default=None, max_length=12)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class Complainant(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    relation: str | None = Field(default=None, max_length=20)
    relation_name: str | None = Field(default=None, max_length=200)
    age: str | None = Field(default=None, max_length=10)
    occupation: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=600)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200)
    place: str | None = Field(default=None, max_length=120)


class AnalyzeRequest(BaseModel):
    facts: str = Field(..., min_length=20, max_length=30000)
    case_title: str | None = Field(default=None, max_length=300)
    location: Location | None = None


class AuthoritiesRequest(BaseModel):
    kind: str
    location: Location | None = None
    office_name: str | None = Field(default=None, max_length=200)
    radius_km: float = Field(default=10.0, ge=1, le=50)
    refresh: bool = False

    @field_validator("kind")
    @classmethod
    def known_kind(cls, value: str) -> str:
        if value not in KINDS:
            raise ValueError("unknown office or court")
        return value


class GeocodeRequest(BaseModel):
    query: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class DraftRequest(AuthoritiesRequest):
    facts: str = Field(..., min_length=20, max_length=30000)
    analysis: dict[str, Any] | None = None
    complainant: Complainant | None = None
    recipient: dict[str, Any] | None = None
    language: str = Field(default="en", max_length=8)
    instructions: str | None = Field(default=None, max_length=2000)


def _run(label: str, action):
    started = time.perf_counter()
    service: FilingService | None = None
    try:
        service = create_filing_service()
        return action(service)
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown office or court") from exc
    except ValueError as exc:
        if "required" in str(exc):
            logger.exception("[FILINGS] %s misconfigured", label)
            raise HTTPException(status_code=503, detail="The filing service is unavailable") from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("[FILINGS] %s unavailable", label)
        raise HTTPException(status_code=503, detail="The filing service is unavailable") from exc
    except Exception as exc:
        logger.exception("[FILINGS] %s failed", label)
        raise HTTPException(status_code=500, detail="Filing request failed") from exc
    finally:
        if service is not None:
            service.close()
        logger.info("[FILINGS] %s complete (%.2fs)", label, time.perf_counter() - started)


def _dump(model: BaseModel | None) -> dict[str, Any] | None:
    return model.model_dump(exclude_none=True) if model is not None else None


@router.get("/kinds")
def filing_kinds() -> dict[str, Any]:
    return {"kinds": kinds_payload(), "templates": template_summaries(list(load_templates().values()))}


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    return _run("analyze", lambda service: service.analyze(
        request.facts, location=_dump(request.location), case_title=request.case_title))


@router.post("/authorities")
def authorities(request: AuthoritiesRequest) -> dict[str, Any]:
    return _run("authorities", lambda service: service.authorities(
        request.kind, _dump(request.location), office_name=request.office_name, radius_km=request.radius_km,
        refresh=request.refresh))


@router.post("/geocode")
def geocode(request: GeocodeRequest) -> dict[str, Any]:
    from complaints import geo

    if request.latitude is not None and request.longitude is not None:
        place = geo.reverse_geocode(request.latitude, request.longitude)
    elif request.query:
        place = geo.geocode(request.query)
    else:
        raise HTTPException(status_code=422, detail="Give a place name or coordinates")
    if place is None:
        raise HTTPException(status_code=404, detail="That location could not be found")
    return {"place": place.as_dict()}


@router.post("/draft")
def draft(request: DraftRequest) -> dict[str, Any]:
    return _run("draft", lambda service: service.draft(
        request.kind, facts=request.facts, analysis=request.analysis, complainant=_dump(request.complainant),
        recipient=request.recipient, location=_dump(request.location), language=request.language,
        instructions=request.instructions))
