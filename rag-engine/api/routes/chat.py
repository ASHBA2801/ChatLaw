import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from api.models import (
    ChatRequest,
    ChatResponse,
    Citation,
    DocumentDraftState,
    GenerationDetails,
    InterviewState,
    RetrievalTimings,
)
from api.service import RagService
from conversation.document_drafting import drafting_state_from_metadata, process_document_turn
from conversation.interview import InterviewManager, active_interview_from_metadata
from conversation.languages import normalize_language
from .search import get_service

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)
_interview = InterviewManager()


def _empty_retrieval(top_k: int) -> RetrievalTimings:
    return RetrievalTimings(top_k=top_k, results_used=0, embedding_latency_seconds=0.0,
                            database_latency_seconds=0.0)


def _interview_payload(state: dict) -> InterviewState:
    return InterviewState.model_validate(state)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: RagService = Depends(get_service)) -> ChatResponse:
    started = time.perf_counter()
    from conversation.language_detector import detect_language
    from conversation.speech_cleaner import clean_speech_text

    prior_lang = None
    raw_lang = normalize_language(request.language, allow_auto=True)
    try:
        prior = None
        draft_prior = None
        if request.conversation_id:
            from api.conversation_service import ConversationStore
            store = ConversationStore(service.connection)
            if store.exists(request.conversation_id):
                meta = store.last_assistant_metadata(request.conversation_id)
                prior = active_interview_from_metadata(meta)
                draft_prior = drafting_state_from_metadata(meta)
                for m in reversed(store.recent_messages(request.conversation_id)):
                    if m.get("language") and m["language"] not in ("auto", "en"):
                        prior_lang = m["language"]
                        break
                    if m.get("language") and not prior_lang:
                        prior_lang = m["language"]

        det = detect_language(request.message, input_type="text", prior_language=prior_lang)
        if det["directive_applied"]:
            language = det["detected_language"]
        elif raw_lang != "auto" and raw_lang != "en":
            language = raw_lang
        else:
            language = det["detected_language"]

        draft = process_document_turn(request.message, draft_prior, language=language)
        if draft.action in {"clarify", "ready", "unsupported"}:
            kind = {
                "clarify": "document_clarification",
                "ready": "document_ready",
                "unsupported": "document_unsupported",
            }[draft.action]
            speech = clean_speech_text(draft.message)
            return ChatResponse(
                message=request.message,
                answer=draft.message,
                display_text=draft.message,
                speech_text=speech,
                has_context=False,
                no_relevant_context=False,
                citations=[],
                retrieval=_empty_retrieval(request.top_k),
                generation=GenerationDetails(model=None, latency_seconds=0.0),
                total_latency_seconds=time.perf_counter() - started,
                invalid_citations=[],
                response_kind=kind,
                language=language,
                detected_language=language,
                document_draft=DocumentDraftState.model_validate(draft.state),
            )

        result = _interview.process_turn(request.message, language, prior)
        if result.action == "clarify":
            ans_text = result.question or ""
            speech = clean_speech_text(ans_text)
            return ChatResponse(
                message=request.message,
                answer=ans_text,
                display_text=ans_text,
                speech_text=speech,
                has_context=False,
                no_relevant_context=False,
                citations=[],
                retrieval=_empty_retrieval(request.top_k),
                generation=GenerationDetails(model=None, latency_seconds=0.0),
                total_latency_seconds=time.perf_counter() - started,
                invalid_citations=[],
                response_kind="clarification",
                language=language,
                detected_language=language,
                interview=_interview_payload(result.state),
            )

        generation_message = result.assembled_situation or request.message
        retrieval_query = str(result.state.get("original_query") or request.message).strip()
        logger.info("[CHAT] Query received; retrieving context")
        retrieval, answer = service.chat(
            generation_message,
            request.top_k,
            request.min_similarity,
            case_context=request.case_context,
            language=language,
            retrieval_query=retrieval_query,
        )
        response_kind = "answer" if answer.has_context else "no_context"
        speech = clean_speech_text(answer.answer)
        return ChatResponse(
            message=request.message,
            answer=answer.answer,
            display_text=answer.answer,
            speech_text=speech,
            has_context=answer.has_context,
            citations=[Citation.model_validate(citation) for citation in answer.citations],
            retrieval=RetrievalTimings(
                top_k=request.top_k,
                results_used=answer.retrieval["results_used"],
                embedding_latency_seconds=retrieval.embedding_latency_seconds,
                database_latency_seconds=retrieval.database_latency_seconds,
            ),
            generation=GenerationDetails.model_validate(answer.generation),
            total_latency_seconds=time.perf_counter() - started,
            no_relevant_context=not answer.has_context,
            invalid_citations=list(answer.invalid_citations),
            response_kind=response_kind,
            language=language,
            detected_language=language,
            interview=_interview_payload(result.state),
        )
    except (ValueError, RuntimeError) as exc:
        logger.exception("[CHAT] dependency or configuration failure")
        raise HTTPException(status_code=503, detail="Chat service is unavailable") from exc
    except Exception as exc:
        logger.exception("[CHAT] request failed")
        raise HTTPException(status_code=500, detail="Chat request failed") from exc
    finally:
        service.close()
        logger.info("[CHAT] Complete (%.2fs)", time.perf_counter() - started)
