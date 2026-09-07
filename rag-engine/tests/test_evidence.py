from verification.evidence import Evidence, validate_citations


def test_citation_validation_preserves_order_and_rejects_unknown_ids():
    evidence = [Evidence(1, "chunk", "doc", "Act", "303", None, None, None, 78, "text")]
    result = validate_citations("[1] then [99] then [1]", evidence)
    assert result.valid_ids == (1,)
    assert result.invalid_ids == (99,)
    assert "[99]" not in result.normalized_answer


def test_missing_metadata_is_not_invented():
    evidence = Evidence(1, "chunk", "doc", "Act", None, None, None, None, None, "text")
    citation = evidence.citation_dict()
    assert citation["section"] is None
    assert citation["page"] is None
    assert "source" not in citation