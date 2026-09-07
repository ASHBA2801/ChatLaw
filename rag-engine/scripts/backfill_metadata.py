#!/usr/bin/env python3
"""Backfill catalog metadata and legal_sources for ingested documents without re-embedding."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from dotenv import load_dotenv

load_dotenv(rag_engine_dir / ".env")

from acts.catalog import get_catalog, reset_catalog_cache
from database.upsert import ChunkUpserter


def main() -> int:
    reset_catalog_cache()
    catalog = get_catalog()
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1
    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg required", file=sys.stderr)
        return 1

    class Adapter:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, query, *params):
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur

    with psycopg.connect(url) as conn:
        adapter = Adapter(conn)
        upserter = ChunkUpserter(adapter)
        cur = adapter.execute(
            'SELECT d."id", d.metadata->>\'source_document_id\' AS source_id, d."contentHash" '
            'FROM "legal_documents" d'
        )
        rows = cur.fetchall()
        updated_docs = 0
        updated_chunks = 0
        for doc_id, source_id, content_hash in rows:
            act = catalog.find_by_alias(source_id) if source_id else None
            if act is None:
                continue
            meta = upserter.document_metadata({"document_id": source_id, "document_title": act.official_title}, content_hash or "")
            adapter.execute(
                'UPDATE "legal_documents" SET '
                '"documentType" = %s, "authority" = %s, "sourceUrl" = %s, '
                '"effectiveDate" = %s::date, "version" = %s, "metadata" = %s::jsonb, '
                '"updatedAt" = now() WHERE "id" = %s',
                act.document_type.lower() if act.document_type else "statute",
                act.source_authority,
                act.official_url,
                act.effective_from,
                act.version,
                json.dumps(meta),
                doc_id,
            )
            upserter.upsert_legal_source(doc_id, act)
            updated_docs += 1

            chunk_cur = adapter.execute(
                'SELECT "id", "metadata" FROM "legal_chunks" WHERE "documentId" = %s',
                doc_id,
            )
            for chunk_id, chunk_meta_raw in chunk_cur.fetchall():
                chunk_meta = chunk_meta_raw if isinstance(chunk_meta_raw, dict) else json.loads(chunk_meta_raw or "{}")
                chunk_meta.update({
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
                    "source_authority": act.source_authority,
                    "source_url": act.official_url,
                })
                adapter.execute(
                    'UPDATE "legal_chunks" SET "metadata" = %s::jsonb WHERE "id" = %s',
                    json.dumps(chunk_meta),
                    chunk_id,
                )
                updated_chunks += 1
        conn.commit()
    print(json.dumps({
        "documents_updated": updated_docs,
        "chunks_updated": updated_chunks,
        "embedding_api_calls": 0,
        "generation_calls": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
