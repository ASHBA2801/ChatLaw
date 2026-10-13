"""Research tab: statutes from the embeddings and verified case law."""

import logging
import re
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from research.discovery import COURT_LEVELS
from research.service import ResearchService, create_research_service, valid_law_keys
from research.store import Provision

router = APIRouter(prefix="/api/research", tags=["research"])
logger = logging.getLogger(__name__)
_ACT_ID_RE = re.compile(r"^[A-Za-z0-9_]{2,40}$")


class ResearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("query must not be empty")
        return value


class ResearchCasesRequest(ResearchQueryRequest):
    law_keys: list[str] | None = Field(default=None, max_length=12)
    court_levels: list[str] = Field(default_factory=lambda: list(COURT_LEVELS), max_length=4)
    refresh: bool = False
    limit: int = Field(default=8, ge=1, le=20)

    @field_validator("court_levels")
    @classmethod
    def known_levels(cls, value: list[str]) -> list[str]:
        levels = [level for level in value if level in COURT_LEVELS]
        return levels or list(COURT_LEVELS)


class JudgmentSummaryRequest(BaseModel):
    case_id: str = Field(..., pattern=r"^case_[0-9a-f]{24}$")


def _provision(provision: Provision) -> dict[str, Any]:
    return {
        "law_key": provision.law_key,
        "act_id": provision.act_id,
        "act_title": provision.act_title,
        "short_title": provision.short_title,
        "section": provision.section,
        "label": provision.label,
        "text": provision.text,
        "chapter": provision.chapter,
        "page_number": provision.page_number,
        "source_url": provision.source_url,
        "similarity": provision.similarity,
        "matched_by": provision.matched_by,
        "translated_from": provision.translated_from,
    }


def _run(label: str, action):
    started = time.perf_counter()
    service: ResearchService | None = None
    try:
        service = create_research_service()
        return action(service)
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        logger.exception("[RESEARCH] %s unavailable", label)
        raise HTTPException(status_code=503, detail="The research service is unavailable") from exc
    except Exception as exc:
        logger.exception("[RESEARCH] %s failed", label)
        raise HTTPException(status_code=500, detail="Research request failed") from exc
    finally:
        if service is not None:
            service.close()
        logger.info("[RESEARCH] %s complete (%.2fs)", label, time.perf_counter() - started)


@router.post("/law")
def research_law(request: ResearchQueryRequest) -> dict[str, Any]:
    """Relevant statutory provisions, fetched straight from the embedded corpus."""
    def action(service: ResearchService):
        result = service.law(request.query, articulate=False)
        return {
            "query": result.query,
            "law_keys": result.law_keys,
            "provisions": [_provision(p) for p in result.provisions],
            "notes": result.notes,
        }
    return _run("law", action)


@router.post("/articulate")
def research_articulate(request: ResearchQueryRequest) -> dict[str, Any]:
    """Plain-language explanation of the retrieved law (cached per query)."""
    def action(service: ResearchService):
        result = service.law(request.query, articulate=True)
        return {"query": result.query, "articulation": result.articulation, "error": result.articulation_error}
    return _run("articulate", action)


@router.post("/cases")
def research_cases(request: ResearchCasesRequest) -> dict[str, Any]:
    """Verified judgments: from the case library first, official sources when needed."""
    def action(service: ResearchService):
        result = service.cases(request.query, law_keys=request.law_keys, court_levels=request.court_levels,
                               refresh=request.refresh, limit=request.limit)
        return {
            "query": result.query,
            "law_keys": result.law_keys,
            "cases": result.cases,
            "source": result.source,
            "discovery_ran": result.discovery_ran,
            "proposed": result.proposed,
            "verified": result.verified,
            "message": result.message,
        }
    return _run("cases", action)


@router.post("/judgment-summary")
def research_judgment_summary(request: JudgmentSummaryRequest) -> dict[str, Any]:
    """Detailed summary written from the official judgment text (cached on the case)."""
    def action(service: ResearchService):
        summary = service.case_summary(request.case_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="Judgment summary is not available for this case")
        return {"case_id": request.case_id, "summary": summary}
    return _run("judgment summary", action)


@router.get("/acts")
def research_acts() -> dict[str, Any]:
    return _run("acts", lambda service: {"acts": service.store.list_acts()})


@router.get("/acts/{act_id}/sections")
def research_sections(act_id: str) -> dict[str, Any]:
    if not _ACT_ID_RE.match(act_id):
        raise HTTPException(status_code=404, detail="Unknown Act")
    return _run("sections", lambda service: {"act_id": act_id, "sections": service.store.list_sections(act_id)})


@router.get("/law-cases")
def research_law_cases(law_key: str = Query(..., max_length=60),
                       court_levels: list[str] = Query(default=list(COURT_LEVELS))) -> dict[str, Any]:
    """Cases already stored for one Act or section; never triggers a web search."""
    if not valid_law_keys([law_key]):
        raise HTTPException(status_code=422, detail="Invalid law key")
    levels = [level for level in court_levels if level in COURT_LEVELS] or list(COURT_LEVELS)
    return _run("law cases", lambda service: {"law_key": law_key,
                                               "cases": service.law_cases(law_key, levels)})
