"""Pydantic request and response models for the public API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryOptions(BaseModel):
    top_k: int = Field(default=8, ge=1, le=20)
    min_similarity: float = Field(default=0.60, ge=0.0, le=1.0)


class SearchRequest(QueryOptions):
    query: str = Field(..., min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be empty")
        return value


class CaseContextExcerpt(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=128)
    file_name: str = Field(..., min_length=1, max_length=255)
    page: int = Field(..., ge=1, le=10000)
    text: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(QueryOptions):
    message: str = Field(..., min_length=1, max_length=12000)
    conversation_id: str | None = None
    language: str = "en"
    case_context: list[CaseContextExcerpt] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be empty")
        return value

    @field_validator("language")
    @classmethod
    def language_normalized(cls, value: str) -> str:
        from conversation.languages import normalize_language
        return normalize_language(value)


class ConversationMessage(BaseModel):
    id: str
    role: str
    content: str
    language: str
    metadata: dict[str, Any] | None = None
    created_at: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class CreateConversationRequest(BaseModel):
    case_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)


class CreateConversationResponse(BaseModel):
    id: str
    created_at: str
    updated_at: str
    case_id: str | None = None
    user_id: str | None = None


class ConversationResponse(ConversationSummary):
    messages: list[ConversationMessage]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]


class ConversationMessageRequest(QueryOptions):
    message: str = Field(..., min_length=1, max_length=12000)
    language: str = "en"
    case_context: list[CaseContextExcerpt] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be empty")
        return value

    @field_validator("language")
    @classmethod
    def language_normalized(cls, value: str) -> str:
        from conversation.languages import normalize_language
        return normalize_language(value)


class RetrievalTimings(BaseModel):
    top_k: int
    results_returned: int | None = None
    results_used: int | None = None
    embedding_latency_seconds: float | None = None
    database_latency_seconds: float | None = None


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    chunk_id: str
    document_id: str
    document_title: str
    section_number: str | None
    subsection: str | None
    chapter: str | None
    clause: str | None
    page_number: int | None
    chunk_index: int
    content: str
    similarity: float
    metadata: dict[str, Any]
    vector_score: float | None = None
    keyword_score: float | None = None
    section_score: float | None = None
    document_score: float | None = None
    rerank_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    no_relevant_context: bool
    retrieval: RetrievalTimings


class Citation(BaseModel):
    id: int
    document: str | None
    section: str | None
    page: int | None
    chunk_id: str
    subsection: str | None = None
    chapter: str | None = None
    clause: str | None = None
    evidence: str | None = None
    source: dict[str, Any] | None = None


class GenerationDetails(BaseModel):
    model: str | None
    latency_seconds: float


class InterviewState(BaseModel):
    domain: str | None = None
    round: int = 0
    max_rounds: int = 3
    slots: dict[str, str] = Field(default_factory=dict)
    asked: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    original_query: str | None = None


class DocumentDraftState(BaseModel):
    mode: str = "document_drafting"
    template_id: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)
    asked: list[str] = Field(default_factory=list)
    round: int = 0
    max_rounds: int = 8
    original_query: str | None = None
    unsupported: bool = False
    pending_field: str | None = None
    missing_optional: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    answer: str
    has_context: bool
    no_relevant_context: bool = False
    citations: list[Citation]
    retrieval: RetrievalTimings
    generation: GenerationDetails
    total_latency_seconds: float
    invalid_citations: list[int] = []
    response_kind: str = "answer"
    language: str = "en"
    interview: InterviewState | None = None
    document_draft: DocumentDraftState | None = None


class ConversationChatResponse(BaseModel):
    conversation_id: str
    user_message: ConversationMessage
    assistant_message: ConversationMessage
    answer: str
    has_context: bool
    citations: list[Citation]
    retrieval: RetrievalTimings
    generation: GenerationDetails
    total_latency_seconds: float
    invalid_citations: list[int] = []
    no_relevant_context: bool = False
    response_kind: str = "answer"
    language: str = "en"
    interview: InterviewState | None = None
    document_draft: DocumentDraftState | None = None


class DocumentGenerateRequest(QueryOptions):
    template_id: str = Field(..., min_length=1, max_length=64)
    values: dict[str, Any] = Field(default_factory=dict)
    use_model: bool = True
    section_ids: list[str] | None = None

    @field_validator("template_id")
    @classmethod
    def template_id_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("template_id must not be empty")
        return value


class DocumentSectionRegenerateRequest(QueryOptions):
    template_id: str = Field(..., min_length=1, max_length=64)
    values: dict[str, Any] = Field(default_factory=dict)
    section_id: str = Field(..., min_length=1, max_length=64)
    use_model: bool = True
    instruction: str | None = Field(default=None, max_length=4000)

    @field_validator("template_id", "section_id")
    @classmethod
    def not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value


class DocumentReviseRequest(QueryOptions):
    template_id: str = Field(..., min_length=1, max_length=64)
    values: dict[str, Any] = Field(default_factory=dict)
    sections: list[dict[str, Any]] = Field(default_factory=list)
    instruction: str = Field(..., min_length=1, max_length=4000)
    target_section_ids: list[str] | None = None
    use_model: bool = True

    @field_validator("template_id", "instruction")
    @classmethod
    def not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value


class DocumentSelectionEditRequest(BaseModel):
    selected_text: str = Field(..., min_length=1, max_length=20000)
    action: str = Field(..., min_length=1, max_length=64)
    surrounding_section: dict[str, Any] = Field(default_factory=dict)
    document_title: str = Field(default="Document", max_length=500)
    jurisdiction: str = Field(default="India", max_length=200)
    custom_instruction: str = Field(default="", max_length=4000)
    language: str = Field(default="en", max_length=16)
    use_model: bool = True

    @field_validator("selected_text", "action")
    @classmethod
    def not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value
