"""Focused API tests using mocked RAG dependencies."""

from fastapi.testclient import TestClient
import pytest

from api.main import app
from api.routes.search import get_service
from generation.answer import NO_CONTEXT_MESSAGE
from retrieval.models import RetrievalResponse, RetrievalResult

AUTH = {"Authorization": "Bearer test-secret"}


@pytest.fixture(autouse=True)
def api_test_environment(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    from api import main
    main._rate_limit.clear()


class FakeService:
    def __init__(self, results=()):
        self.results = tuple(results)
        self.generator_called = False

    def close(self):
        pass

    def search(self, query, top_k, min_similarity):
        return RetrievalResponse(self.results, not self.results,
                                 embedding_latency_seconds=0.01,
                                 database_latency_seconds=0.02)

    def chat(self, message, top_k, min_similarity, history="", case_context=None, *, language="en",
             retrieval_query=None):
        from generation.answer import answer_question
        from context.case_documents import attach_case_context
        query_for_search = (retrieval_query or message).strip() or message
        retrieval = attach_case_context(self.search(query_for_search, top_k, min_similarity), case_context)
        if retrieval.no_relevant_context:
            return retrieval, answer_question(message, retrieval, None, top_k=top_k, language=language)

        def generator(question, context):
            self.generator_called = True
            from generation.gemini import GenerationResult
            return GenerationResult("The punishment is stated in [SOURCE 1].", "test-model", 0.03)

        return retrieval, answer_question(message, retrieval, generator, top_k=top_k, language=language)


def fake_result():
    return RetrievalResult("chunk-1", "doc-1", "THE BHARATIYA NYAYA SANHITA, 2023",
                            "The punishment for theft is provided here.", "303", None,
                            "XVII", None, 78, 123, 0.88, {})


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "chatlaw-rag-engine"
    assert body["health"] == "/health"


def test_search_returns_structured_result():
    service = FakeService([fake_result()])
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/search", json={"query": "punishment for theft"}, headers=AUTH)
        assert response.status_code == 200
        assert response.json()["results"][0]["section_number"] == "303"
    finally:
        app.dependency_overrides.clear()


def test_chat_uses_citations():
    service = FakeService([fake_result()])
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={"message": "What is the punishment for theft under BNS section 303?"},
                headers=AUTH,
            )
        assert response.status_code == 200
        assert response.json()["citations"][0]["section"] == "303"
        assert response.json()["response_kind"] == "answer"
        assert service.generator_called
    finally:
        app.dependency_overrides.clear()


def test_chat_uses_case_context_when_legal_retrieval_is_empty():
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={
                "message": "What does my agreement say about the deposit? just answer",
                "case_context": [{
                    "document_id": "doc-1",
                    "file_name": "Rental Agreement.pdf",
                    "page": 4,
                    "text": "The security deposit shall be refunded.",
                }],
            }, headers=AUTH)
        assert response.status_code == 200
        assert response.json()["has_context"] is True
        assert service.generator_called
        assert response.json()["citations"][0]["source"]["source_type"] == "case_document"
    finally:
        app.dependency_overrides.clear()


def test_chat_does_not_generate_without_context():
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "recipe for biryani"}, headers=AUTH)
        assert response.status_code == 200
        assert response.json()["has_context"] is False
        assert response.json()["citations"] == []
        assert response.json()["answer"] == NO_CONTEXT_MESSAGE
        assert not service.generator_called
    finally:
        app.dependency_overrides.clear()


def test_empty_message_is_rejected():
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "   "}, headers=AUTH)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_api_requires_authentication(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_api_rejects_invalid_authentication(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "hello"}, headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_api_accepts_valid_authentication(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "hello"}, headers=AUTH)
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_oversized_message_is_rejected():
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "x" * 12001}, headers=AUTH)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    monkeypatch.setattr("api.main.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("api.main.RATE_LIMIT_WINDOW_SECONDS", 60)
    service = FakeService()
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.post("/api/chat", json={"message": "one"}, headers=AUTH).status_code == 200
            assert client.post("/api/chat", json={"message": "two"}, headers=AUTH).status_code == 429
    finally:
        app.dependency_overrides.clear()