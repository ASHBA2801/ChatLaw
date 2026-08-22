import pymupdf
from fastapi.testclient import TestClient

from api.main import app
from extraction.pdf import extract_pdf_bytes

AUTH = {"Authorization": "Bearer test-secret"}


def _pdf_bytes(text: str = "Security deposit of 50000") -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_extract_pdf_bytes_preserves_pages():
    result = extract_pdf_bytes(_pdf_bytes())
    assert result["page_count"] == 1
    assert result["pages"][0]["page"] == 1
    assert "Security deposit" in result["pages"][0]["text"]


def test_extract_rejects_non_pdf():
    try:
        extract_pdf_bytes(b"not a pdf")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_extract_endpoint(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    from api import main
    main._rate_limit.clear()
    with TestClient(app) as client:
        response = client.post(
            "/api/extract/pdf",
            content=_pdf_bytes(),
            headers={**AUTH, "Content-Type": "application/pdf"},
        )
    assert response.status_code == 200
    assert response.json()["pages"][0]["page"] == 1


def test_extract_requires_auth(monkeypatch):
    monkeypatch.setenv("RAG_API_SECRET", "test-secret")
    with TestClient(app) as client:
        response = client.post("/api/extract/pdf", content=_pdf_bytes())
    assert response.status_code == 401
