from types import SimpleNamespace

from context.builder import build_context
from generation.answer import NO_CONTEXT_MESSAGE, answer_question
from retrieval.models import RetrievalResponse, RetrievalResult


def result(section="303", page=87, content="The punishment is imprisonment."):
    return RetrievalResult("chunk-1", "doc-1", "Bharatiya Nyaya Sanhita, 2023", content,
                           section, "(1)", "Chapter XVII", "(a)", page, 0, .6683,
                           {"source_document_id": "BNS2023"})


def test_context_preserves_text_and_metadata():
    built = build_context([result()])
    assert "The punishment is imprisonment." in built.text
    assert "Section: 303" in built.text
    assert "Similarity: 0.6683" in built.text
    assert built.sources[0].citation_dict()["chunk_id"] == "chunk-1"


def test_no_context_does_not_call_generator():
    called = False
    def generator(*args):
        nonlocal called
        called = True
    response = answer_question("recipe for biryani", RetrievalResponse((), True), generator, top_k=8)
    assert response.answer == NO_CONTEXT_MESSAGE
    assert called is False
    assert response.has_context is False


def test_citations_are_retrieval_metadata_only():
    generated = SimpleNamespace(answer="The provision states imprisonment [SOURCE 1].", model="gemini-test", latency_seconds=.12)
    response = answer_question("punishment?", RetrievalResponse((result(),), False),
                               lambda question, context: generated, top_k=8)
    assert "Bharatiya Nyaya Sanhita, 2023 — Section 303 — Page 87" in response.answer
    assert response.citations[0]["chunk_id"] == "chunk-1"
    assert "[SOURCE" not in response.answer


def test_invalid_citation_is_flagged_and_not_created():
    generated = SimpleNamespace(answer="Section 999 [99].", model="gemini-test", latency_seconds=.01)
    response = answer_question("punishment?", RetrievalResponse((result(),), False),
                               lambda question, context: generated, top_k=8)
    assert response.invalid_citations == (99,)
    assert response.citations == ()
    assert "[99]" not in response.answer


def test_duplicate_evidence_gets_one_deterministic_id():
    duplicate = result(content="The punishment is imprisonment.")
    built = build_context([result(), duplicate])
    assert [source.citation_id for source in built.sources] == [1]


def test_hierarchy_and_evidence_are_exposed():
    citation = build_context([result()]).sources[0].citation_dict()
    assert citation["subsection"] == "(1)"
    assert citation["chapter"] == "Chapter XVII"
    assert citation["evidence"] == "The punishment is imprisonment."
