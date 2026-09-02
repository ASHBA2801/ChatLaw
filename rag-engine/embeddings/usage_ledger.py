"""Embedding usage ledger for cost tracking during corpus expansion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_ledger_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "evaluation" / "embedding_usage.json"


def load_ledger(path: Path | None = None) -> dict[str, Any]:
    ledger_path = path or default_ledger_path()
    if ledger_path.is_file():
        return json.loads(ledger_path.read_text(encoding="utf-8"))
    return {
        "generation_calls": 0,
        "embedding_api_calls": 0,
        "new_chunks_embedded": 0,
        "existing_embeddings_reused": 0,
        "runs": [],
    }


def save_ledger(ledger: dict[str, Any], path: Path | None = None) -> Path:
    ledger_path = path or default_ledger_path()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    return ledger_path


def record_run(
    *,
    run_type: str,
    generation_calls: int = 0,
    embedding_api_calls: int = 0,
    new_chunks_embedded: int = 0,
    existing_embeddings_reused: int = 0,
    notes: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    ledger = load_ledger(path)
    ledger["generation_calls"] = int(ledger.get("generation_calls", 0)) + generation_calls
    ledger["embedding_api_calls"] = int(ledger.get("embedding_api_calls", 0)) + embedding_api_calls
    ledger["new_chunks_embedded"] = int(ledger.get("new_chunks_embedded", 0)) + new_chunks_embedded
    ledger["existing_embeddings_reused"] = int(
        ledger.get("existing_embeddings_reused", 0)
    ) + existing_embeddings_reused
    ledger.setdefault("runs", []).append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_type": run_type,
        "generation_calls": generation_calls,
        "embedding_api_calls": embedding_api_calls,
        "new_chunks_embedded": new_chunks_embedded,
        "existing_embeddings_reused": existing_embeddings_reused,
        "notes": notes,
    })
    save_ledger(ledger, path)
    return ledger
