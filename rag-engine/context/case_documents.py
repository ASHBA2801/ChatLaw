"""Attach authorized case-document excerpts to existing retrieval results."""

from retrieval.models import RetrievalResponse, RetrievalResult


def case_excerpt_to_result(excerpt: dict, index: int) -> RetrievalResult:
    document_id = str(excerpt["document_id"])
    page = int(excerpt["page"])
    file_name = str(excerpt["file_name"])
    return RetrievalResult(
        chunk_id=f"case:{document_id}:p{page}:{index}",
        document_id=document_id,
        document_title=file_name,
        content=str(excerpt["text"]),
        section_number=None,
        subsection=None,
        chapter=None,
        clause=None,
        page_number=page,
        chunk_index=index,
        similarity=1.0,
        metadata={"kind": "case_document", "file_name": file_name},
        source_name=file_name,
        source_type="case_document",
        is_official=False,
    )


def attach_case_context(retrieval: RetrievalResponse, case_context: list | None) -> RetrievalResponse:
    extras = tuple(
        case_excerpt_to_result(item if isinstance(item, dict) else item.model_dump(), index)
        for index, item in enumerate(case_context or (), start=1)
    )
    if not extras:
        return retrieval
    results = retrieval.results + extras
    return RetrievalResponse(
        results,
        False,
        embedding_latency_seconds=retrieval.embedding_latency_seconds,
        database_latency_seconds=retrieval.database_latency_seconds,
        candidate_results=retrieval.candidate_results,
    )
