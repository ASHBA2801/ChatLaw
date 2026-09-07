"""Deterministic PDF text extraction for authorized case documents.

This module extracts page text with PyMuPDF. It does not call Gemini, write to
the legal corpus, or generate embeddings.
"""

from __future__ import annotations

from typing import Any

import pymupdf


def extract_pdf_bytes(data: bytes) -> dict[str, Any]:
    if not data:
        raise ValueError("PDF bytes are required")
    if not data.startswith(b"%PDF"):
        raise ValueError("File is not a PDF")

    document = pymupdf.open(stream=data, filetype="pdf")
    try:
        if document.is_encrypted and not document.authenticate(""):
            raise ValueError("Encrypted PDFs are not supported")
        pages = []
        for index, page in enumerate(document, start=1):
            pages.append({"page": index, "text": page.get_text() or ""})
        metadata = {
            key: value
            for key, value in (document.metadata or {}).items()
            if isinstance(value, str) and value.strip()
        }
        return {
            "page_count": document.page_count,
            "pages": pages,
            "metadata": metadata,
        }
    finally:
        document.close()
