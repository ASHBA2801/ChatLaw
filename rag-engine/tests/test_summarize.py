from fastapi.testclient import TestClient

from api.main import app
from generation.gemini import GenerationResult

AUTH = {"Authorization": "Bearer test-secret"}


class FakeGenerator:
    def generate_text(self, prompt, *, temperature=0.0):
        assert "CASE DOCUMENT TEXT" in prompt
        assert "Security deposit" in prompt
        return GenerationResult("AI-generated summary of deposit terms.", "mock-model", 0.01)


def test_summarize_endpoint_uses_mocked_gemini(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    monkeypatch.setattr("generation.gemini.GeminiGenerator", FakeGenerator)
    from api import main
    main._rate_limit.clear()
    with TestClient(app) as client:
        response = client.post(
            "/api/summarize/document",
            json={"file_name": "Rental Agreement.pdf", "text": "Security deposit of 50000."},
            headers=AUTH,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "AI-generated summary"
    assert "deposit" in body["summary"].lower()


def test_summarize_requires_auth(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post("/api/summarize/document", json={"text": "hello"})
    assert response.status_code == 401


def test_summarize_rejects_empty_text(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post("/api/summarize/document", json={"text": "   "}, headers=AUTH)
    assert response.status_code == 422
