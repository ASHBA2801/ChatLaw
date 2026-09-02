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
    from acts.catalog import ActCatalogEntry, get_catalog
except ImportError:
    get_catalog = None
    ActCatalogEntry = None  # type: ignore


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
    def _act_document_fields(cls, act) -> dict[str, Any]:
        return {
            "act_id": act.act_id,
            "act_title": act.official_title,
            "short_title": act.short_title,
            "act_year": act.year,
            "act_number": act.act_number,
            "domain": act.domain,
            "domains": list(act.domains or (act.domain,)),
            "category": act.category,
            "document_type": act.document_type,
            "status": act.status,
            "effective_from": act.effective_from,
            "effective_to": act.effective_to,
            "source_authority": act.source_authority,
            "source_url": act.official_url,
            "source_type": act.source_type,
            "jurisdiction": act.jurisdiction,
            "jurisdiction_level": act.jurisdiction_level,
            "personal_law_framework": act.personal_law_framework,
            "gst_component": act.gst_component,
            "assessment_year_from": act.assessment_year_from,
            "assessment_year_to": act.assessment_year_to,
            "implementation_notes": act.implementation_notes,
        }

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
            meta.update(cls._act_document_fields(act))
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
                "domains": list(act.domains or (act.domain,)),
                "category": act.category,
                "document_type": act.document_type,
                "act_year": act.year,
                "jurisdiction_level": act.jurisdiction_level,
                "status": act.status,
                "effective_from": act.effective_from,
                "effective_to": act.effective_to,
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

    def get_existing_chunk(self, chunk_id: str) -> tuple[str | None, list[float] | None] | None:
        rows = self.client.execute(
            'SELECT metadata->>\'chunk_hash\', embedding::text FROM "legal_chunks" WHERE "id" = %s LIMIT 1',
            chunk_id,
        )
        row = rows.fetchone() if hasattr(rows, "fetchone") else None
        if not row:
            return None
        chunk_hash, embedding_text = row[0], row[1]
        if embedding_text is None:
            return chunk_hash, None
        # Parse pgvector text format [0.1,0.2,...]
        try:
            vector = json.loads(embedding_text.replace(" ", ""))
            return chunk_hash, [float(v) for v in vector]
        except (json.JSONDecodeError, ValueError):
            return chunk_hash, None

    def upsert_legal_source(self, document_db_id: str, act) -> None:
        if act is None:
            return
        rows = self.client.execute(
            'SELECT "id" FROM "legal_sources" WHERE "documentId" = %s AND "url" = %s LIMIT 1',
            document_db_id,
            act.official_url,
        )
        existing = rows.fetchone() if hasattr(rows, "fetchone") else None
        if existing:
            self.client.execute(
                'UPDATE "legal_sources" SET "name" = %s, "authority" = %s, '
                '"sourceType" = %s, "isOfficial" = %s, "lastVerifiedAt" = now(), '
                '"updatedAt" = now() WHERE "id" = %s',
                act.official_title,
                act.source_authority,
                act.source_type,
                True,
                existing[0],
            )
            return
        source_id = "src_" + hashlib.sha256(
            f"{document_db_id}:{act.official_url}".encode("utf-8")
        ).hexdigest()[:32]
        self.client.execute(
            'INSERT INTO "legal_sources" '
            '("id", "documentId", "name", "authority", "url", "sourceType", "isOfficial", '
            '"lastVerifiedAt", "createdAt", "updatedAt") '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now(), now()) '
            'ON CONFLICT ("id") DO UPDATE SET '
            '"name" = EXCLUDED."name", "authority" = EXCLUDED."authority", '
            '"url" = EXCLUDED."url", "sourceType" = EXCLUDED."sourceType", '
            '"isOfficial" = EXCLUDED."isOfficial", "lastVerifiedAt" = now(), '
            '"updatedAt" = now()',
            source_id,
            document_db_id,
            act.official_title,
            act.source_authority,
            act.official_url,
            act.source_type,
            True,
        )

    def upsert_document(self, chunk: Mapping[str, Any], source_hash: str) -> str:
        source_id = str(chunk["document_id"])
        act = self._resolve_act_cls(source_id) or self._resolve_act_cls(chunk.get("document_title"))
        existing_id = self.find_document_id(source_id, source_hash)
        metadata = json.dumps(self.document_metadata(chunk, source_hash))
        title = chunk.get("document_title") or source_id
        doc_type = (act.document_type.lower() if act and act.document_type else "statute")
        authority = act.source_authority if act else None
        source_url = act.official_url if act else None
        effective_date = act.effective_from if act else None
        version = act.version if act else None

        if existing_id:
            self.client.execute(
                'UPDATE "legal_documents" SET "title" = %s, "documentType" = %s, '
                '"authority" = %s, "sourceUrl" = %s, "effectiveDate" = %s::date, '
                '"version" = %s, "contentHash" = %s, "metadata" = %s::jsonb, '
                '"updatedAt" = now() WHERE "id" = %s',
                title,
                doc_type,
                authority,
                source_url,
                effective_date,
                version,
                source_hash,
                metadata,
                existing_id,
            )
            self.upsert_legal_source(existing_id, act)
            return existing_id

        deterministic_id = "ragdoc_" + hashlib.sha256(
            f"{source_id}:{source_hash}".encode("utf-8")
        ).hexdigest()[:40]
        rows = self.client.execute(
            'INSERT INTO "legal_documents" '
            '("id", "title", "documentType", "authority", "sourceUrl", "effectiveDate", '
            '"version", "language", "contentHash", "metadata", "createdAt", "updatedAt") '
            'VALUES (%s, %s, %s, %s, %s, %s::date, %s, %s, %s, %s::jsonb, now(), now()) RETURNING "id"',
            deterministic_id,
            title,
            doc_type,
            authority,
            source_url,
            effective_date,
            version,
            "en",
            source_hash,
            metadata,
        )
        row = rows.fetchone()
        doc_id = row[0]
        self.upsert_legal_source(doc_id, act)
        return doc_id

    def upsert_chunk(
        self,
        chunk: Mapping[str, Any],
        document_db_id: str,
        embedding: list[float],
        info: EmbeddingProviderInfo,
    ) -> str:
        metadata = json.dumps(self.chunk_metadata(chunk, info))
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
