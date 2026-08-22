import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request

from api.conversation_service import ConversationStore
from api.models import (
    ConversationChatResponse,
    ConversationListResponse,
    ConversationMessageRequest,
    ConversationResponse,
    CreateConversationResponse,
    Citation,
    ConversationMessage,
    DocumentDraftState,
    GenerationDetails,
    InterviewState,
    RetrievalTimings,
)
from api.routes.search import get_service
from conversation.document_drafting import drafting_state_from_metadata, process_document_turn
from conversation.interview import InterviewManager, interview_state_from_metadata
from conversation.languages import normalize_language
from retrieval.vector_search import connect_from_environment

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)
_interview = InterviewManager()


def get_store() -> ConversationStore:
    return ConversationStore(connect_from_environment())


def _empty_retrieval(top_k: int) -> RetrievalTimings:
    return RetrievalTimings(
        top_k=top_k,
        results_used=0,
        embedding_latency_seconds=0.0,
        database_latency_seconds=0.0,
    )


def _document_draft_response(
    *,
    conversation_id: str,
    user_message: dict,
    assistant_message: dict,
    answer: str,
    response_kind: str,
    draft_state: dict,
    language: str,
    started: float,
    top_k: int,
) -> ConversationChatResponse:
    return ConversationChatResponse(
        conversation_id=conversation_id,
        user_message=ConversationMessage.model_validate(user_message),
        assistant_message=ConversationMessage.model_validate(assistant_message),
        answer=answer,
        has_context=False,
        citations=[],
        retrieval=_empty_retrieval(top_k),
        generation=GenerationDetails(model=None, latency_seconds=0.0),
        total_latency_seconds=time.perf_counter() - started,
        no_relevant_context=False,
        invalid_citations=[],
        response_kind=response_kind,
        language=language,
        document_draft=DocumentDraftState.model_validate(draft_state),
    )


@router.post("", response_model=CreateConversationResponse, status_code=201)
async def create_conversation(http_request: Request, store: ConversationStore = Depends(get_store)):
    case_id = None
    user_id = None
    try:
        payload = await http_request.json()
        if isinstance(payload, dict):
            if isinstance(payload.get("case_id"), str):
                case_id = payload["case_id"].strip() or None
            if isinstance(payload.get("user_id"), str):
                user_id = payload["user_id"].strip() or None
    except Exception:
        case_id = None
        user_id = None
    try:
        return store.create(case_id, user_id)
    finally:
        store.connection.close()


@router.get("", response_model=ConversationListResponse)
def list_conversations(store: ConversationStore = Depends(get_store)):
    try:
        return {"conversations": store.list()}
    finally:
        store.connection.close()


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, store: ConversationStore = Depends(get_store)):
    try:
        conversation = store.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    finally:
        store.connection.close()


@router.post("/{conversation_id}/messages", response_model=ConversationChatResponse)
def send_message(conversation_id: str, request: ConversationMessageRequest):
    started = time.perf_counter()
    service = get_service()
    store = ConversationStore(service.connection)
    language = normalize_language(request.language)
    try:
        if not store.exists(conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")

        last_meta = store.last_assistant_metadata(conversation_id)
        draft_prior = drafting_state_from_metadata(last_meta)
        draft = process_document_turn(request.message, draft_prior)

        user_message = store.add_message(
            conversation_id, "user", request.message, language=language,
        )

        if draft.action in {"clarify", "ready", "unsupported"}:
            kind = {
                "clarify": "document_clarification",
                "ready": "document_ready",
                "unsupported": "document_unsupported",
            }[draft.action]
            metadata = {
                "kind": kind,
                "document_draft": draft.state,
                "template_id": draft.state.get("template_id"),
            }
            assistant_message = store.add_message(
                conversation_id,
                "assistant",
                draft.message,
                metadata,
                language=language,
            )
            return _document_draft_response(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
                answer=draft.message,
                response_kind=kind,
                draft_state=draft.state,
                language=language,
                started=started,
                top_k=request.top_k,
            )

        prior = interview_state_from_metadata(last_meta)
        result = _interview.process_turn(request.message, language, prior)

        if result.action == "clarify":
            metadata = {
                "kind": "clarification",
                "interview": result.state,
                "domain": result.state.get("domain"),
                "round": result.state.get("round"),
                "max_rounds": result.state.get("max_rounds"),
                "slots": result.state.get("slots"),
                "asked": result.state.get("asked"),
                "assumptions": result.state.get("assumptions"),
                "original_query": result.state.get("original_query"),
            }
            assistant_message = store.add_message(
                conversation_id,
                "assistant",
                result.question or "",
                metadata,
                language=language,
            )
            return ConversationChatResponse(
                conversation_id=conversation_id,
                user_message=ConversationMessage.model_validate(user_message),
                assistant_message=ConversationMessage.model_validate(assistant_message),
                answer=result.question or "",
                has_context=False,
                citations=[],
                retrieval=_empty_retrieval(request.top_k),
                generation=GenerationDetails(model=None, latency_seconds=0.0),
                total_latency_seconds=time.perf_counter() - started,
                no_relevant_context=False,
                invalid_citations=[],
                response_kind="clarification",
                language=language,
                interview=InterviewState.model_validate(result.state),
            )

        history = "\n".join(
            f"{item['role'].upper()}: {item['content']}"
            for item in store.recent_messages(conversation_id)[:-1]
        )
        retrieval, answer = service.chat(
            result.assembled_situation or request.message,
            request.top_k,
            request.min_similarity,
            history,
            case_context=request.case_context,
            language=language,
        )
        response_kind = "answer" if answer.has_context else "no_context"
        metadata = {
            "kind": response_kind,
            "has_context": answer.has_context,
            "citations": list(answer.citations),
            "retrieval": answer.retrieval,
            "generation": answer.generation,
            "invalid_citations": list(answer.invalid_citations),
            "interview": result.state,
        }
        assistant_message = store.add_message(
            conversation_id, "assistant", answer.answer, metadata, language=language,
        )
        return ConversationChatResponse(
            conversation_id=conversation_id,
            user_message=ConversationMessage.model_validate(user_message),
            assistant_message=ConversationMessage.model_validate(assistant_message),
            answer=answer.answer,
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
            interview=InterviewState.model_validate(result.state),
        )
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        logger.exception("[CHAT] conversation dependency failure")
        raise HTTPException(status_code=503, detail="Chat service is unavailable") from exc
    except Exception as exc:
        logger.exception("[CHAT] conversation request failed")
        raise HTTPException(status_code=500, detail="Chat request failed") from exc
    finally:
        service.close()


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, store: ConversationStore = Depends(get_store)):
    try:
        if not store.delete(conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"deleted": True}
    finally:
        store.connection.close()
