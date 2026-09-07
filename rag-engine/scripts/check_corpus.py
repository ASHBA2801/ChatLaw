#!/usr/bin/env python3
"""Read-only inventory of legal corpus and vector completeness."""

import os
import sys

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))


def main() -> int:
    try:
        import psycopg
    except ImportError:
        print("ERROR: install psycopg[binary,pool]", file=sys.stderr)
        return 1
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("ERROR: DATABASE_URL is not configured", file=sys.stderr)
        return 1
    query = """
    SELECT
      (SELECT count(*) FROM "legal_documents") AS documents,
      (SELECT count(*) FROM "legal_chunks") AS chunks,
      (SELECT count(*) FROM "legal_chunks" WHERE "embedding" IS NOT NULL) AS embedded,
      (SELECT count(*) FROM "legal_chunks" WHERE "embedding" IS NULL) AS missing,
      (SELECT coalesce(min(vector_dims("embedding")), 0) FROM "legal_chunks" WHERE "embedding" IS NOT NULL) AS min_dimension,
      (SELECT coalesce(max(vector_dims("embedding")), 0) FROM "legal_chunks" WHERE "embedding" IS NOT NULL) AS max_dimension,
      (SELECT count(*) FROM "legal_documents" d LEFT JOIN "legal_chunks" c ON c."documentId" = d."id" WHERE c."id" IS NULL) AS documents_without_chunks,
      (SELECT count(DISTINCT vector_dims("embedding")) FROM "legal_chunks" WHERE "embedding" IS NOT NULL) AS distinct_dimensions
    """
    try:
        with psycopg.connect(url, connect_timeout=int(float(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "30")))) as connection:
            row = connection.execute(query).fetchone()
    except Exception as exc:
        print(f"ERROR: corpus inventory unavailable ({type(exc).__name__})", file=sys.stderr)
        return 1
    labels = ("documents", "chunks", "embedded_chunks", "chunks_without_embeddings", "min_dimension", "max_dimension", "documents_without_chunks", "distinct_dimensions")
    for label, value in zip(labels, row):
        print(f"{label}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())