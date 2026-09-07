"""Isolated Gemini embedding adapter.

The SDK is imported only when a real provider is configured. This keeps dry-run
configuration validation and unit tests independent of the provider package.
"""

import math
import os
import time
from typing import List, Sequence

from .base import EmbeddingProvider, EmbeddingProviderInfo
from .validation import validate_embedding


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Gemini adapter using GEMINI_EMBEDDING_MODEL; model choice is never invented.

    Requests exactly 768 dimensions via output_dimensionality and normalizes
    the returned vector as required by the model for non-default dimensionality.
    """

    def __init__(self, info: EmbeddingProviderInfo):
        if info.provider != "gemini":
            raise ValueError(f"Gemini provider received provider={info.provider!r}")
        self._info = info
        self._api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embedding ingestion")
        configured_model = os.getenv("GEMINI_EMBEDDING_MODEL", "").strip()
        if not configured_model:
            raise ValueError(
                "GEMINI_EMBEDDING_MODEL is required; do not invent a Gemini model name"
            )
        if configured_model != info.model:
            raise ValueError(
                "EMBEDDING_MODEL must match GEMINI_EMBEDDING_MODEL for the Gemini provider"
            )
        try:
            timeout_seconds = float(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "60"))
        except ValueError as exc:
            raise ValueError("GEMINI_REQUEST_TIMEOUT_SECONDS must be a number") from exc
        if timeout_seconds <= 0:
            raise ValueError("GEMINI_REQUEST_TIMEOUT_SECONDS must be positive")
        self._timeout_seconds = timeout_seconds

        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Gemini provider requires the optional google-genai package; "
                "install it manually before real ingestion"
            ) from exc
        self._client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self._types = types

    @property
    def info(self) -> EmbeddingProviderInfo:
        return self._info

    def embed(self, text: str) -> List[float]:
        if not text:
            raise ValueError("Cannot embed empty text")
        started = time.perf_counter()
        print(f"[EMBED] Sending request (chars={len(text)})", flush=True)
        response = self._client.models.embed_content(
            model=self._info.model,
            contents=text,
            config={"output_dimensionality": self._info.dimension},
        )
        print(
            f"[EMBED] Response received ({time.perf_counter() - started:.2f}s)",
            flush=True,
        )
        raw = getattr(response, "embeddings", None)
        if raw is None:
            raw = [getattr(response, "embedding", None)]
        if not raw or raw[0] is None:
            raise RuntimeError("Gemini returned no embedding")
        vector = getattr(raw[0], "values", raw[0])

        # Normalize for non-default dimensionality as required by Gemini Embedding 001
        if self._info.dimension != 3072:
            vector = self._normalize(vector)

        validated = validate_embedding(
            vector,
            expected_dimension=self._info.dimension,
            provider=self._info.provider,
            model=self._info.model,
        )
        print(f"[EMBED] Dimension validated: {len(validated)}", flush=True)
        return validated

    @staticmethod
    def _normalize(vector: List[float]) -> List[float]:
        """L2-normalize the vector to unit length."""
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        # Keep provider behavior isolated. Sequential calls are conservative and
        # avoid assuming an SDK batch response shape across SDK versions.
        return [self.embed(text) for text in texts]
