from types import SimpleNamespace

from context.builder import build_context
from context.case_documents import attach_case_context
from generation.answer import answer_question, render_citation
from retrieval.models import RetrievalResponse, RetrievalResult
from verification.evidence import Evidence, validate_citations


def legal_result():
    return RetrievalResult(
        "chunk-1", "doc-1", "Bharatiya Nyaya Sanhita, 2023",
        "The punishment for theft is provided here.", "303", None, "XVII", None,
        78, 0, 0.88, {}, source_type="statute", is_official=True,
    )


def test_case_documents_are_labeled_separately_from_legal_sources():
    retrieval = attach_case_context(
        RetrievalResponse((legal_result(),), False),
        [{"document_id": "case-doc-1", "file_name": "Rental Agreement.pdf", "page": 4,
          "text": "The security deposit shall be refunded."}],
    )
    built = build_context(retrieval.results)
    assert "Kind: LEGAL SOURCE" in built.text
    assert "Kind: CASE DOCUMENT" in built.text
    assert "not an official legal source" in built.text
    case_source = next(source for source in built.sources if source.source_type == "case_document")
    assert "Case Document — Rental Agreement.pdf — Page 4" in render_citation(case_source)
    assert case_source.is_official is False


def test_case_context_alone_is_enough_to_generate():
    retrieval = attach_case_context(
        RetrievalResponse((), True),
        [{"document_id": "case-doc-1", "file_name": "Notice.pdf", "page": 1, "text": "Notice received on 20 Aug."}],
    )
    assert retrieval.no_relevant_context is False
    generated = SimpleNamespace(answer="The notice is dated 20 Aug [SOURCE 1].", model="mock", latency_seconds=0.01)
    response = answer_question("When was notice received?", retrieval, lambda *_: generated, top_k=8)
    assert response.has_context is True
    assert "Case Document — Notice.pdf — Page 1" in response.answer
    assert response.citations[0]["source"]["source_type"] == "case_document"


def test_invalid_case_citation_is_rejected():
    evidence = [
        Evidence(1, "case:doc:p1:1", "doc", "Rental Agreement.pdf", None, None, None, None, 4,
                 "deposit terms", source_type="case_document", is_official=False),
    ]
    result = validate_citations("See [1] and also [99].", evidence)
    assert result.valid_ids == (1,)
    assert result.invalid_ids == (99,)
    assert "[99]" not in result.normalized_answer


def test_duplicate_case_pages_get_one_id():
    excerpt = {"document_id": "doc", "file_name": "A.pdf", "page": 1, "text": "same text"}
    retrieval = attach_case_context(RetrievalResponse((), True), [excerpt, excerpt])
    built = build_context(retrieval.results)
    assert [source.citation_id for source in built.sources] == [1]
