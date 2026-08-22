"""Canonical retrieval-backed evidence and deterministic citation validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from retrieval.models import RetrievalResult


@dataclass(frozen=True)
class Evidence:
    """A citation-safe view of one database retrieval result."""

    citation_id: int
    chunk_id: str
    document_id: str
    document_title: str
    section_number: str | None
    subsection: str | None
    chapter: str | None
    clause: str | None
    page_number: int | None
    content: str
    source_name: str | None = None
    source_url: str | None = None
    source_type: str | None = None
    is_official: bool | None = None
    similarity: float | None = None
    rerank_score: float | None = None

    @property
    def id(self) -> int:
        return self.citation_id

    @property
    def document(self) -> str:
        return self.document_title

    @property
    def section(self) -> str | None:
        return self.section_number

    @property
    def page(self) -> int | None:
        return self.page_number

    @classmethod
    def from_result(cls, result: RetrievalResult, citation_id: int) -> "Evidence":
        return cls(citation_id, result.chunk_id, result.document_id, result.document_title,
                   result.section_number, result.subsection, result.chapter, result.clause,
                   result.page_number, result.content, result.source_name, result.source_url,
                   result.source_type, result.is_official, result.similarity, result.rerank_score)

    def citation_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "id": self.citation_id, "document": self.document_title,
            "section": self.section_number, "page": self.page_number,
            "chunk_id": self.chunk_id, "evidence": self.content,
        }
        if self.subsection is not None:
            value["subsection"] = self.subsection
        if self.chapter is not None:
            value["chapter"] = self.chapter
        if self.clause is not None:
            value["clause"] = self.clause
        source = {"name": self.source_name, "url": self.source_url,
                  "source_type": self.source_type, "is_official": self.is_official}
        source = {key: item for key, item in source.items() if item is not None}
        if source:
            value["source"] = source
        return value


@dataclass(frozen=True)
class CitationValidation:
    normalized_answer: str
    valid_ids: tuple[int, ...]
    invalid_ids: tuple[int, ...]


_CITATION_PATTERN = re.compile(r"\[\s*(?:SOURCE\s+)?(\d+)\s*\]", re.IGNORECASE)
_SECTION_CLAIM_PATTERN = re.compile(r"(?:section|sec\.?)[\s.]*([0-9]+[a-z]?)\b[^\[\n]{0,40}\[\s*(?:source\s+)?(\d+)\s*\]", re.IGNORECASE)


def validate_citations(answer: str, evidence: Iterable[Evidence]) -> CitationValidation:
    evidence_by_id = {item.citation_id: item for item in evidence}
    available = set(evidence_by_id)
    referenced = [int(value) for value in _CITATION_PATTERN.findall(answer)]
    valid = tuple(dict.fromkeys(value for value in referenced if value in available))
    invalid = tuple(dict.fromkeys(value for value in referenced if value not in available))
    # A valid source ID must not make an explicitly different section number
    # appear database-confirmed.  This conservative check only applies when a
    # section claim is directly associated with its citation marker.
    for section, citation in _SECTION_CLAIM_PATTERN.findall(answer):
        source = evidence_by_id.get(int(citation))
        if source is not None and re.sub(r"[^a-z0-9]", "", source.section_number or "").lower() != section.lower():
            valid = tuple(value for value in valid if value != int(citation))
            if int(citation) not in invalid:
                invalid += (int(citation),)
    normalized = _CITATION_PATTERN.sub(
        lambda match: f"[{match.group(1)}]" if int(match.group(1)) in valid else "",
        answer,
    )
    if invalid:
        normalized += "\n\nLimitation: The answer contained an invalid citation reference " \
                   + ", ".join(str(value) for value in invalid) + "."
    return CitationValidation(normalized, valid, invalid)