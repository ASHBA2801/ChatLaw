"""Parameterized pgvector cosine retrieval for the existing legal_chunks table."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Protocol

from embeddings.base import EmbeddingProvider
from embeddings.validation import validate_embedding

from .models import RetrievalResponse, RetrievalResult
from .reranker import RerankWeights, document_score, extract_query_signals, rerank, section_score


DEFAULT_CANDIDATE_TOP_K = int(os.getenv("RETRIEVAL_CANDIDATE_TOP_K", "40"))
DEFAULT_VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.80"))
DEFAULT_KEYWORD_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", "0.10"))
DEFAULT_SECTION_WEIGHT = float(os.getenv("SECTION_WEIGHT", "0.07"))
DEFAULT_DOCUMENT_WEIGHT = float(os.getenv("DOCUMENT_WEIGHT", "0.03"))
_pool = None


class Cursor(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] = ...) -> Any: ...
    def fetchall(self) -> list[Any]: ...


class Connection(Protocol):
    def cursor(self) -> Cursor: ...


SEARCH_SQL = '''
SELECT
  c."id" AS chunk_id,
  d."id" AS document_id,
  d."title" AS document_title,
  c."content" AS content,
  c."sectionNumber" AS section_number,
  c."subsection" AS subsection,
  c."chapter" AS chapter,
  c."clause" AS clause,
  c."pageNumber" AS page_number,
  c."chunkIndex" AS chunk_index,
  1 - (c."embedding" <=> %s::vector) AS similarity,
  c."metadata" AS metadata
    ,s.name AS source_name, s.url AS source_url, s."sourceType" AS source_type,
    s."isOfficial" AS is_official
FROM "legal_chunks" AS c
JOIN "legal_documents" AS d ON d."id" = c."documentId"
LEFT JOIN LATERAL (
    SELECT name, url, "sourceType", "isOfficial" FROM "legal_sources"
    WHERE "documentId" = d."id" ORDER BY "isOfficial" DESC, id ASC LIMIT 1
) AS s ON TRUE
WHERE c."embedding" IS NOT NULL
  AND 1 - (c."embedding" <=> %s::vector) >= %s
ORDER BY c."embedding" <=> %s::vector
LIMIT %s
'''


class VectorSearcher:
    """Embed a query once and retrieve existing source text without mutation."""

    def __init__(self, connection: Connection, embedding_provider: EmbeddingProvider,
                 *, default_top_k: int = 8, default_min_similarity: float | None = None):
        if embedding_provider.info.dimension != 768:
            raise ValueError("Retrieval requires an embedding provider configured for dimension 768")
        if default_top_k <= 0:
            raise ValueError("default_top_k must be positive")
        self.connection = connection
        self.embedding_provider = embedding_provider
        self.default_top_k = default_top_k
        self.default_min_similarity = default_min_similarity

    def search(self, query: str, *, top_k: int | None = None,
               min_similarity: float | None = None, candidate_top_k: int | None = None,
               debug: bool = False, weights: RerankWeights | None = None) -> RetrievalResponse:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        resolved_top_k = self.default_top_k if top_k is None else top_k
        if resolved_top_k <= 0:
            raise ValueError("top_k must be positive")
        threshold = self.default_min_similarity if min_similarity is None else min_similarity
        if threshold is None:
            threshold = -1.0
        if not -1.0 <= threshold <= 1.0:
            raise ValueError("min_similarity must be between -1 and 1")
        resolved_candidate_top_k = candidate_top_k or max(DEFAULT_CANDIDATE_TOP_K, resolved_top_k)
        if resolved_candidate_top_k < resolved_top_k:
            raise ValueError("candidate_top_k must be at least top_k")

        print("[RETRIEVAL] Embedding query", flush=True)
        embedding_started = time.perf_counter()
        vector = self.embedding_provider.embed(normalized_query)
        vector = validate_embedding(vector, expected_dimension=768,
                                    provider=self.embedding_provider.info.provider,
                                    model=self.embedding_provider.info.model)
        print(f"[RETRIEVAL] Query embedding received ({time.perf_counter() - embedding_started:.2f}s)", flush=True)

        vector_text = "[" + ",".join(repr(float(value)) for value in vector) + "]"
        print("[RETRIEVAL] Searching pgvector", flush=True)
        database_started = time.perf_counter()
        cursor = self.connection.cursor()
        # Retrieve the full candidate pool first. The configured threshold is
        # applied after metadata-aware reranking so explicit legal references
        # can remain eligible even when their vector score is slightly lower.
        cursor.execute(SEARCH_SQL, (vector_text, vector_text, -1.0, vector_text, resolved_candidate_top_k))
        rows = cursor.fetchall()
        candidates = [RetrievalResult.from_row(_row_to_mapping(row)) for row in rows]
        resolved_weights = weights or RerankWeights(DEFAULT_VECTOR_WEIGHT, DEFAULT_KEYWORD_WEIGHT,
                                DEFAULT_SECTION_WEIGHT, DEFAULT_DOCUMENT_WEIGHT)
        ranked = rerank(candidates, normalized_query, resolved_weights)
        signals = extract_query_signals(normalized_query)
        ranked = [
            result for result in ranked
            if result.similarity >= threshold
            or section_score(signals, result) >= 1.0
            or document_score(signals, result) >= 1.0
        ]
        results = tuple(ranked[:resolved_top_k])
        if debug:
            for result in results:
                print(f"Candidate: {result.document_title} / Section {result.section_number or '—'}", flush=True)
                print(f"Vector: {result.vector_score or result.similarity:.4f}", flush=True)
                print(f"Keyword: {result.keyword_score or 0.0:.4f}", flush=True)
                print(f"Section: {result.section_score or 0.0:.4f}", flush=True)
                print(f"Document: {result.document_score or 0.0:.4f}", flush=True)
                print(f"Final: {result.rerank_score or result.similarity:.4f}", flush=True)
        print(f"[RETRIEVAL] Results returned ({len(results)}, db={time.perf_counter() - database_started:.2f}s)", flush=True)
        return RetrievalResponse(
            results=results,
            no_relevant_context=not results,
            embedding_latency_seconds=time.perf_counter() - embedding_started,
            database_latency_seconds=time.perf_counter() - database_started,
            candidate_results=tuple(ranked),
        )


def _row_to_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return dict(row)
    names = ("chunk_id", "document_id", "document_title", "content", "section_number",
             "subsection", "chapter", "clause", "page_number", "chunk_index", "similarity", "metadata",
             "source_name", "source_url", "source_type", "is_official")
    return dict(zip(names, row))


def connect_from_environment() -> Any:
    """Borrow a bounded pooled PostgreSQL connection."""
    global _pool
    try:
        from psycopg_pool import ConnectionPool  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Retrieval requires psycopg[binary,pool]") from exc
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for retrieval")
    timeout = int(float(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "30")))
    if _pool is None:
        _pool = ConnectionPool(database_url, min_size=1,
                                max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "10")),
                                timeout=timeout, kwargs={"connect_timeout": timeout},
                                open=True)
    return _PooledConnection(_pool.getconn(), _pool)


class _PooledConnection:
    def __init__(self, connection, pool):
        self._connection, self._pool, self._returned = connection, pool, False

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self):
        if not self._returned:
            self._pool.putconn(self._connection)
            self._returned = True


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def check_readiness() -> bool:
    connection = None
    try:
        connection = connect_from_environment()
        cursor = connection.cursor()
        cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector'), "
                       "to_regclass('legal_documents'), to_regclass('legal_chunks'), "
                       "to_regclass('legal_sources')")
        vector, documents, chunks, sources = cursor.fetchone()
        return bool(vector and documents and chunks and sources)
    except Exception:
        return False
    finally:
        if connection is not None:
            connection.close()


def ensure_cosine_index(connection: Connection) -> None:
    """Create the optional cosine index without changing the table schema."""
    cursor = connection.cursor()
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS "legal_chunks_embedding_cosine_idx" '
        'ON "legal_chunks" USING hnsw ("embedding" vector_cosine_ops)'
    )
    connection.commit()
