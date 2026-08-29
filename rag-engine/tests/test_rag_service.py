"""Unit tests for RagService orchestration."""

from unittest.mock import MagicMock

from api.service import RagService
from retrieval.models import RetrievalResponse


def test_chat_uses_retrieval_query_for_search():
    searches: list[str] = []

    class RecordingSearcher:
        def search(self, query, *, top_k, min_similarity):
            searches.append(query)
            return RetrievalResponse((), True, embedding_latency_seconds=0.0, database_latency_seconds=0.0)

    connection = MagicMock()
    provider = MagicMock()
    provider.info.dimension = 768
    service = RagService(connection, provider)
    service.searcher = RecordingSearcher()

    service.chat(
        "My landlord is refusing to return my deposit. Domain: landlord_tenant. Known facts: party role: tenant.",
        top_k=8,
        min_similarity=0.6,
        retrieval_query="My landlord is refusing to return my deposit.",
    )

    assert searches == ["My landlord is refusing to return my deposit."]
