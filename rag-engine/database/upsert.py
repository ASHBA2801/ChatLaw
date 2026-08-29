"""Safe PostgreSQL/pgvector upsert adapter for RAG-03.

This module intentionally accepts a small DB protocol so dry-run and tests do
not require a live database. It uses the existing schema without migrations.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from embeddings.base import EmbeddingProviderInfo

try:
    from acts.catalog import get_catalog
except ImportError:
    get_catalog = None


class DatabaseClient(Protocol):
    def execute(self, query: str, *params: Any) -> Any: ...


class ChunkUpserter:
    """Upserts documents/chunks while preserving the existing schema contract."""

    def __init__(self, client: DatabaseClient):
        self.client = client
        self.catalog = get_catalog() if get_catalog else None

    @classmethod
    def _resolve_act_cls(cls, doc_id_or_title: str | None):
        if not get_catalog or not doc_id_or_title:
            return None
        catalog = get_catalog()
        return catalog.find_by_alias(doc_id_or_title) or catalog.get(doc_id_or_title)

    @classmethod
    def document_metadata(cls, chunk: Mapping[str, Any], source_file_hash: str) -> dict[str, Any]:
        source_doc_id = chunk.get("document_id")
        doc_title = chunk.get("document_title")
        act = cls._resolve_act_cls(source_doc_id) or cls._resolve_act_cls(doc_title)

        meta: dict[str, Any] = {
            "source_document_id": source_doc_id,
            "source_document_sha256": source_file_hash,
            "document_title": doc_title,
        }
        if act:
            meta.update({
                "act_id": act.act_id,
                "act_title": act.official_title,
                "short_title": act.short_title,
                "act_year": act.year,
                "act_number": act.act_number,
                "domain": act.domain,
                "category": act.category,
                "document_type": act.document_type,
                "status": act.status,
                "effective_from": act.effective_from,
                "source_authority": act.source_authority,
                "source_url": act.official_url,
                "jurisdiction": act.jurisdiction,
            })
        return meta

    @classmethod
    def chunk_metadata(cls, chunk: Mapping[str, Any], info: EmbeddingProviderInfo) -> dict[str, Any]:
        fields = (
            "chunk_id", "chunk_hash", "document_id", "part", "subclause", "schedule",
            "page_start", "page_end", "chunk_part", "total_parts", "is_continuation",
            "parent_chunk_id", "context_path", "context_prefix", "chunk_type",
        )
        metadata = {key: chunk.get(key) for key in fields}

        source_doc_id = chunk.get("document_id")
        doc_title = chunk.get("document_title")
        act = cls._resolve_act_cls(source_doc_id) or cls._resolve_act_cls(doc_title)

        if act:
            metadata.update({
                "act_id": act.act_id,
                "domain": act.domain,
                "category": act.category,
                "document_type": act.document_type,
                "act_year": act.year,
            })

        metadata.update({
            "embedding_provider": info.provider,
            "embedding_model": info.model,
            "embedding_dimension": info.dimension,
            "embedding_generated_at": datetime.now(timezone.utc).isoformat(),
        })
        return metadata

    def find_document_id(self, source_document_id: str, source_hash: str) -> str | None:
        rows = self.client.execute(
            'SELECT "id" FROM "legal_documents" '
            'WHERE metadata->>\'source_document_id\' = %s LIMIT 1',
            source_document_id,
        )
        row = rows.fetchone() if hasattr(rows, "fetchone") else None
        return row[0] if row else None

    def upsert_document(self, chunk: Mapping[str, Any], source_hash: str) -> str:
        source_id = str(chunk["document_id"])
        existing_id = self.find_document_id(source_id, source_hash)
        metadata = json.dumps(self.document_metadata(chunk, source_hash))
        title = chunk.get("document_title") or source_id
        if existing_id:
            self.client.execute(
                'UPDATE "legal_documents" SET "title" = %s, "contentHash" = %s, '
                '"metadata" = %s::jsonb, "updatedAt" = now() WHERE "id" = %s',
                title, source_hash, metadata, existing_id,
            )
            return existing_id

        deterministic_id = "ragdoc_" + hashlib.sha256(
            f"{source_id}:{source_hash}".encode("utf-8")
        ).hexdigest()[:40]
        rows = self.client.execute(
            'INSERT INTO "legal_documents" '
            '("id", "title", "documentType", "language", "contentHash", "metadata", "createdAt", "updatedAt") '
            'VALUES (%s, %s, %s, %s, %s, %s::jsonb, now(), now()) RETURNING "id"',
            deterministic_id, title, "act", "en", source_hash, metadata,
        )
        row = rows.fetchone()
        return row[0]

    def upsert_chunk(
        self,
        chunk: Mapping[str, Any],
        document_db_id: str,
        embedding: list[float],
        info: EmbeddingProviderInfo,
    ) -> str:
        metadata = json.dumps(self.chunk_metadata(chunk, info))
        # The Python deterministic chunk_id is the database primary key. This
        # makes unchanged and re-run ingestion idempotent without schema changes.
        rows = self.client.execute(
            'INSERT INTO "legal_chunks" '
            '("id", "documentId", "content", "sectionNumber", "subsection", "chapter", '
            '"clause", "pageNumber", "chunkIndex", "embedding", "metadata", "createdAt") '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb, now()) '
            'ON CONFLICT ("id") DO UPDATE SET '
            '"documentId" = EXCLUDED."documentId", "content" = EXCLUDED."content", '
            '"sectionNumber" = EXCLUDED."sectionNumber", "subsection" = EXCLUDED."subsection", '
            '"chapter" = EXCLUDED."chapter", "clause" = EXCLUDED."clause", '
            '"pageNumber" = EXCLUDED."pageNumber", "chunkIndex" = EXCLUDED."chunkIndex", '
            '"embedding" = EXCLUDED."embedding", "metadata" = EXCLUDED."metadata" '
            'RETURNING "id"',
            chunk["chunk_id"],
            document_db_id,
            chunk["content"],
            chunk.get("section"),
            chunk.get("subsection"),
            chunk.get("chapter"),
            chunk.get("clause"),
            chunk.get("page_start"),
            chunk.get("chunk_index"),
            "[" + ",".join(repr(float(value)) for value in embedding) + "]",
            metadata,
        )
        row = rows.fetchone()
        return row[0] if row else str(chunk["chunk_id"])
