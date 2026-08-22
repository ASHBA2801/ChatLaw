"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  sendConversationMessage,
  type ConversationSummary,
  type StoredMessage,
  type ChatResponse,
  type Citation,
  RagApiError,
  isCaseDocumentCitation,
} from "@/lib/api/rag";
import {
  useAnswerPlayback,
  useSpeechInput,
  useVoiceChat,
  type ChatInputMode,
  type VoiceChatSendResult,
  chatLanguageToSpeechCode,
  isSpeechLocaleLikelySupported,
} from "@/lib/speech";
import VoiceInputControls from "@/components/chat/VoiceInputControls";
import VoiceChatPanel from "@/components/chat/VoiceChatPanel";
import { ClarificationCard, DocumentDraftCard, LegalAnswerCard } from "@/components/chat/LegalAnswerCard";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import { formatLanguageLabel } from "@/lib/i18n/languages";
import { defaultValues, getTemplate } from "@/lib/documents/templates";
import type { DocumentValues } from "@/lib/documents/types";

type Message =
  | StoredMessage
  | { id: string; role: "assistant"; content: string; response?: ChatResponse; error?: boolean };

const NO_CONTEXT_MESSAGE =
  "I couldn't find sufficiently relevant legal sources for this question.";
const MESSAGE_LIMIT = 12_000;
const SUGGESTED_QUESTIONS = [
  "My landlord is refusing to return my deposit.",
  "My employer terminated me without notice.",
  "Explain Section 303 of the Bharatiya Nyaya Sanhita.",
  "What remedies are available for a defective product?",
];
const LOADING_STATES = [
  "Understanding your situation...",
  "Researching legal sources...",
  "Preparing a plain-language answer...",
];

type CitationPanelState = {
  citation: ChatResponse["citations"][number];
};

function formatRelativeDate(value: string): string {
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return "Unknown activity";
  const diff = Date.now() - time;
  if (diff < 60_000) return "Just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  if (diff < 604_800_000) return `${Math.floor(diff / 86_400_000)}d ago`;
  return new Date(value).toLocaleDateString();
}

function composeCitationText(citation: Citation): string {
  if (isCaseDocumentCitation(citation)) {
    return ["Case Document", citation.document, citation.page !== null ? `Page ${citation.page}` : null]
      .filter(Boolean)
      .join(" | ");
  }
  return [
    citation.document,
    citation.section ? `Section ${citation.section}` : null,
    citation.subsection ? `Subsection ${citation.subsection}` : null,
    citation.clause ? `Clause ${citation.clause}` : null,
    citation.page !== null ? `Page ${citation.page}` : null,
  ]
    .filter(Boolean)
    .join(" | ");
}

function responseFromStoredMessage(message: Message): ChatResponse | undefined {
  if (
    message.role !== "assistant" ||
    !("metadata" in message) ||
    !message.metadata ||
    typeof message.metadata !== "object"
  ) {
    return undefined;
  }
  const metadata = message.metadata as Record<string, unknown>;
  const citations = Array.isArray(metadata.citations) ? metadata.citations : [];
  const kind =
    typeof metadata.kind === "string"
      ? metadata.kind
      : typeof metadata.response_kind === "string"
        ? metadata.response_kind
        : "answer";

  if (kind === "clarification" || kind === "document_clarification" || kind === "document_unsupported" || kind === "document_ready") {
    return {
      message: message.content,
      answer: message.content,
      has_context: false,
      no_relevant_context: false,
      citations: [],
      invalid_citations: [],
      retrieval: { top_k: 0, results_used: 0 },
      generation: { model: null, latency_seconds: 0 },
      total_latency_seconds: 0,
      response_kind: kind as ChatResponse["response_kind"],
      interview:
        metadata.interview && typeof metadata.interview === "object"
          ? (metadata.interview as ChatResponse["interview"])
          : null,
      document_draft:
        metadata.document_draft && typeof metadata.document_draft === "object"
          ? (metadata.document_draft as ChatResponse["document_draft"])
          : null,
    };
  }

  return {
    message: message.content,
    answer: message.content,
    has_context: metadata.has_context === true,
    no_relevant_context: metadata.has_context !== true,
    citations: citations as Citation[],
    invalid_citations: Array.isArray(metadata.invalid_citations)
      ? metadata.invalid_citations.filter((id): id is number => typeof id === "number")
      : [],
    retrieval: (
      metadata.retrieval && typeof metadata.retrieval === "object"
        ? metadata.retrieval
        : { top_k: 8, results_used: citations.length }
    ) as ChatResponse["retrieval"],
    generation: (
      metadata.generation && typeof metadata.generation === "object"
        ? metadata.generation
        : { model: null, latency_seconds: 0 }
    ) as ChatResponse["generation"],
    total_latency_seconds: 0,
    response_kind:
      kind === "no_context" || kind === "answer"
        ? kind
        : metadata.has_context === true
          ? "answer"
          : "no_context",
    interview:
      metadata.interview && typeof metadata.interview === "object"
        ? (metadata.interview as ChatResponse["interview"])
        : null,
  };
}

export default function ChatInterface({ caseId }: { caseId?: string }) {
  const router = useRouter();
  const { language, languageOption } = useLanguage();
  const speechLang = chatLanguageToSpeechCode(language);
  const voiceSupportedForLanguage = isSpeechLocaleLikelySupported(speechLang);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [loadingConversation, setLoadingConversation] = useState(true);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [sidebarSearch, setSidebarSearch] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [citationPanel, setCitationPanel] = useState<CitationPanelState | null>(null);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const [chatMode, setChatMode] = useState<ChatInputMode>("text");
  const [draftGenerating, setDraftGenerating] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const draftCreateRef = useRef(false);

  const filteredHistory = useMemo(
    () => history.filter((item) => item.title.toLowerCase().includes(sidebarSearch.toLowerCase().trim())),
    [history, sidebarSearch],
  );

  useEffect(() => {
    void (async () => {
      try {
        if (caseId) {
          const storedId = window.localStorage.getItem(`chatlaw-case-conversation:${caseId}`);
          setConversationId(storedId);
          setHistory([]);
          return;
        }
        const storedId = window.localStorage.getItem("chatlaw-active-conversation");
        const conversations = await listConversations();
        setHistory(conversations.conversations);
        const id =
          storedId && conversations.conversations.some((item) => item.id === storedId) ? storedId : null;
        if (id) {
          const conversation = await getConversation(id);
          setConversationId(id);
          setMessages(conversation.messages);
        } else {
          const created = await createConversation();
          window.localStorage.setItem("chatlaw-active-conversation", created.id);
          setConversationId(created.id);
        }
      } catch (requestError) {
        setError(requestError instanceof RagApiError ? requestError.message : "Unable to load conversation history.");
      } finally {
        setLoadingConversation(false);
      }
    })();
  }, [caseId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!isLoading) return;
    const interval = window.setInterval(() => {
      setLoadingStepIndex((current) => (current + 1) % LOADING_STATES.length);
    }, 1200);
    return () => window.clearInterval(interval);
  }, [isLoading]);

  const speech = useSpeechInput({
    value: input,
    onChange: setInput,
    limit: MESSAGE_LIMIT,
    language: speechLang,
    disabled: isLoading || loadingConversation || chatMode === "voice",
  });

  const sendChatMessage = useCallback(
    async (message: string): Promise<VoiceChatSendResult> => {
      const trimmed = message.trim();
      if (!trimmed || isLoading) {
        throw new Error("Enter a question before sending.");
      }
      if (!caseId && !conversationId) {
        throw new Error("Your conversation is still loading. Please try again.");
      }

      setError(null);
      setIsLoading(true);
      const userId = `${Date.now()}`;
      setMessages((current) => [
        ...current,
        {
          id: userId,
          role: "user",
          content: trimmed,
          language,
          metadata: null,
          created_at: new Date().toISOString(),
        },
      ]);

      try {
        let response: ChatResponse & {
          assistant_message?: { id: string };
          conversation_id?: string;
          no_relevant_context?: boolean;
        };
        if (caseId) {
          const result = await fetch(`/api/cases/${caseId}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: trimmed, conversationId, language }),
          });
          const payload = await result.json();
          if (!result.ok) throw new RagApiError(payload.error || "The question could not be answered.", result.status);
          if (typeof payload.conversation_id === "string") {
            setConversationId(payload.conversation_id);
            window.localStorage.setItem(`chatlaw-case-conversation:${caseId}`, payload.conversation_id);
          }
          response = payload;
        } else {
          response = await sendConversationMessage(conversationId!, {
            message: trimmed,
            language,
            top_k: 8,
            min_similarity: 0.6,
          });
        }
        const assistantText =
          response.response_kind === "clarification" ||
          response.response_kind === "document_clarification" ||
          response.response_kind === "document_ready" ||
          response.response_kind === "document_unsupported"
            ? response.answer
            : response.no_relevant_context
              ? NO_CONTEXT_MESSAGE
              : response.answer;
        setHistory((current) =>
          current.map((item) =>
            item.id === (response.conversation_id || conversationId)
              ? {
                  ...item,
                  title: item.title === "New conversation" ? trimmed.slice(0, 60) : item.title,
                  updated_at: new Date().toISOString(),
                }
              : item,
          ),
        );
        setMessages((current) => [
          ...current,
          {
            id: response.assistant_message?.id || `${userId}-a`,
            role: "assistant",
            content: assistantText,
            response,
          },
        ]);

        if (response.response_kind === "document_ready" && response.document_draft?.template_id && !caseId) {
          const templateId = response.document_draft.template_id;
          const draftValues = response.document_draft.values || {};
          if (!draftCreateRef.current) {
            draftCreateRef.current = true;
            setDraftGenerating(true);
            void (async () => {
              try {
                const template = getTemplate(templateId);
                const values: DocumentValues = {
                  ...defaultValues(template),
                  ...draftValues,
                  draft_language: language,
                };
                const createResponse = await fetch("/api/documents", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    templateId,
                    values,
                    conversationId: response.conversation_id || conversationId,
                  }),
                });
                const payload = await createResponse.json();
                if (!createResponse.ok) {
                  throw new Error(payload.error || "Could not generate the document draft.");
                }
                router.push(`/documents/${payload.id}`);
              } catch (draftError) {
                draftCreateRef.current = false;
                setDraftGenerating(false);
                setError(draftError instanceof Error ? draftError.message : "Document generation failed.");
              }
            })();
          }
        }

        return { userText: trimmed, assistantText, response };
      } catch (requestError) {
        const friendlyMessage =
          requestError instanceof RagApiError
            ? requestError.message
            : "Unable to connect to the legal research service. Please try again.";
        setError(friendlyMessage);
        setMessages((current) => [
          ...current,
          { id: `${userId}-error`, role: "assistant", content: friendlyMessage, error: true },
        ]);
        if (process.env.NODE_ENV === "development") console.error(requestError);
        throw new Error(friendlyMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [caseId, conversationId, isLoading, language, router],
  );

  const voiceChat = useVoiceChat({
    conversationId,
    allowWithoutConversation: Boolean(caseId),
    language: speechLang,
    disabled: loadingConversation || chatMode !== "voice",
    sendMessage: sendChatMessage,
  });

  const answerPlayback = useAnswerPlayback();

  async function startNewChat() {
    speech.cancel();
    voiceChat.reset();
    if (caseId) {
      window.localStorage.removeItem(`chatlaw-case-conversation:${caseId}`);
      setConversationId(null);
      setMessages([]);
      setError(null);
      setCitationPanel(null);
      setIsSidebarOpen(false);
      inputRef.current?.focus();
      return;
    }
    try {
      const created = await createConversation();
      window.localStorage.setItem("chatlaw-active-conversation", created.id);
      setConversationId(created.id);
      setMessages([]);
      setError(null);
      setCitationPanel(null);
      inputRef.current?.focus();
      setHistory((current) => [
        {
          id: created.id,
          title: "New conversation",
          created_at: created.created_at,
          updated_at: created.updated_at,
        },
        ...current,
      ]);
      setIsSidebarOpen(false);
    } catch (requestError) {
      setError(requestError instanceof RagApiError ? requestError.message : "Unable to create a new conversation.");
    }
  }

  async function openChat(id: string) {
    speech.cancel();
    voiceChat.reset();
    setLoadingConversation(true);
    try {
      const conversation = await getConversation(id);
      setConversationId(id);
      setMessages(conversation.messages);
      setCitationPanel(null);
      window.localStorage.setItem("chatlaw-active-conversation", id);
      setIsSidebarOpen(false);
    } catch (requestError) {
      setError(requestError instanceof RagApiError ? requestError.message : "Unable to load conversation.");
    } finally {
      setLoadingConversation(false);
    }
  }

  async function handleDeleteConversation(id: string) {
    const proceed = window.confirm("Delete this conversation? This cannot be undone.");
    if (!proceed) return;
    try {
      await deleteConversation(id);
      const nextHistory = history.filter((item) => item.id !== id);
      setHistory(nextHistory);
      if (conversationId === id) {
        await startNewChat();
      }
    } catch (requestError) {
      setError(requestError instanceof RagApiError ? requestError.message : "Unable to delete conversation.");
    }
  }

  async function submitMessage() {
    if (speech.isListening || voiceChat.state === "listening") return;
    const message = input.trim();
    if (!message || isLoading) return;
    setInput("");
    try {
      await sendChatMessage(message);
    } catch {
      /* handled in sendChatMessage */
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitMessage();
  }

  function handleInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading && !loadingConversation && !speech.isListening && input.trim()) {
        void submitMessage();
      }
    }
  }

  function openCitationPanel(citation: ChatResponse["citations"][number]) {
    setLoadingEvidence(true);
    setCitationPanel({ citation });
    setTimeout(() => setLoadingEvidence(false), 120);
  }

  const composerValue = speech.isListening ? speech.displayValue : input;
  const remainingChars = MESSAGE_LIMIT - composerValue.length;
  const conversationTitle =
    history.find((item) => item.id === conversationId)?.title ||
    (caseId ? "Case conversation" : "New conversation");

  return (
    <div className="flex w-full">
      <aside
        className={`${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-40 w-[86%] max-w-sm border-r border-[var(--line)] bg-white transition-transform duration-200 ease-out lg:static lg:inset-auto lg:z-0 lg:w-72 lg:max-w-none lg:translate-x-0 ${isSidebarCollapsed ? "lg:w-16" : ""}`}
        aria-label="Conversations"
      >
        <div className="flex h-full flex-col pt-16 lg:pt-0">
          <div className="border-b border-[var(--line)] p-3">
            <div className="flex items-center gap-2">
              {!isSidebarCollapsed && (
                <button
                  type="button"
                  onClick={() => void startNewChat()}
                  className="min-h-11 flex-1 rounded-lg bg-[var(--forest)] px-3 text-sm font-semibold text-white"
                >
                  + New conversation
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsSidebarCollapsed((v) => !v)}
                className="hidden min-h-11 min-w-11 rounded-lg border border-[var(--line)] text-sm lg:block"
                aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {isSidebarCollapsed ? "›" : "‹"}
              </button>
            </div>
            {!isSidebarCollapsed && (
              <label className="mt-3 block">
                <span className="sr-only">Search conversations</span>
                <input
                  value={sidebarSearch}
                  onChange={(event) => setSidebarSearch(event.target.value)}
                  placeholder="Search conversations"
                  className="h-11 w-full rounded-lg border border-[var(--line)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]"
                />
              </label>
            )}
          </div>
          {!isSidebarCollapsed && (
            <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
              {loadingConversation && history.length === 0 ? (
                <p className="px-2 py-3 text-sm text-[var(--ink-muted)]">Loading conversations...</p>
              ) : filteredHistory.length === 0 ? (
                <p className="px-2 py-3 text-sm text-[var(--ink-muted)]">
                  {caseId ? "Case chats stay on this matter." : "No matching conversations."}
                </p>
              ) : (
                filteredHistory.map((item) => (
                  <div
                    key={item.id}
                    className={`group mb-1 rounded-lg border ${item.id === conversationId ? "border-[var(--forest)] bg-[#eef5d0]" : "border-transparent hover:border-[var(--line)]"}`}
                  >
                    <button type="button" onClick={() => void openChat(item.id)} className="w-full p-3 text-left">
                      <p className="truncate text-sm font-medium">{item.title}</p>
                      <p className="mt-1 text-xs text-[var(--ink-muted)]">
                        Last activity {formatRelativeDate(item.updated_at)}
                      </p>
                    </button>
                    <div className="flex items-center justify-end px-3 pb-2">
                      <button
                        type="button"
                        onClick={() => void handleDeleteConversation(item.id)}
                        className="text-xs text-[#935a1e] underline-offset-2 hover:underline"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </aside>
      {isSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/25 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-label="Close conversations panel"
        />
      )}

      <section className="flex min-h-[calc(100dvh-8rem)] min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-2 border-b border-[var(--line)] px-4 py-2 sm:px-6">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(true)}
            className="min-h-11 min-w-11 rounded-lg border border-[var(--line)] text-sm lg:hidden"
            aria-label="Open conversations panel"
          >
            ☰
          </button>
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-sm font-semibold">{conversationTitle}</h2>
            <p className="truncate text-xs text-[var(--ink-muted)]">
              Answering in {formatLanguageLabel(languageOption)}
            </p>
          </div>
          <div className="flex rounded-lg border border-[var(--line)] p-0.5" role="group" aria-label="Input mode">
            <button
              type="button"
              onClick={() => {
                voiceChat.reset();
                answerPlayback.stop();
                setChatMode("text");
              }}
              className={`min-h-9 rounded-md px-3 text-xs font-medium ${chatMode === "text" ? "bg-[var(--forest)] text-white" : "text-[var(--ink-muted)]"}`}
              aria-pressed={chatMode === "text"}
            >
              Text
            </button>
            <button
              type="button"
              onClick={() => {
                speech.cancel();
                answerPlayback.stop();
                setChatMode("voice");
              }}
              className={`min-h-9 rounded-md px-3 text-xs font-medium ${chatMode === "voice" ? "bg-[var(--forest)] text-white" : "text-[var(--ink-muted)]"}`}
              aria-pressed={chatMode === "voice"}
            >
              Voice
            </button>
          </div>
        </div>

        {caseId ? (
          <p className="border-b border-[var(--line)] bg-[#eef5d0] px-4 py-2 text-sm text-[var(--forest)]">
            This conversation may use official legal sources and your authorized case documents. Uploaded files are not
            official law.
          </p>
        ) : null}

        <div ref={scrollRef} className="chat-scroll min-h-0 flex-1 overflow-y-auto px-3 py-4 sm:px-4 md:px-8 md:py-6">
          {chatMode === "voice" && (
            <div className="mb-6">
              {!voiceSupportedForLanguage ? (
                <p className="mb-3 rounded-xl border border-[var(--line)] bg-white px-4 py-3 text-sm text-[var(--ink-muted)]">
                  Voice may not be available for {formatLanguageLabel(languageOption)} in this browser. Text chat still
                  works in your selected language.
                </p>
              ) : null}
              <VoiceChatPanel
                state={voiceChat.state === "thinking" && isLoading ? "thinking" : voiceChat.state}
                stateLabel={voiceChat.state === "thinking" && isLoading ? "Researching…" : voiceChat.stateLabel}
                supported={voiceChat.supported}
                ttsSupported={voiceChat.ttsSupported}
                language={voiceChat.language}
                onLanguageChange={voiceChat.setLanguage}
                muted={voiceChat.muted}
                onMutedChange={voiceChat.setMuted}
                error={voiceChat.error}
                interimText={voiceChat.interimText}
                draftText={voiceChat.draftText}
                onDraftTextChange={voiceChat.setDraftText}
                lastUserText={voiceChat.lastUserText}
                lastAssistantText={voiceChat.lastAssistantText}
                disabled={loadingConversation || isLoading}
                onStartListening={voiceChat.startListening}
                onStopListening={voiceChat.stopListening}
                onCancelListening={voiceChat.cancelListening}
                onConfirmSend={voiceChat.confirmSend}
                onDiscardDraft={voiceChat.discardDraft}
                onStopSpeaking={voiceChat.stopSpeaking}
                onPauseSpeaking={voiceChat.pauseSpeaking}
                onResumeSpeaking={voiceChat.resumeSpeaking}
                onReplaySpeaking={voiceChat.replaySpeaking}
                onClearError={voiceChat.clearError}
                onSwitchToText={() => {
                  voiceChat.reset();
                  answerPlayback.stop();
                  setChatMode("text");
                }}
              />
            </div>
          )}

          {loadingConversation ? (
            <p className="mt-16 text-center text-sm text-[var(--ink-muted)]">Loading conversation...</p>
          ) : messages.length === 0 ? (
            <div className="mx-auto mt-8 max-w-xl text-center sm:mt-12">
              <h3 className="text-2xl font-semibold tracking-tight">Describe your situation</h3>
              <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
                ChatLaw may ask a few focused follow-ups, then explain the law in plain language with sources.
              </p>
              <div className="mt-6 grid gap-2 text-left">
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => setInput(question)}
                    className="min-h-11 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm hover:border-[var(--forest)]"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
              {messages.map((message, index) => {
                const response =
                  message.role === "assistant"
                    ? message.response || responseFromStoredMessage(message)
                    : undefined;
                const priorUserText =
                  [...messages.slice(0, index)].reverse().find((item) => item.role === "user")?.content || "";
                return (
                  <article
                    key={message.id}
                    className={
                      message.role === "user"
                        ? "ml-auto w-full max-w-[96%] rounded-2xl rounded-br-md bg-[var(--forest)] px-4 py-3 text-sm text-white sm:max-w-[80%]"
                        : `w-full rounded-2xl rounded-bl-md border px-4 py-4 text-[var(--foreground)] ${message.error ? "border-[#e3c59f] bg-[#fff5e7]" : "border-[var(--line)] bg-white"}`
                    }
                  >
                    {message.role === "user" ? (
                      <p className="whitespace-pre-wrap leading-6">{message.content}</p>
                    ) : message.error ? (
                      <p className="leading-6">{message.content}</p>
                    ) : response?.response_kind === "clarification" ? (
                      <ClarificationCard content={message.content} />
                    ) : response?.response_kind === "document_clarification" ||
                      response?.response_kind === "document_ready" ||
                      response?.response_kind === "document_unsupported" ? (
                      <DocumentDraftCard
                        content={message.content}
                        response={response}
                        generating={response.response_kind === "document_ready" && draftGenerating}
                      />
                    ) : response ? (
                      <LegalAnswerCard
                        messageId={message.id}
                        content={message.content}
                        response={response}
                        priorUserText={priorUserText}
                        onOpenCitation={openCitationPanel}
                        playback={answerPlayback}
                        chatMode={chatMode}
                        disabledPlayback={isLoading || speech.isListening}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap leading-6">{message.content}</p>
                    )}
                  </article>
                );
              })}
              {isLoading && (
                <div
                  className="w-full rounded-2xl rounded-bl-md border border-[var(--line)] bg-white px-4 py-4 text-sm text-[var(--ink-muted)]"
                  role="status"
                >
                  {LOADING_STATES[loadingStepIndex]}
                </div>
              )}
              {error && <p className="text-sm text-[#935a1e]">{error}</p>}
            </div>
          )}
        </div>

        {chatMode === "text" && (
          <div className="border-t border-[var(--line)] bg-[var(--background)] px-2 py-2 pb-4 sm:px-4 sm:py-3 md:px-8">
            <form onSubmit={handleSubmit} className="mx-auto w-full max-w-3xl rounded-2xl border border-[var(--line)] bg-white p-2">
              <div className="flex items-end gap-2">
                <label className="sr-only" htmlFor="chatlaw-message">
                  Message input
                </label>
                <textarea
                  id="chatlaw-message"
                  ref={inputRef}
                  value={composerValue}
                  onChange={(event) => setInput(event.target.value.slice(0, MESSAGE_LIMIT))}
                  onKeyDown={handleInputKeyDown}
                  rows={2}
                  disabled={isLoading || loadingConversation || speech.isListening}
                  placeholder="Describe your situation in your own words..."
                  className="max-h-48 min-h-11 w-full resize-y bg-transparent px-3 py-2 text-sm leading-6 outline-none placeholder:text-[var(--ink-muted)] disabled:cursor-not-allowed"
                />
                <button
                  type="button"
                  disabled
                  className="min-h-11 min-w-11 shrink-0 rounded-lg border border-[var(--line)] text-[var(--ink-muted)]"
                  aria-label="Document upload coming soon"
                  title="Document upload coming soon"
                >
                  <svg className="mx-auto h-5 w-5" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" />
                    <path d="M14 3v5h5" />
                  </svg>
                </button>
                <button
                  type="submit"
                  disabled={isLoading || loadingConversation || speech.isListening || !input.trim()}
                  className="min-h-11 shrink-0 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50"
                  aria-label="Send message"
                >
                  {isLoading ? "Sending..." : "Send"}
                </button>
              </div>
              <div className="mt-2 flex flex-col gap-2 px-1 sm:flex-row sm:items-start sm:justify-between">
                <VoiceInputControls
                  status={speech.status}
                  supported={speech.supported}
                  language={speech.language}
                  onLanguageChange={speech.setLanguage}
                  error={speech.error}
                  interimText={speech.interimText}
                  disabled={isLoading || loadingConversation}
                  onStart={speech.start}
                  onStop={speech.stop}
                  onCancel={speech.cancel}
                  onClearError={speech.clearError}
                />
                <div className="flex items-center justify-between gap-3 text-xs text-[var(--ink-muted)] sm:flex-col sm:items-end sm:justify-start">
                  <span>
                    Language: {languageOption.nativeName} · Enter to send
                  </span>
                  <span className={remainingChars < 200 ? "text-[#935a1e]" : ""}>{remainingChars}</span>
                </div>
              </div>
            </form>
          </div>
        )}
      </section>

      {citationPanel && (
        <aside className="fixed inset-0 z-50 flex justify-end bg-black/30" role="dialog" aria-modal="true" aria-label="Evidence panel">
          <button type="button" className="flex-1" onClick={() => setCitationPanel(null)} aria-label="Close evidence panel" />
          <div className="chat-scroll h-full w-full max-w-md overflow-y-auto border-l border-[var(--line)] bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-base font-semibold">Evidence</h3>
              <button
                type="button"
                onClick={() => setCitationPanel(null)}
                className="min-h-11 min-w-11 rounded-lg border border-[var(--line)] text-sm"
                aria-label="Close evidence panel"
              >
                ✕
              </button>
            </div>
            {loadingEvidence ? (
              <p className="mt-4 text-sm text-[var(--ink-muted)]">Loading evidence...</p>
            ) : (
              <div className="mt-4 space-y-3 text-sm">
                <p className="font-semibold">{citationPanel.citation.document || "Source unavailable"}</p>
                {isCaseDocumentCitation(citationPanel.citation) ? (
                  <p className="rounded-full bg-[#eef5d0] px-3 py-1 text-xs font-semibold text-[var(--forest)]">
                    Case document — not an official legal source
                  </p>
                ) : (
                  <p className="text-[var(--ink-muted)]">
                    {citationPanel.citation.section
                      ? `Section ${citationPanel.citation.section}`
                      : "Section unavailable"}
                    {citationPanel.citation.subsection
                      ? ` · Subsection ${citationPanel.citation.subsection}`
                      : ""}
                  </p>
                )}
                {citationPanel.citation.page !== null && (
                  <p className="text-[var(--ink-muted)]">Page {citationPanel.citation.page}</p>
                )}
                {citationPanel.citation.evidence && (
                  <div className="rounded-lg border border-[var(--line)] bg-[var(--background)] p-3">
                    <p className="whitespace-pre-wrap leading-6">{citationPanel.citation.evidence}</p>
                  </div>
                )}
                <div className="flex flex-wrap gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(composeCitationText(citationPanel.citation))}
                    className="min-h-11 rounded-lg border border-[var(--line)] px-3 text-sm"
                  >
                    Copy citation
                  </button>
                  {citationPanel.citation.source?.url && (
                    <a
                      className="inline-flex min-h-11 items-center rounded-lg border border-[var(--line)] px-3 text-sm text-[var(--forest)] underline"
                      href={citationPanel.citation.source.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      View source
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
