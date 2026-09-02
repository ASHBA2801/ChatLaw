#!/usr/bin/env python3
"""Update catalog ingestion_status from DB chunk presence."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
repo_root = rag_engine_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from dotenv import load_dotenv

load_dotenv(rag_engine_dir / ".env")

from acts.catalog import get_default_catalog_path, load_catalog


def main() -> int:
    import psycopg

    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL required", file=sys.stderr)
        return 1
    catalog_path = get_default_catalog_path()
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    acts = {a["act_id"]: a for a in data["acts"]}
    catalog = load_catalog()

    with psycopg.connect(url) as conn:
        rows = conn.execute(
            'SELECT c.metadata->>\'act_id\' AS act_id, COUNT(*) '
            'FROM "legal_chunks" c JOIN "legal_documents" d ON d.id = c."documentId" '
            'WHERE c.metadata->>\'act_id\' IS NOT NULL GROUP BY 1'
        ).fetchall()
    ingested_ids = {row[0] for row in rows if row[0]}
    for act_id in ingested_ids:
        if act_id in acts:
            acts[act_id]["ingestion_status"] = "ingested"
            pdf = repo_root / "Law_files" / f"{act_id}.pdf"
            if pdf.is_file():
                acts[act_id]["source_file"] = f"Law_files/{pdf.name}"
    data["acts"] = list(acts.values())
    catalog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ingested_act_ids": sorted(ingested_ids)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
