"""Mocked, non-destructive tests for RAG-03 embedding ingestion."""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from embeddings.base import EmbeddingProvider, EmbeddingProviderInfo
from embeddings.ingestion import EmbeddingIngestor
from embeddings.validation import EmbeddingValidationError, validate_chunk_record, validate_embedding


class MockProvider(EmbeddingProvider):
    def __init__(self, dimension=768, vectors=None):
        self._info = EmbeddingProviderInfo("mock", "mock-model", dimension, 2)
        self.vectors = vectors
        self.calls = []

    @property
    def info(self):
        return self._info

    def embed(self, text):
        self.calls.append(text)
        return self.vectors or [0.0] * self.info.dimension

    def embed_batch(self, texts):
        self.calls.extend(texts)
        return [self.vectors or [0.0] * self.info.dimension for _ in texts]


def valid_chunk(**overrides):
    record = {
        "document_id": "BNS2023",
        "chunk_id": "BNS2023_p1_Sec_1_idx0_pt1",
        "chunk_hash": "abc123",
        "content": "Section 1 exact legal text.",
    }
    record.update(overrides)
    return record


def test_empty_content_rejected():
    with pytest.raises(ValueError, match="empty content"):
        validate_chunk_record(valid_chunk(content=""))


def test_required_ids_rejected():
    with pytest.raises(ValueError, match="chunk_id"):
        validate_chunk_record(valid_chunk(chunk_id=""))
    with pytest.raises(ValueError, match="document_id"):
        validate_chunk_record(valid_chunk(document_id=""))


def test_dimension_mismatch_rejected():
    with pytest.raises(EmbeddingValidationError, match="expected 768.*actual 3"):
        validate_embedding([1.0, 2.0, 3.0], expected_dimension=768, provider="mock", model="m")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_embedding_rejected(value):
    with pytest.raises(EmbeddingValidationError, match="not finite"):
        validate_embedding([value] + [0.0] * 767, expected_dimension=768, provider="mock", model="m")


def test_batch_generation_preserves_content_order():
    provider = MockProvider()
    ingestor = EmbeddingIngestor(provider, batch_size=2, sleep=lambda _: None)
    records = [valid_chunk(chunk_id=f"chunk-{i}") for i in range(3)]
    vectors = ingestor.embed_records(records)
    assert len(vectors) == 3
    assert provider.calls == [record["content"] for record in records]


def test_dimension_compatibility_rejected_at_ingestor_creation():
    with pytest.raises(ValueError, match="vector\(768\)"):
        EmbeddingIngestor(MockProvider(dimension=384))


def test_dry_run_plan_does_not_call_provider():
    provider = MockProvider()
    ingestor = EmbeddingIngestor(provider, batch_size=2)
    records = [valid_chunk(chunk_id=f"chunk-{i}") for i in range(3)]
    plan = ingestor.dry_run_plan(records)
    assert plan["chunks"] == 3
    assert plan["batches"] == 2
    assert provider.calls == []


def test_metadata_preservation_mapping():
    from database.upsert import ChunkUpserter

    info = EmbeddingProviderInfo("mock", "mock-model", 768, 2)
    record = valid_chunk(
        part="PART I", subclause="(i)", schedule="THE FIRST SCHEDULE",
        page_start=2, page_end=3, chunk_part=2, total_parts=3,
        is_continuation=True, parent_chunk_id="parent",
        context_path="Act > Section 1", context_prefix="Section 1",
        chunk_type="continuation",
    )
    metadata = ChunkUpserter.chunk_metadata(record, info)
    assert metadata["page_start"] == 2
    assert metadata["page_end"] == 3
    assert metadata["is_continuation"] is True
    assert metadata["embedding_dimension"] == 768


# --- Gemini provider specific tests ---

class MockGeminiResponse:
    """Mock response object matching google-genai embed_content return shape."""
    def __init__(self, values):
        self.embeddings = [MagicMock(values=values)]


def test_gemini_requests_768_dimensions():
    """Verify the Gemini provider passes output_dimensionality=768 to the SDK."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSION": "768",
    }):
        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.models.embed_content.return_value = MockGeminiResponse([0.1] * 768)

            from embeddings.gemini import GeminiEmbeddingProvider
            from embeddings.base import EmbeddingProviderInfo

            info = EmbeddingProviderInfo("gemini", "gemini-embedding-001", 768, 32)
            provider = GeminiEmbeddingProvider(info)
            provider.embed("test text")

            # Verify the SDK was called with output_dimensionality=768
            call_args = mock_client.models.embed_content.call_args
            assert call_args is not None
            config = call_args.kwargs.get("config")
            assert config is not None
            assert config["output_dimensionality"] == 768


def test_gemini_returns_exactly_768_values():
    """Verify the provider returns exactly 768 values when configured for 768."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSION": "768",
    }):
        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.models.embed_content.return_value = MockGeminiResponse([0.1] * 768)

            from embeddings.gemini import GeminiEmbeddingProvider
            from embeddings.base import EmbeddingProviderInfo

            info = EmbeddingProviderInfo("gemini", "gemini-embedding-001", 768, 32)
            provider = GeminiEmbeddingProvider(info)
            vector = provider.embed("test text")

            assert len(vector) == 768


def test_gemini_normalizes_768_dimensional_vectors():
    """Verify 768-dimensional vectors are L2-normalized (non-default dimensionality)."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSION": "768",
    }):
        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            # Return a non-normalized vector
            raw_vector = [3.0, 4.0] + [0.0] * 766  # norm = 5
            mock_client.models.embed_content.return_value = MockGeminiResponse(raw_vector)

            from embeddings.gemini import GeminiEmbeddingProvider
            from embeddings.base import EmbeddingProviderInfo

            info = EmbeddingProviderInfo("gemini", "gemini-embedding-001", 768, 32)
            provider = GeminiEmbeddingProvider(info)
            vector = provider.embed("test text")

            # Check L2 normalization: norm should be 1.0
            norm = math.sqrt(sum(v * v for v in vector))
            assert abs(norm - 1.0) < 1e-6


def test_gemini_rejects_3072_dimensional_response():
    """Verify 3072-dimensional responses are rejected when 768 is configured."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSION": "768",
    }):
        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.models.embed_content.return_value = MockGeminiResponse([0.1] * 3072)

            from embeddings.gemini import GeminiEmbeddingProvider
            from embeddings.base import EmbeddingProviderInfo
            from embeddings.validation import EmbeddingValidationError

            info = EmbeddingProviderInfo("gemini", "gemini-embedding-001", 768, 32)
            provider = GeminiEmbeddingProvider(info)

            with pytest.raises(EmbeddingValidationError, match="expected 768.*actual 3072"):
                provider.embed("test text")


def test_gemini_non_finite_values_rejected():
    """Verify non-finite values in embeddings are rejected."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSION": "768",
    }):
        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            # Include NaN in the response
            raw_vector = [math.nan] + [0.1] * 767
            mock_client.models.embed_content.return_value = MockGeminiResponse(raw_vector)

            from embeddings.gemini import GeminiEmbeddingProvider
            from embeddings.base import EmbeddingProviderInfo
            from embeddings.validation import EmbeddingValidationError

            info = EmbeddingProviderInfo("gemini", "gemini-embedding-001", 768, 32)
            provider = GeminiEmbeddingProvider(info)

            with pytest.raises(EmbeddingValidationError, match="not finite"):
                provider.embed("test text")


def test_database_ingestion_requires_768_dimensions():
    """Verify the ingestion pipeline rejects non-768 embeddings at the database layer."""
    from embeddings.ingestion import EmbeddingIngestor
    from embeddings.base import EmbeddingProviderInfo

    # Provider that returns 3072 dimensions
    class BadDimensionProvider(EmbeddingProvider):
        def __init__(self):
            self._info = EmbeddingProviderInfo("bad", "bad-model", 3072, 32)

        @property
        def info(self):
            return self._info

        def embed(self, text):
            return [0.1] * 3072

    with pytest.raises(ValueError, match="vector\(768\)"):
        EmbeddingIngestor(BadDimensionProvider())
