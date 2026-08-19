#!/usr/bin/env python3
"""Validate RAG-03 embedding configuration without API or database access."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

load_dotenv(rag_engine_dir / ".env")

from embeddings.provider import EmbeddingConfigurationError, load_embedding_info


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EmbeddingConfigurationError(f"Required configuration {name} is not set")
    return value


def validate_configuration() -> dict[str, object]:
    """Validate all configuration required before real embedding ingestion."""
    info = load_embedding_info()
    if info.provider != "gemini":
        raise EmbeddingConfigurationError(
            f"Unsupported EMBEDDING_PROVIDER={info.provider!r}; supported providers: gemini"
        )
    api_key = _require("GEMINI_API_KEY")
    gemini_model = _require("GEMINI_EMBEDDING_MODEL")
    if gemini_model != info.model:
        raise EmbeddingConfigurationError(
            "EMBEDDING_MODEL must exactly match GEMINI_EMBEDDING_MODEL"
        )
    if info.dimension != 768:
        raise EmbeddingConfigurationError(
            f"Database compatibility failure: expected dimension 768 for vector(768), "
            f"got {info.dimension}; provider={info.provider}, model={info.model}"
        )

    database_url = _require("DATABASE_URL")
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"} or not parsed.hostname:
        raise EmbeddingConfigurationError(
            "DATABASE_URL must be a valid PostgreSQL URL"
        )

    return {
        "provider": info.provider,
        "model": info.model,
        "dimension": info.dimension,
        "batch_size": info.batch_size,
        "database_host": parsed.hostname,
        "database_port": parsed.port or 5432,
        "api_key_configured": bool(api_key),
        "api_base_url": "SDK default Gemini endpoint",
        "retry_attempts_after_initial": 3,
        "retry_backoff_seconds": [1, 2, 4],
    }


def main() -> int:
    try:
        result = validate_configuration()
    except (EmbeddingConfigurationError, ValueError) as exc:
        print(f"CONFIGURATION INVALID: {exc}", file=sys.stderr)
        return 1

    print("RAG-03 embedding configuration is valid.")
    for key, value in result.items():
        print(f"{key}: {value}")
    print("No API request was made. No database connection was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())