"""Environment-driven embedding provider construction."""

import os
from typing import Optional

from .base import EmbeddingProvider, EmbeddingProviderInfo


class EmbeddingConfigurationError(ValueError):
    """Raised for incomplete or incompatible provider configuration."""


def _required_env(name: str, value: Optional[str] = None) -> str:
    resolved = value if value is not None else os.getenv(name)
    if not resolved or not resolved.strip():
        raise EmbeddingConfigurationError(f"Required embedding configuration {name} is not set")
    return resolved.strip()


def load_embedding_info() -> EmbeddingProviderInfo:
    """Load provider-neutral configuration without contacting an API."""
    provider = _required_env("EMBEDDING_PROVIDER").lower()
    model = _required_env("EMBEDDING_MODEL")
    try:
        dimension = int(_required_env("EMBEDDING_DIMENSION"))
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    except ValueError as exc:
        raise EmbeddingConfigurationError(
            "EMBEDDING_DIMENSION and EMBEDDING_BATCH_SIZE must be integers"
        ) from exc
    if dimension <= 0:
        raise EmbeddingConfigurationError("EMBEDDING_DIMENSION must be positive")
    if batch_size <= 0:
        raise EmbeddingConfigurationError("EMBEDDING_BATCH_SIZE must be positive")
    if provider == "gemini" and model != _required_env("GEMINI_EMBEDDING_MODEL"):
        raise EmbeddingConfigurationError("EMBEDDING_MODEL must match GEMINI_EMBEDDING_MODEL")
    if dimension != 768:
        raise EmbeddingConfigurationError("EMBEDDING_DIMENSION must be 768 for vector(768)")
    return EmbeddingProviderInfo(provider, model, dimension, batch_size)


def create_embedding_provider() -> EmbeddingProvider:
    """Construct the configured provider; no provider is silently guessed."""
    info = load_embedding_info()
    if info.provider == "gemini":
        from .gemini import GeminiEmbeddingProvider

        return GeminiEmbeddingProvider(info=info)
    raise EmbeddingConfigurationError(
        f"Unsupported EMBEDDING_PROVIDER={info.provider!r}. Supported providers: gemini"
    )
