"""Authenticated PDF text extraction. No Gemini, corpus, or embeddings."""

import logging

from fastapi import APIRouter, HTTPException, Request

from extraction.pdf import extract_pdf_bytes

router = APIRouter(prefix="/api/extract", tags=["extract"])
logger = logging.getLogger(__name__)
MAX_PDF_BYTES = 16 * 1024 * 1024


@router.post("/pdf")
async def extract_pdf(request: Request) -> dict:
    data = await request.body()
    if not data:
        raise HTTPException(status_code=422, detail="A PDF file is required")
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF is too large")
    try:
        return extract_pdf_bytes(data)
    except ValueError as exc:
        logger.info("[EXTRACT] rejected PDF: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[EXTRACT] PDF parsing failed")
        raise HTTPException(status_code=422, detail="The PDF could not be read") from exc
