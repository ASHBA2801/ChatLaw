"""Embedding generation orchestration and safe ingestion workflow."""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .base import EmbeddingProvider
from .validation import validate_chunk_record, validate_embedding


class EmbeddingIngestor:
    """Loads JSONL chunks, embeds in batches, and delegates database writes."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        *,
        expected_dimension: int = 768,
        batch_size: int = 32,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.provider = provider
        self.expected_dimension = expected_dimension
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.sleep = sleep
        if provider.info.dimension != expected_dimension:
            raise ValueError(
                f"Database compatibility failure: vector(768) requires expected dimension 768, "
                f"but configured provider dimension is {provider.info.dimension} "
                f"(provider={provider.info.provider!r}, model={provider.info.model!r})"
            )

    @staticmethod
    def load_chunks(input_dir: Path, document: str | None = None) -> list[dict[str, Any]]:
        files = sorted(input_dir.glob("*.jsonl"))
        if document:
            files = [path for path in files if path.stem.lower() == document.lower()]
        records: list[dict[str, Any]] = []
        for path in files:
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
                    record["_source_file"] = path.name
                    validate_chunk_record(record)
                    records.append(record)
        return records

    def _embed_batch_with_retry(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            print(
                f"[EMBED] Starting batch attempt {attempt + 1}/{self.max_retries + 1} "
                f"(size={len(texts)})",
                flush=True,
            )
            try:
                vectors = self.provider.embed_batch(texts)
                if len(vectors) != len(texts):
                    raise ValueError(
                        f"Embedding provider returned {len(vectors)} vectors for {len(texts)} texts"
                    )
                return [
                    validate_embedding(
                        vector,
                        expected_dimension=self.expected_dimension,
                        provider=self.provider.info.provider,
                        model=self.provider.info.model,
                    )
                    for vector in vectors
                ]
            except Exception as exc:
                last_error = exc
                print(f"[EMBED] Batch failed: {exc}", flush=True)
                if attempt >= self.max_retries:
                    break
                delay = 2**attempt
                print(f"[EMBED] Retrying in {delay}s", flush=True)
                self.sleep(delay)
        raise RuntimeError(f"Embedding batch failed after retries: {last_error}") from last_error

    def generate_embeddings(self, records: list[dict[str, Any]]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(records), self.batch_size):
            batch = records[start:start + self.batch_size]
            vectors.extend(self._embed_batch_with_retry([record["content"] for record in batch]))
        return vectors

    def embed_records(self, records: list[dict[str, Any]]) -> list[list[float]]:
        """Generate vectors for records, preserving exact input content order."""
        return self.generate_embeddings(records)

    def dry_run_plan(self, records: list[dict[str, Any]]) -> dict[str, int]:
        """Validate source records and report planned work without API or DB writes."""
        for record in records:
            validate_chunk_record(record)
        return {
            "documents": len({record["document_id"] for record in records}),
            "chunks": len(records),
            "batches": (len(records) + self.batch_size - 1) // self.batch_size,
            "expected_dimension": self.expected_dimension,
        }
