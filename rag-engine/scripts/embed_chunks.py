#!/usr/bin/env python3
"""Safe RAG-03 embedding and database ingestion CLI.

Dry-run is the default safety mode. Real ingestion requires --execute and
explicit environment configuration; it is never run automatically.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

load_dotenv(rag_engine_dir / ".env")

from embeddings.ingestion import EmbeddingIngestor
from embeddings.provider import EmbeddingConfigurationError, create_embedding_provider, load_embedding_info
from embeddings.usage_ledger import record_run
from embeddings.validation import validate_chunk_record


def write_report(metadata_dir: Path, report: dict) -> None:
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "embedding_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "CHATLAW EMBEDDING INGESTION REPORT (RAG-03)",
        "=" * 55,
        f"Generated: {report['processing_timestamp']}",
        f"Dry run: {report['dry_run']}",
        f"Provider: {report.get('embedding_provider') or 'unresolved'}",
        f"Model: {report.get('embedding_model') or 'unresolved'}",
        f"Dimension: {report.get('embedding_dimension') or 'unresolved'}",
        "",
        f"Documents discovered: {report['documents_discovered']}",
        f"Chunks discovered: {report['chunks_discovered']}",
        f"Chunks skipped: {report['chunks_skipped']}",
        f"Chunks embedded: {report['chunks_embedded']}",
        f"Chunks inserted: {report['chunks_inserted']}",
        f"Chunks updated: {report['chunks_updated']}",
        f"Chunks failed: {report['chunks_failed']}",
        f"Batches processed: {report['batches_processed']}",
        f"Retries: {report['retry_count']}",
        f"Duration: {report['duration_seconds']:.2f}s",
        "",
        "Errors:",
        *[f"- {error}" for error in report["errors"]],
    ]
    (metadata_dir / "embedding_report.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatLaw RAG-03 embedding/database ingestion")
    parser.add_argument("--input", type=Path, default=rag_engine_dir / "data" / "chunks")
    parser.add_argument("--metadata-dir", type=Path, default=rag_engine_dir / "data" / "metadata")
    parser.add_argument("--document", help="Only process one JSONL stem")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan only; never call APIs or DB")
    parser.add_argument("--execute", action="store_true", help="Enable real embedding and database writes")
    parser.add_argument(
        "--one-chunk-timing",
        action="store_true",
        help="Process exactly one chunk and print embedding/database timings; requires --execute",
    )
    parser.add_argument("--force", action="store_true", help="Reserved for future explicit re-embedding behavior")
    args = parser.parse_args()

    if args.execute and args.dry_run:
        parser.error("--execute and --dry-run cannot be combined")
    if args.one_chunk_timing and not args.execute:
        parser.error("--one-chunk-timing requires --execute")
    dry_run = not args.execute
    started = time.time()
    report = {
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "documents_discovered": 0,
        "chunks_discovered": 0,
        "chunks_skipped": 0,
        "chunks_embedded": 0,
        "chunks_inserted": 0,
        "chunks_updated": 0,
        "chunks_failed": 0,
        "batches_processed": 0,
        "retry_count": 0,
        "embedding_provider": None,
        "embedding_model": None,
        "embedding_dimension": None,
        "duration_seconds": 0.0,
        "errors": [],
    }

    try:
        info = load_embedding_info()
        report.update({
            "embedding_provider": info.provider,
            "embedding_model": info.model,
            "embedding_dimension": info.dimension,
        })
        if info.dimension != 768:
            raise ValueError(
                f"Database compatibility failure: expected EMBEDDING_DIMENSION=768 for vector(768), "
                f"got {info.dimension}; provider={info.provider}, model={info.model}"
            )

        records = EmbeddingIngestor.load_chunks(args.input, args.document)
        if args.one_chunk_timing:
            if not records:
                raise ValueError("No chunks found for one-chunk timing mode")
            records = records[:1]
            print("[TIMING] One-chunk mode: exactly 1 chunk selected", flush=True)
        report["documents_discovered"] = len({record["document_id"] for record in records})
        report["chunks_discovered"] = len(records)
        batch_size = args.batch_size or info.batch_size
        if batch_size <= 0:
            raise ValueError("batch size must be positive")

        # Dry-run deliberately does not construct a provider, import a DB driver,
        # call an embedding API, or write any database row.
        if dry_run:
            provider = _ConfigurationOnlyProvider(info)
            plan = EmbeddingIngestor(provider, expected_dimension=768, batch_size=batch_size).dry_run_plan(records)
            report["batches_processed"] = plan["batches"]
            print(json.dumps({"mode": "dry-run", **plan}, indent=2))
        else:
            print("[EMBED] Starting provider", flush=True)
            print("[EMBED] Creating Gemini client", flush=True)
            provider = create_embedding_provider()
            ingestor = EmbeddingIngestor(provider, expected_dimension=768, batch_size=batch_size)
            vectors, embed_stats = ingestor.generate_embeddings_with_reuse(records, reuse_lookup=_lookup_existing_embedding)
            report["chunks_embedded"] = embed_stats["new_chunks_embedded"]
            report["chunks_skipped"] = embed_stats["existing_embeddings_reused"]
            report["batches_processed"] = (embed_stats["embedding_api_calls"] + batch_size - 1) // batch_size
            _execute_database_writes(records, vectors, provider.info, report)
            record_run(
                run_type="embed_execute",
                generation_calls=0,
                embedding_api_calls=embed_stats["embedding_api_calls"],
                new_chunks_embedded=embed_stats["new_chunks_embedded"],
                existing_embeddings_reused=embed_stats["existing_embeddings_reused"],
                notes=f"document={args.document or 'all'}",
            )

    except Exception as exc:
        report["errors"].append(str(exc))
        write_report(args.metadata_dir, {**report, "duration_seconds": round(time.time() - started, 2)})
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report["duration_seconds"] = round(time.time() - started, 2)
    write_report(args.metadata_dir, report)
    print(f"Embedding report written to {args.metadata_dir}")
    return 0


class _ConfigurationOnlyProvider:
    def __init__(self, info):
        self._info = info

    @property
    def info(self):
        return self._info

    def embed(self, text):
        raise RuntimeError("Dry-run provider must not embed")


def _lookup_existing_embedding(chunk_id: str, chunk_hash: str) -> list[float] | None:
    try:
        import psycopg  # type: ignore
    except ImportError:
        return None
    from database.upsert import ChunkUpserter

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None
    try:
        db_timeout = float(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "30"))
    except ValueError:
        db_timeout = 30.0
    with psycopg.connect(database_url, connect_timeout=int(db_timeout)) as connection:
        upserter = ChunkUpserter(_PsycopgAdapter(connection))
        existing = upserter.get_existing_chunk(chunk_id)
        if existing is None:
            return None
        existing_hash, vector = existing
        if existing_hash == chunk_hash and vector is not None:
            return vector
    return None


def _execute_database_writes(records, vectors, info, report) -> None:
    """Execute writes only after explicit --execute and successful embeddings."""
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Real ingestion requires psycopg[binary]; install it manually") from exc

    from database.upsert import ChunkUpserter

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for real ingestion")
    try:
        db_timeout = float(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "30"))
    except ValueError as exc:
        raise RuntimeError("DATABASE_CONNECT_TIMEOUT_SECONDS must be a number") from exc
    if db_timeout <= 0:
        raise RuntimeError("DATABASE_CONNECT_TIMEOUT_SECONDS must be positive")
    print("[DB] Connecting", flush=True)
    connect_started = time.perf_counter()
    with psycopg.connect(database_url, connect_timeout=int(db_timeout)) as connection:
        print(f"[DB] Connected ({time.perf_counter() - connect_started:.2f}s)", flush=True)
        adapter = _PsycopgAdapter(connection)
        upserter = ChunkUpserter(adapter)
        by_document = {}
        document_ids = {}
        for record, vector in tqdm(zip(records, vectors), total=len(records), desc="Writing chunks"):
            print("[DB] Inserting batch", flush=True)
            insert_started = time.perf_counter()
            source_document_id = record["document_id"]
            if source_document_id not in document_ids:
                document_ids[source_document_id] = upserter.upsert_document(
                    record, record.get("document_sha256", "")
                )
            document_id = document_ids[source_document_id]
            result = upserter.upsert_chunk(record, document_id, vector, info)
            by_document.setdefault(document_id, 0)
            by_document[document_id] += 1
            report["chunks_inserted"] += 1
        connection.commit()
        print(
            f"[DB] Batch committed ({time.perf_counter() - insert_started:.2f}s)",
            flush=True,
        )


class _PsycopgAdapter:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, *params):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor


if __name__ == "__main__":
    raise SystemExit(main())
