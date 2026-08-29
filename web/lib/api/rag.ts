export interface ChatRequest {
  message: string;
  language?: string;
  top_k?: number;
  min_similarity?: number;
  conversation_id?: string | null;
}

export type ResponseKind =
  | "clarification"
  | "answer"
  | "no_context"
  | "document_clarification"
  | "document_ready"
  | "document_unsupported";

export interface InterviewState {
  domain: string | null;
  round: number;
  max_rounds: number;
  slots: Record<string, string>;
  asked: string[];
  assumptions: string[];
  original_query?: string | null;
  pending?: boolean;
}

export interface DocumentDraftState {
  mode: string;
  template_id?: string | null;
  values?: Record<string, string | number | boolean | "">;
  asked?: string[];
  round?: number;
  max_rounds?: number;
  original_query?: string | null;
  unsupported?: boolean;
  pending_field?: string | null;
  missing_optional?: string[];
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  section_number: string | null;
  subsection: string | null;
  chapter: string | null;
  clause: string | null;
  page_number: number | null;
  chunk_index: number;
  content: string;
  similarity: number;
  metadata: Record<string, unknown>;
  vector_score?: number | null;
  keyword_score?: number | null;
  section_score?: number | null;
  document_score?: number | null;
  rerank_score?: number | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  no_relevant_context: boolean;
  retrieval: RetrievalTimings;
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  language: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  response?: ChatResponse;
  error?: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation extends ConversationSummary {
  messages: StoredMessage[];
}

export interface ConversationChatResponse extends ChatResponse {
  conversation_id: string;
  user_message: StoredMessage;
  assistant_message: StoredMessage;
}

export interface Citation {
  id: number;
  document: string | null;
  section: string | null;
  page: number | null;
  chunk_id: string;
  subsection?: string | null;
  chapter?: string | null;
  clause?: string | null;
  evidence?: string | null;
  source?: {
    name?: string | null;
    url?: string | null;
    source_type?: string | null;
    is_official?: boolean | null;
  } | null;
}

export function isCaseDocumentCitation(citation: Citation): boolean {
  return citation.source?.source_type === "case_document" || citation.source?.is_official === false;
}

export interface RetrievalTimings {
  top_k: number;
  results_returned?: number | null;
  results_used?: number | null;
  embedding_latency_seconds?: number | null;
  database_latency_seconds?: number | null;
}

export interface GenerationDetails {
  model: string | null;
  latency_seconds: number;
}

export interface ChatResponse {
  message: string;
  answer: string;
  has_context: boolean;
  no_relevant_context: boolean;
  citations: Citation[];
  invalid_citations: number[];
  retrieval: RetrievalTimings;
  generation: GenerationDetails;
  total_latency_seconds: number;
  response_kind?: ResponseKind;
  language?: string;
  interview?: InterviewState | null;
  document_draft?: DocumentDraftState | null;
}

const DEFAULT_API_URL = "/api/rag";
const REQUEST_TIMEOUT_MS = 90_000;

export class RagApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "RagApiError";
  }
}

function mapStatusMessage(status: number, fallback: string): string {
  if (status === 401 || status === 403) return "You are not authorized to use the legal research service.";
  if (status === 404) return "The requested conversation was not found.";
  if (status === 408) return "The legal research request timed out. Please try again.";
  if (status === 413) return "Your message is too large. Please shorten it and try again.";
  if (status === 422) return "The question could not be processed. Please revise it and try again.";
  if (status === 429) return "Too many requests in a short time. Please wait a moment and retry.";
  if (status >= 500) return "The legal research service is temporarily unavailable.";
  return fallback;
}

function getApiUrl(): string {
  // Keep browser traffic on the same-origin proxy. The backend URL and
  // service secret are server-only configuration.
  return DEFAULT_API_URL;
}

export async function askLegalQuestion(
  request: ChatRequest,
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${getApiUrl()}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new RagApiError(
        mapStatusMessage(response.status, "The legal research service could not process that question."),
        response.status,
      );
    }

    try {
      return (await response.json()) as ChatResponse;
    } catch {
      throw new RagApiError("The legal research service returned a malformed response.");
    }
  } catch (error) {
    if (error instanceof RagApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new RagApiError("The request took too long. Please try again.");
    }
    throw new RagApiError("Unable to connect to the legal research service.");
  } finally {
    clearTimeout(timeout);
  }
}

async function conversationRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${getApiUrl()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
      signal: controller.signal,
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => null) as { detail?: unknown } | null;
      const message = typeof detail?.detail === "string" ? detail.detail : null;
      throw new RagApiError(
        mapStatusMessage(response.status, message || "The legal research service could not complete the request."),
        response.status,
      );
    }
    try {
      return (await response.json()) as T;
    } catch {
      throw new RagApiError("The legal research service returned a malformed response.", response.status);
    }
  } catch (error) {
    if (error instanceof RagApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new RagApiError("The request took too long. Please try again.");
    }
    throw new RagApiError("Unable to connect to the legal research service. Make sure the RAG backend is running.");
  } finally {
    clearTimeout(timeout);
  }
}

export const createConversation = () => conversationRequest<{ id: string; created_at: string; updated_at: string }>("/api/conversations", { method: "POST" });
export const listConversations = () => conversationRequest<{ conversations: ConversationSummary[] }>("/api/conversations");
export const getConversation = (id: string) => conversationRequest<Conversation>(`/api/conversations/${encodeURIComponent(id)}`);
export const deleteConversation = (id: string) => conversationRequest<{ deleted: boolean }>(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
export const sendConversationMessage = (id: string, request: ChatRequest) => conversationRequest<ConversationChatResponse>(`/api/conversations/${encodeURIComponent(id)}/messages`, { method: "POST", body: JSON.stringify(request) });

export function searchLegalSources(request: {
  query: string;
  top_k?: number;
  min_similarity?: number;
}): Promise<SearchResponse> {
  return conversationRequest<SearchResponse>("/api/search", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
export async function checkRagHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${getApiUrl()}/health`, {
      signal: AbortSignal.timeout(10_000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
