"""Structured results returned by the RAG-05 vector retrieval engine."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    section_number: str | None
    subsection: str | None
    chapter: str | None
    clause: str | None
    page_number: int | None
    chunk_index: int
    similarity: float
    metadata: Mapping[str, Any]
    vector_score: float | None = None
    keyword_score: float | None = None
    section_score: float | None = None
    document_score: float | None = None
    concept_score: float | None = None
    rerank_score: float | None = None
    source_name: str | None = None
    source_url: str | None = None
    source_type: str | None = None
    is_official: bool | None = None

    def with_scores(self, **scores: float) -> "RetrievalResult":
        return RetrievalResult(
            chunk_id=self.chunk_id, document_id=self.document_id,
            document_title=self.document_title, content=self.content,
            section_number=self.section_number, subsection=self.subsection,
            chapter=self.chapter, clause=self.clause, page_number=self.page_number,
            chunk_index=self.chunk_index, similarity=self.similarity,
            metadata=self.metadata, vector_score=self.similarity, **scores,
        )

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "RetrievalResult":
        return cls(
            chunk_id=str(row["chunk_id"]),
            document_id=str(row["document_id"]),
            document_title=str(row["document_title"]),
            content=str(row["content"]),
            section_number=row.get("section_number"),
            subsection=row.get("subsection"),
            chapter=row.get("chapter"),
            clause=row.get("clause"),
            page_number=row.get("page_number"),
            chunk_index=int(row["chunk_index"]),
            similarity=float(row["similarity"]),
            metadata=row.get("metadata") or {},
            source_name=row.get("source_name"), source_url=row.get("source_url"),
            source_type=row.get("source_type"), is_official=row.get("is_official"),
        )


@dataclass(frozen=True)
class RetrievalResponse:
    results: tuple[RetrievalResult, ...]
    no_relevant_context: bool
    embedding_latency_seconds: float = 0.0
    database_latency_seconds: float = 0.0
    candidate_results: tuple[RetrievalResult, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "results": [result.__dict__ for result in self.results],
            "no_relevant_context": self.no_relevant_context,
            "embedding_latency_seconds": self.embedding_latency_seconds,
            "database_latency_seconds": self.database_latency_seconds,
        }
