"""User-triggered document summarization. Gemini is used only on this path."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/summarize", tags=["summarize"])
logger = logging.getLogger(__name__)
MAX_SUMMARY_CHARS = 20_000

SUMMARY_PROMPT = """You are ChatLaw's document summarizer.

Summarize only the supplied CASE DOCUMENT TEXT. Do not use outside legal knowledge.
Do not invent parties, dates, amounts, clauses, or obligations that are not in the text.
If a detail is missing, say it is not stated in the supplied text.
Clearly distinguish quoted document terms from your paraphrase.
This is an AI-generated informational summary, not legal advice and not a legal conclusion.

Return short sections when present in the text:
- Parties
- Agreement period
- Deposit terms
- Obligations
- Termination terms
- Important clauses

CASE DOCUMENT TEXT
"""


class SummarizeDocumentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_SUMMARY_CHARS)
    file_name: str = Field(default="document.pdf", max_length=255)

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be empty")
        return value[:MAX_SUMMARY_CHARS]


@router.post("/document")
def summarize_document(request: SummarizeDocumentRequest) -> dict[str, str]:
    try:
        from generation.gemini import GeminiGenerator

        generator = GeminiGenerator()
        prompt = (
            f"{SUMMARY_PROMPT}Filename: {request.file_name}\n\n{request.text}"
        )
        result = generator.generate_text(prompt)
        return {
            "summary": result.answer,
            "model": result.model,
            "label": "AI-generated summary",
        }
    except (ValueError, RuntimeError) as exc:
        logger.exception("[SUMMARIZE] generation unavailable")
        raise HTTPException(status_code=503, detail="Document summary is unavailable") from exc
    except Exception as exc:
        logger.exception("[SUMMARIZE] request failed")
        raise HTTPException(status_code=500, detail="Document summary failed") from exc
