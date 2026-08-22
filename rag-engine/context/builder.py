"""Build immutable, metadata-rich legal context for grounded generation."""

from dataclasses import dataclass
from typing import Iterable

from retrieval.models import RetrievalResult
from verification.evidence import Evidence

ContextSource = Evidence


@dataclass(frozen=True)
class BuiltContext:
    text: str
    sources: tuple[ContextSource, ...]


def build_context(results: Iterable[RetrievalResult]) -> BuiltContext:
    unique = []
    seen = set()
    for result in results:
        fingerprint = (result.document_id, result.section_number, result.subsection,
                       result.chapter, result.clause, result.page_number, result.content)
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(result)
    sources = tuple(Evidence.from_result(result, index) for index, result in enumerate(unique, 1))
    blocks = []
    for source in sources:
        if source.source_type == "case_document":
            fields = [
                "Kind: CASE DOCUMENT (user-uploaded; not an official legal source)",
                f"Document: {source.document_title}",
                f"Page: {source.page_number if source.page_number is not None else 'Unavailable'}",
                f"Chunk ID: {source.chunk_id}",
            ]
        else:
            fields = [
                "Kind: LEGAL SOURCE",
                f"Document: {source.document_title}",
                f"Section: {source.section_number or 'Unavailable'}",
                f"Subsection: {source.subsection or 'Unavailable'}",
                f"Chapter: {source.chapter or 'Unavailable'}",
                f"Clause: {source.clause or 'Unavailable'}",
                f"Page: {source.page_number if source.page_number is not None else 'Unavailable'}",
                f"Chunk ID: {source.chunk_id}",
                f"Similarity: {source.similarity:.4f}" if source.similarity is not None else "Similarity: Unavailable",
            ]
        blocks.append(f"SOURCE {source.id}\n" + "\n".join(fields) + "\n\n" + source.content)
    return BuiltContext(text="\n\n".join(blocks), sources=sources)
