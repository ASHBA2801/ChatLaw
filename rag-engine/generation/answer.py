"""Grounded answer orchestration and retrieval-backed citation rendering."""

from dataclasses import dataclass
from typing import Callable

from context.builder import BuiltContext, build_context
from retrieval.models import RetrievalResponse
from verification.evidence import Evidence, validate_citations

NO_CONTEXT_MESSAGE = (
    "Sorry, I couldn't find the right law for this in what I have with me. "
    "Could you tell me a little more about what happened, in your own words?"
)

_NO_CONTEXT_LOCALIZED = {
    "en": NO_CONTEXT_MESSAGE,
    "hi": "माफ़ कीजिए, मेरे पास जो कानून हैं उनमें मुझे इसका सही जवाब नहीं मिला। क्या आप अपने शब्दों में थोड़ा और बता सकते हैं कि क्या हुआ?",
    "ta": "மன்னிக்கவும், என்னிடம் உள்ள சட்டங்களில் இதற்கான சரியான பதில் கிடைக்கவில்லை. என்ன நடந்தது என்று உங்கள் வார்த்தைகளில் கொஞ்சம் கூடுதலாகச் சொல்ல முடியுமா?",
}


def no_context_message(language: str = "en") -> str:
    code = (language or "en").strip().lower().split("-", 1)[0]
    return _NO_CONTEXT_LOCALIZED.get(code, NO_CONTEXT_MESSAGE)


@dataclass(frozen=True)
class AnswerResponse:
    question: str
    answer: str
    has_context: bool
    citations: tuple[dict[str, object], ...]
    retrieval: dict[str, int]
    generation: dict[str, object]
    invalid_citations: tuple[int, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "answer": self.answer,
            "has_context": self.has_context,
            "citations": list(self.citations),
            "retrieval": self.retrieval,
            "generation": self.generation,
            "no_relevant_context": not self.has_context,
            "invalid_citations": list(self.invalid_citations),
        }


def render_citation(source: Evidence) -> str:
    if source.source_type == "case_document":
        page = f" — Page {source.page_number}" if source.page_number is not None else ""
        return f"[{source.citation_id}] Case Document — {source.document_title}{page}"
    location = f" — Section {source.section_number}" if source.section_number else ""
    if source.page_number is not None:
        location += f" — Page {source.page_number}"
    if source.subsection:
        location += f" — Subsection {source.subsection}"
    return f"[{source.citation_id}] {source.document_title}{location}"


def answer_question(
    question: str,
    retrieval: RetrievalResponse,
    generator: Callable[[str, str], object] | None,
    *,
    top_k: int,
    language: str = "en",
) -> AnswerResponse:
    if retrieval.no_relevant_context:
        return AnswerResponse(
            question,
            no_context_message(language),
            False,
            (),
            {"top_k": top_k, "results_used": 0},
            {"model": None, "latency_seconds": 0.0},
        )
    built: BuiltContext = build_context(retrieval.results)
    if generator is None:
        raise ValueError("generator is required when legal context is available")
    generated = generator(question, built.text)
    answer = getattr(generated, "answer", None)
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("grounded generator returned a malformed or empty response")
    validation = validate_citations(answer, built.sources)
    used = tuple(source for source in built.sources if source.citation_id in validation.valid_ids)
    rendered = validation.normalized_answer
    for source in used:
        rendered = rendered.replace(f"[{source.citation_id}]", render_citation(source))
    return AnswerResponse(
        question,
        rendered,
        True,
        tuple(source.citation_dict() for source in used),
        {"top_k": top_k, "results_used": len(used)},
        {"model": generated.model, "latency_seconds": generated.latency_seconds},
        validation.invalid_ids,
    )
