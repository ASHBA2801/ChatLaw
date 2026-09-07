"""Strict embedding and chunk validation for database compatibility."""

import math
from typing import Any, Mapping, Sequence


class EmbeddingValidationError(ValueError):
    """Raised when an embedding cannot safely be stored in vector(768)."""


def validate_embedding(
    embedding: Sequence[float],
    *,
    expected_dimension: int,
    provider: str,
    model: str,
) -> list[float]:
    """Validate finiteness and exact dimension without reshaping values."""
    actual_dimension = len(embedding)
    if actual_dimension != expected_dimension:
        raise EmbeddingValidationError(
            f"Embedding dimension mismatch: expected {expected_dimension}, "
            f"actual {actual_dimension}; provider={provider!r}, model={model!r}. "
            "Vectors are never padded or truncated."
        )

    values: list[float] = []
    for index, value in enumerate(embedding):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise EmbeddingValidationError(
                f"Embedding value at index {index} is not numeric; "
                f"provider={provider!r}, model={model!r}."
            )
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise EmbeddingValidationError(
                f"Embedding value at index {index} is not finite; "
                f"provider={provider!r}, model={model!r}."
            )
        values.append(numeric_value)
    return values


def validate_chunk_record(chunk: Mapping[str, Any]) -> None:
    """Validate required source chunk fields before embedding."""
    for field in ("document_id", "chunk_id"):
        if not isinstance(chunk.get(field), str) or not chunk[field].strip():
            raise ValueError(f"Chunk is missing required {field}")
    if not isinstance(chunk.get("content"), str) or not chunk["content"].strip():
        raise ValueError(f"Chunk {chunk.get('chunk_id', '<unknown>')} has empty content")
    if not isinstance(chunk.get("chunk_hash"), str) or not chunk["chunk_hash"].strip():
        raise ValueError(f"Chunk {chunk['chunk_id']} is missing chunk_hash")
