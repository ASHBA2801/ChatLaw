from retrieval.models import RetrievalResult
from retrieval.reranker import (
    RerankWeights,
    document_score,
    extract_query_signals,
    keyword_score,
    normalize_document_alias,
    rerank,
    section_score,
)


def result(section="303", document="BNS2023", content="The punishment for theft is imprisonment.", chunk="1"):
    return RetrievalResult(chunk, "doc", document, content, section, "(2)", None, None, None, 0, 0.60, {"source_document_id": document})


def test_extracts_section_and_subsection():
    signals = extract_query_signals("under Sec. 303(2) of BNS")
    assert signals.sections == (("303", "(2)"),)
    assert "BNS2023" in signals.documents


def test_document_aliases_are_normalized():
    assert normalize_document_alias("Bharatiya Nyaya Sanhita, 2023") == "BNS2023"
    assert normalize_document_alias("Bharatiya Nagarik Suraksha Sanhita") == "BNSS2023"


def test_keyword_and_metadata_scores():
    signals = extract_query_signals("What is the punishment for theft under BNS?")
    candidate = result()
    assert keyword_score(signals.keywords, candidate.content) > 0
    assert section_score(signals, candidate) == 0
    assert document_score(signals, candidate) == 1


def test_explicit_section_reranks_above_semantic_neighbor():
    ranked = rerank([result("304", content="Snatching is theft."), result("303")], "What is section 303 theft?", RerankWeights())
    assert ranked[0].section_number == "303"
    assert ranked[0].rerank_score is not None


def test_deduplicates_identical_content():
    ranked = rerank([result(chunk="1"), result(chunk="2")], "punishment for theft")
    assert len(ranked) == 1
