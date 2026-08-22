"""Focused, non-destructive unit tests for RAG-05 retrieval."""

from embeddings.base import EmbeddingProvider, EmbeddingProviderInfo
from retrieval.vector_search import VectorSearcher


class MockProvider(EmbeddingProvider):
    @property
    def info(self):
        return EmbeddingProviderInfo("mock", "mock-model", 768, 32)

    def embed(self, text):
        assert text
        return [0.1] * 768


class MockCursor:
    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query, self.params = query, params

    def fetchall(self):
        return self.rows


class MockConnection:
    def __init__(self, rows):
        self.cursor_instance = MockCursor(rows)

    def cursor(self):
        return self.cursor_instance


def row(similarity=0.9):
    return {
        "chunk_id": "BNS2023_p12_Sec_20_idx0_pt1",
        "document_id": "doc-bns",
        "document_title": "Bharatiya Nyaya Sanhita, 2023",
        "content": "Exact legal source text.",
        "section_number": "20",
        "subsection": "(1)",
        "chapter": "III",
        "clause": "(a)",
        "page_number": 12,
        "chunk_index": 0,
        "similarity": similarity,
        "metadata": {"source_document_id": "BNS2023"},
    }


def test_search_preserves_metadata_and_uses_cosine_query():
    connection = MockConnection([row()])
    response = VectorSearcher(connection, MockProvider()).search("punishment for theft")
    result = response.results[0]
    assert result.section_number == "20"
    assert result.page_number == 12
    assert result.metadata["source_document_id"] == "BNS2023"
    assert "<=>" in connection.cursor_instance.query
    assert connection.cursor_instance.params[-1] == 40
    assert len(connection.cursor_instance.params[0].strip("[]").split(",")) == 768


def test_top_k_and_threshold_are_parameterized():
    connection = MockConnection([])
    response = VectorSearcher(connection, MockProvider()).search(
        "recipe for biryani", top_k=3, min_similarity=0.85
    )
    assert response.results == ()
    assert response.no_relevant_context is True
    assert connection.cursor_instance.params[-1] == 40
    assert connection.cursor_instance.params[2] == -1.0
