"""Semantic retrieval for legal chunks."""

from .models import RetrievalResult, RetrievalResponse
from .vector_search import VectorSearcher

__all__ = ["RetrievalResult", "RetrievalResponse", "VectorSearcher"]
