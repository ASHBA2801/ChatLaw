"""Structured document generation endpoints. Additive; chat and search are unchanged."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.models import (
    DocumentGenerateRequest,
    DocumentReviseRequest,
    DocumentSectionRegenerateRequest,
    DocumentSelectionEditRequest,
)
from api.service import RagService
from api.routes.search import get_service
from documents.templates import TEMPLATES, list_templates

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.get("/templates")
def templates():
    return {
        "templates": [
            {
                "id": item["id"],
                "title": item["title"],
                "category": item["category"],
                "document_type": item["document_type"],
                "description": item["description"],
            }
            for item in list_templates()
        ]
    }


def _run_generation(service: RagService, request: DocumentGenerateRequest, section_ids: list[str] | None):
    if request.template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown document template")
    try:
        result = service.generate_document(
            request.template_id,
            request.values,
            use_model=request.use_model,
            section_ids=section_ids,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown document template") from exc
    except (ValueError, RuntimeError) as exc:
        logger.exception("[DOCUMENT] generation dependency failure")
        raise HTTPException(status_code=503, detail="Document generation is unavailable") from exc
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)
    return result


@router.post("/generate")
def generate_document(request: DocumentGenerateRequest, service: RagService = Depends(get_service)):
    try:
        return _run_generation(service, request, request.section_ids)
    finally:
        service.close()


@router.post("/regenerate")
def regenerate_section(request: DocumentSectionRegenerateRequest, service: RagService = Depends(get_service)):
    try:
        return _run_generation(service, request, [request.section_id])
    finally:
        service.close()


@router.post("/revise")
def revise_document(request: DocumentReviseRequest, service: RagService = Depends(get_service)):
    if request.template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown document template")
    try:
        try:
            result = service.revise_document(
                request.template_id,
                request.values,
                request.sections,
                request.instruction,
                target_section_ids=request.target_section_ids,
                use_model=request.use_model,
                top_k=request.top_k,
                min_similarity=request.min_similarity,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown document template") from exc
        except (ValueError, RuntimeError) as exc:
            logger.exception("[DOCUMENT] revise dependency failure")
            raise HTTPException(status_code=503, detail="Document revise is unavailable") from exc
        if not result.get("ok"):
            raise HTTPException(status_code=422, detail=result)
        return result
    finally:
        service.close()


@router.post("/selection-edit")
def selection_edit(request: DocumentSelectionEditRequest, service: RagService = Depends(get_service)):
    try:
        try:
            result = service.selection_edit(
                selected_text=request.selected_text,
                action=request.action,
                surrounding_section=request.surrounding_section,
                document_title=request.document_title,
                jurisdiction=request.jurisdiction,
                custom_instruction=request.custom_instruction,
                language=request.language,
                use_model=request.use_model,
            )
        except (ValueError, RuntimeError) as exc:
            logger.exception("[DOCUMENT] selection-edit dependency failure")
            raise HTTPException(status_code=503, detail="Selection edit is unavailable") from exc
        if not result.get("ok"):
            raise HTTPException(status_code=422, detail=result)
        return result
    finally:
        service.close()
