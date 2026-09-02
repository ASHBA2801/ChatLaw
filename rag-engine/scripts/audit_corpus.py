#!/usr/bin/env python3
"""Generate a comprehensive legal corpus inventory from catalog, Law_files, and DB."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
repo_root = rag_engine_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from dotenv import load_dotenv

load_dotenv(rag_engine_dir / ".env")

from acts.catalog import get_default_catalog_path, load_catalog


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_law_file(source_file: str | None) -> Path | None:
    if not source_file:
        return None
    candidates = [
        repo_root / source_file,
        rag_engine_dir / source_file,
        repo_root / "Law_files" / Path(source_file).name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_db_documents() -> dict[str, dict]:
    """Map source_document_id -> DB stats."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return {}
    try:
        import psycopg
    except ImportError:
        return {}

    query = """
    SELECT
      d."id",
      d."title",
      d."documentType",
      d."language",
      d."contentHash",
      d.metadata->>'source_document_id' AS source_document_id,
      d.metadata->>'act_id' AS act_id,
      d.metadata->>'domain' AS domain,
      d.metadata->>'status' AS status,
      COUNT(c."id") AS chunk_count,
      COUNT(c."embedding") FILTER (WHERE c."embedding" IS NOT NULL) AS embedded_count
    FROM "legal_documents" d
    LEFT JOIN "legal_chunks" c ON c."documentId" = d."id"
    GROUP BY d."id", d."title", d."documentType", d."language", d."contentHash",
             d.metadata->>'source_document_id', d.metadata->>'act_id',
             d.metadata->>'domain', d.metadata->>'status'
    """
    result: dict[str, dict] = {}
    try:
        with psycopg.connect(
            url, connect_timeout=int(float(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "30")))
        ) as connection:
            for row in connection.execute(query).fetchall():
                source_id = row[5] or row[0]
                result[str(source_id)] = {
                    "db_document_id": row[0],
                    "db_title": row[1],
                    "document_type": row[2],
                    "language": row[3],
                    "content_hash": row[4],
                    "act_id": row[6],
                    "domain": row[7],
                    "status": row[8],
                    "chunk_count": int(row[9] or 0),
                    "embedded_count": int(row[10] or 0),
                }
    except Exception as exc:
        print(f"WARN: DB unavailable ({type(exc).__name__})", file=sys.stderr)
    return result


def _load_chunk_files() -> dict[str, int]:
    counts: dict[str, int] = {}
    chunks_dir = rag_engine_dir / "data" / "chunks"
    if not chunks_dir.is_dir():
        return counts
    for path in chunks_dir.glob("*.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            counts[path.stem] = sum(1 for line in handle if line.strip())
    return counts


def build_inventory() -> dict:
    catalog = load_catalog()
    db_docs = _load_db_documents()
    chunk_files = _load_chunk_files()
    seen_hashes: dict[str, list[str]] = {}
    documents: list[dict] = []

    for entry in catalog.all_entries():
        law_path = _resolve_law_file(entry.source_file)
        file_hash = _sha256(law_path) if law_path else None
        if file_hash:
            seen_hashes.setdefault(file_hash, []).append(entry.act_id)

        db_match = None
        for key, stats in db_docs.items():
            if stats.get("act_id") == entry.act_id or entry.act_id.lower() in key.lower():
                db_match = stats
                break
        if db_match is None and entry.source_file:
            stem = Path(entry.source_file).stem.replace(",", "").replace(" ", "_")
            for key, stats in db_docs.items():
                if stem.lower() in key.lower() or key.lower() in stem.lower():
                    db_match = stats
                    break

        domains = list(getattr(entry, "domains", ()) or ())
        if not domains and entry.domain:
            domains = [entry.domain]

        chunk_count = 0
        if db_match:
            chunk_count = db_match["chunk_count"]
        else:
            for stem, count in chunk_files.items():
                alias_hit = any(
                    alias.replace(" ", "_").lower() in stem.lower()
                    for alias in (entry.act_id, entry.short_title, *entry.aliases)
                )
                if alias_hit:
                    chunk_count = max(chunk_count, count)

        documents.append({
            "act_id": entry.act_id,
            "official_title": entry.official_title,
            "short_title": entry.short_title,
            "year": entry.year,
            "act_number": entry.act_number,
            "domains": domains,
            "domain": entry.domain,
            "category": entry.category,
            "sub_domains": list(entry.sub_domains),
            "document_type": getattr(entry, "document_type_normalized", entry.document_type),
            "jurisdiction_level": getattr(entry, "jurisdiction_level", "CENTRAL"),
            "jurisdiction": entry.jurisdiction,
            "status": entry.status,
            "effective_from": entry.effective_from,
            "effective_to": getattr(entry, "effective_to", None),
            "language": "en",
            "source_authority": entry.source_authority,
            "official_url": entry.official_url,
            "source_type": getattr(entry, "source_type", "official_gazette"),
            "source_file": entry.source_file,
            "source_sha256": file_hash,
            "source_present": law_path is not None,
            "ingestion_status": entry.ingestion_status,
            "ingestion_stage": getattr(entry, "ingestion_stage", None),
            "chunk_count": chunk_count,
            "embeddings_count": db_match["embedded_count"] if db_match else 0,
            "db_document_id": db_match["db_document_id"] if db_match else None,
            "is_duplicate_source": False,
        })

    duplicate_hashes = {h: ids for h, ids in seen_hashes.items() if len(ids) > 1}
    for doc in documents:
        if doc["source_sha256"] and doc["source_sha256"] in duplicate_hashes:
            doc["is_duplicate_source"] = len(duplicate_hashes[doc["source_sha256"]]) > 1

    ingested = [d for d in documents if d["ingestion_status"] == "ingested"]
    pending = [d for d in documents if d["ingestion_status"] == "pending_source"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_version": "2.0",
        "catalog_path": str(get_default_catalog_path()),
        "summary": {
            "total_catalog_acts": len(documents),
            "ingested_acts": len(ingested),
            "pending_source_acts": len(pending),
            "total_chunks_in_db": sum(d["chunk_count"] for d in documents),
            "total_embeddings_in_db": sum(d["embeddings_count"] for d in documents),
            "duplicate_source_hashes": len(duplicate_hashes),
            "db_available": bool(db_docs),
        },
        "duplicate_hashes": duplicate_hashes,
        "documents": documents,
    }


def main() -> int:
    inventory = build_inventory()
    out_dir = repo_root / "data" / "evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "legal_corpus_inventory.json"
    out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps(inventory["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
