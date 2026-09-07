"""End-to-end and retrieval unit tests for scenario queries."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from context.builder import build_context
from embeddings.base import EmbeddingProvider, EmbeddingProviderInfo
from generation.answer import answer_question, no_context_message
from retrieval.models import RetrievalResponse, RetrievalResult
from retrieval.vector_search import VectorSearcher
from scenario.analyzer import analyze_scenario
from scenario.expansion import expand_query


class MockScenarioEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.call_count = 0
        self.embedded_texts = []

    @property
    def info(self):
        return EmbeddingProviderInfo("mock", "mock-model", 768, 32)

    def embed(self, text: str):
        self.call_count += 1
        self.embedded_texts.append(text)
        # Produce a non-zero deterministic vector
        val = 0.05
        return [val] * 768


class MockDbCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed_queries = []
        self.params_list = []

    def execute(self, query, params):
        self.executed_queries.append(query)
        self.params_list.append(params)

    def fetchall(self):
        return self.rows


class MockDbConnection:
    def __init__(self, rows):
        self.cursor_obj = MockDbCursor(rows)

    def cursor(self):
        return self.cursor_obj


def make_chunk_row(
    chunk_id="CPA2019_p5_Sec_2_idx0_pt1",
    document_title="The Consumer Protection Act, 2019",
    content="Defect in goods means any fault, imperfection or shortcoming in the quality, quantity, potency, purity or standard.",
    section_number="2",
    similarity=0.75,
    doc_id="doc-cpa",
):
    return {
        "chunk_id": chunk_id,
        "document_id": doc_id,
        "document_title": document_title,
        "content": content,
        "section_number": section_number,
        "subsection": "(10)",
        "chapter": "I",
        "clause": None,
        "page_number": 5,
        "chunk_index": 0,
        "similarity": similarity,
        "metadata": {"source_document_id": "CPA2019"},
        "source_name": "Consumer Protection Act 2019",
        "source_url": "https://consumeraffairs.nic.in",
        "source_type": "statute",
        "is_official": True,
    }


def test_ecommerce_defective_product_scenario_retrieves_and_ranks():
    query = "I bought a product on an e-commerce website. The product was defective when I received it, and the seller refused to accept a return or provide a refund."
    
    rows = [
        make_chunk_row(
            chunk_id="cpa_defect",
            document_title="The Consumer Protection Act, 2019",
            content="A consumer may file a complaint against a trader or service provider for defect in goods, deficiency in service, or refusal to refund.",
            section_number="35",
            similarity=0.72,
        ),
        make_chunk_row(
            chunk_id="bns_theft",
            document_title="Bharatiya Nyaya Sanhita, 2023",
            content="Whoever commits theft shall be punished with imprisonment.",
            section_number="303",
            similarity=0.40,
        ),
    ]
    
    provider = MockScenarioEmbeddingProvider()
    connection = MockDbConnection(rows)
    searcher = VectorSearcher(connection, provider)
    
    response = searcher.search(query, top_k=5)
    
    assert response.no_relevant_context is False
    assert len(response.results) > 0
    top_res = response.results[0]
    assert top_res.chunk_id == "cpa_defect"
    assert "Consumer" in top_res.document_title


def test_scenario_grounded_answer_generation():
    query = "I bought a product in an e-commerce website. The product was defective when I received it and they refused for returns or refunds."
    
    result_chunk = RetrievalResult(
        chunk_id="cpa_defect",
        document_id="doc-cpa",
        document_title="The Consumer Protection Act, 2019",
        content="Under the Consumer Protection Act, a consumer who receives defective goods is entitled to replacement, repair, or refund from the trader or e-commerce platform.",
        section_number="35",
        subsection=None,
        chapter="IV",
        clause=None,
        page_number=18,
        chunk_index=0,
        similarity=0.78,
        metadata={"source_document_id": "CPA2019"},
    )
    
    retrieval = RetrievalResponse(results=(result_chunk,), no_relevant_context=False)
    
    generated_text = (
        "### What your situation appears to involve\n"
        "Your situation involves a consumer purchase where goods were defective and the seller refused return/refund.\n\n"
        "### Relevant law\n"
        "Under Section 35 of the Consumer Protection Act [SOURCE 1], a consumer is entitled to seek remedies for defective goods.\n\n"
        "### What you may be able to do\n"
        "You may file a grievance or complaint seeking refund or replacement [SOURCE 1].\n\n"
        "### What you should keep\n"
        "- Invoice and order receipt\n"
        "- Proof of defective item\n"
        "- Communication refusing refund\n\n"
        "### Important\n"
        "Ensure notice is served to the seller before filing a complaint."
    )
    
    mock_gen = SimpleNamespace(answer=generated_text, model="gemini-2.5-flash", latency_seconds=0.35)
    
    response = answer_question(query, retrieval, lambda q, ctx: mock_gen, top_k=5)
    
    assert response.has_context is True
    assert "Consumer Protection Act" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0]["chunk_id"] == "cpa_defect"


def test_irrelevant_query_returns_no_context():
    query = "What is the capital of France?"
    provider = MockScenarioEmbeddingProvider()
    # Mock returns no high-similarity legal rows
    connection = MockDbConnection([])
    searcher = VectorSearcher(connection, provider)
    
    response = searcher.search(query, top_k=5, min_similarity=0.70)
    assert response.no_relevant_context is True
    assert len(response.results) == 0
    
    # Grounded answer gives localized no-context message
    ans = answer_question(query, response, None, top_k=5)
    assert ans.has_context is False
    assert ans.answer == no_context_message("en")


def test_embedding_caching_prevents_duplicate_calls():
    provider = MockScenarioEmbeddingProvider()
    connection = MockDbConnection([])
    searcher = VectorSearcher(connection, provider)
    
    query = "What is the punishment for theft?"
    searcher.search(query, top_k=3)
    initial_count = provider.call_count
    
    # Second search with same query should hit cache
    searcher.search(query, top_k=3)
    assert provider.call_count == initial_count
