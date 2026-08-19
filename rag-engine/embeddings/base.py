"""Provider-neutral embedding interfaces for RAG-03."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class EmbeddingProviderInfo:
    """Resolved provider configuration and its declared output contract."""

    provider: str
    model: str
    dimension: int
    batch_size: int


class EmbeddingProvider(ABC):
    """Interface implemented by concrete embedding providers."""

    @property
    @abstractmethod
    def info(self) -> EmbeddingProviderInfo:
        """Return provider metadata."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed one exact input string."""

    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed texts in provider-sized batches."""
        return [self.embed(text) for text in texts]
