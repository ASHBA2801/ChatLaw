"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  sendConversationMessage,
  type ConversationSummary,
  type ChatResponse,
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
import ChatMessageList, { type ChatMessage } from "@/components/chat/ChatMessageList";
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon, MenuIcon } from "@/components/chat/ChatIcons";
import { composeCitationText, formatRelativeDate, formatCitationEvidence, groupConversationsByDate, runConversationBoot, type CitationPanelState } from "@/components/chat/chatUtils";
import LanguageSelector from "@/components/layout/LanguageSelector";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import { formatLanguageLabel } from "@/lib/i18n/languages";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

const VoiceChatPanel = dynamic(() => import("@/components/chat/VoiceChatPanel"), { ssr: false });

type Message = ChatMessage;

const SUGGESTED_QUESTIONS = [
  "Explain Section 303 of the Bharatiya Nyaya Sanhita.",
  "What is the punishment for theft?",
  "When can police arrest without a warrant under BNSS?",
  "What is a document under the Bharatiya Sakshya Adhiniyam?",
];
const MESSAGE_LIMIT = 12_000;
const LOADING_STATES = [
  "Understanding your situation...",
  "Researching legal sources...",
  "Preparing a plain-language answer...",
];

export default function ChatInterface({ caseId }: { caseId?: string }) {
  const router = useRouter();
  const { language, languageOption } = useLanguage();
  const speechLang = useMemo(() => chatLanguageToSpeechCode(language), [language]);
  const voiceSupportedForLanguage = useMemo(() => isSpeechLocaleLikelySupported(speechLang), [speechLang]);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [loadingConversation, setLoadingConversation] = useState(true);
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
  const isLoadingRef = useRef(false);
  const messageCountRef = useRef(0);

  const loadingStepLabel = LOADING_STATES[loadingStepIndex] ?? LOADING_STATES[0];

  const interviewStep = useMemo(() => {
    if (isLoading) return { current: loadingStepIndex + 1, total: LOADING_STATES.length, label: loadingStepLabel };
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      if (message.role !== "assistant") continue;
      const response = "response" in message ? message.response : undefined;
      if (response?.response_kind === "clarification") {
        return { current: 2, total: 3, label: "Clarifying your situation" };
      }
      if (response?.citations?.length) {
        return { current: 3, total: 3, label: "Answer grounded in statute" };
      }
    }
    return messages.length === 0 ? { current: 1, total: 3, label: "Describe your situation" } : null;
  }, [isLoading, loadingStepIndex, loadingStepLabel, messages]);

  const filteredHistory = useMemo(
    () => history.filter((item) => item.title.toLowerCase().includes(sidebarSearch.toLowerCase().trim())),
    [history, sidebarSearch],
  );

  const groupedHistory = useMemo(() => groupConversationsByDate(filteredHistory), [filteredHistory]);

  useEffect(() => {
    isLoadingRef.current = isLoading;
  }, [isLoading]);

  useEffect(() => {
    let cancelled = false;
    const bootKey = caseId ?? "__default__";
    queueMicrotask(() => {
      if (!cancelled) setLoadingConversation(true);
    });

    void runConversationBoot(bootKey, async () => {
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
    })
      .catch((requestError: unknown) => {
        setError(requestError instanceof RagApiError ? requestError.message : "Unable to load conversation history.");
      })
      .finally(() => {
        if (!cancelled) setLoadingConversation(false);
      });

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const count = messages.length;
    const isInitialLoad = count > 0 && messageCountRef.current === 0;
    const appended = count > messageCountRef.current;
    messageCountRef.current = count;
    el.scrollTo({
      top: el.scrollHeight,
      behavior: isInitialLoad ? "auto" : appended || isLoading ? "smooth" : "auto",
    });
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
      if (!trimmed || isLoadingRef.current) {
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
        const assistantText = response.answer;
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
                const { defaultValues, getTemplate } = await import("@/lib/documents/templates");
                const template = getTemplate(templateId);
                const values = {
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
    [caseId, conversationId, language, router],
  );

  const voiceChat = useVoiceChat({
    conversationId,
    allowWithoutConversation: Boolean(caseId),
    language: speechLang,
    disabled: loadingConversation || isLoading || chatMode !== "voice",
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

  const handleOpenCitation = useCallback((citation: ChatResponse["citations"][number]) => {
    setCitationPanel({ citation });
  }, []);

  const applySuggestedQuestion = useCallback(
    (question: string) => {
      if (chatMode === "voice") {
        voiceChat.reset();
        answerPlayback.stop();
        setChatMode("text");
      }
      setInput(question);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    },
    [answerPlayback, chatMode, voiceChat],
  );

  const handleAskAnother = useCallback(() => {
    if (chatMode === "voice") {
      voiceChat.reset();
      answerPlayback.stop();
      setChatMode("text");
    }
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }, [answerPlayback, chatMode, voiceChat]);

  const composerValue = speech.isListening ? speech.displayValue : input;
  const remainingChars = MESSAGE_LIMIT - composerValue.length;
  const conversationTitle =
    history.find((item) => item.id === conversationId)?.title ||
    (caseId ? "Case conversation" : "New conversation");

  const citationEvidenceParagraphs = useMemo(
    () => (citationPanel?.citation.evidence ? formatCitationEvidence(citationPanel.citation.evidence) : []),
    [citationPanel],
  );

  useEffect(() => {
    if (!citationPanel) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setCitationPanel(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [citationPanel]);

  return (
    <div
      className={`grid h-full min-h-0 w-full overflow-hidden ${
        isSidebarCollapsed ? "lg:grid-cols-1" : "lg:grid-cols-[minmax(220px,280px)_minmax(0,1fr)]"
      }`}
    >
      <aside
        className={`${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-40 w-[86%] max-w-sm border-r border-[var(--line)] bg-white transition-transform duration-200 ease-out lg:static lg:inset-auto lg:z-0 lg:flex lg:h-full lg:max-w-none lg:translate-x-0 ${
          isSidebarCollapsed ? "lg:hidden" : ""
        }`}
        aria-label="Conversations"
        aria-hidden={isSidebarCollapsed && !isSidebarOpen ? true : undefined}
      >
        <div className="flex h-full min-h-0 w-full flex-col pt-16 lg:pt-0">
          <div className="module-tab">Conversations</div>
          <div className="border-b border-[var(--line)] p-2">
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => void startNewChat()}
                className="min-h-11 flex-1 bg-[var(--signal)] px-3 text-xs font-bold uppercase tracking-wide text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
              >
                New conversation
              </button>
              <button
                type="button"
                onClick={() => setIsSidebarCollapsed(true)}
                className="hidden min-h-11 min-w-11 items-center justify-center rounded-sm border border-[var(--line)] text-sm lg:inline-flex focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                aria-label="Hide conversations"
              >
                <ChevronLeftIcon className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={() => setIsSidebarOpen(false)}
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-sm border border-[var(--line)] text-sm lg:hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                aria-label="Close conversations panel"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>
            <label className="mt-3 block">
              <span className="sr-only">Search conversations</span>
              <input
                value={sidebarSearch}
                onChange={(event) => setSidebarSearch(event.target.value)}
                placeholder="Search conversations"
                className="h-11 w-full rounded-sm border border-[var(--line)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]"
              />
            </label>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
            {loadingConversation && history.length === 0 ? (
              <p className="px-2 py-3 text-sm text-[var(--ink-muted)]" role="status">
                Loading conversations…
              </p>
            ) : filteredHistory.length === 0 ? (
              <p className="px-2 py-3 text-sm text-[var(--ink-muted)]">
                {caseId ? "Case chats stay on this matter." : "No matching conversations."}
              </p>
            ) : (
              <>
                {groupedHistory.map((group) => (
                  <div key={group.label} className="mb-3">
                    <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-[var(--ink-muted)]">{group.label}</p>
                    {group.items.map((item) => (
                      <div
                        key={item.id}
                        className={`mb-1 border ${item.id === conversationId ? "border-[var(--signal)] bg-[var(--signal-soft)]" : "border-transparent hover:border-[var(--line)]"}`}
                      >
                        <button type="button" onClick={() => void openChat(item.id)} className="w-full p-3 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]">
                          <p className="truncate text-sm font-semibold">{item.title}</p>
                          <div className="mt-1 flex items-center justify-between gap-2">
                            <p className="truncate text-[11px] text-[var(--ink-muted)]">Legal chat thread</p>
                            <span className="shrink-0 text-[10px] text-[var(--ink-muted)]">{formatRelativeDate(item.updated_at)}</span>
                          </div>
                        </button>
                        <div className="flex items-center justify-end px-3 pb-2">
                          <button
                            type="button"
                            onClick={() => void handleDeleteConversation(item.id)}
                            className="min-h-10 text-xs text-[var(--warn)] underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
                            aria-label={`Delete conversation: ${item.title}`}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
                {history.length > 0 ? (
                  <p className="border-t border-[var(--line)] px-2 py-2 text-center text-[11px] font-bold text-[var(--signal)]">
                    Show all history ({history.length})
                  </p>
                ) : null}
              </>
            )}
          </div>
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

      <section className="flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[var(--line)] px-4 py-2 sm:px-6">
          {caseId ? (
            <Link
              href={`/cases/${caseId}`}
              className="inline-flex min-h-11 shrink-0 items-center rounded-sm border border-[var(--line)] px-3 text-xs font-semibold text-[var(--forest)] sm:text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            >
              <span className="sm:hidden">← Case</span>
              <span className="hidden sm:inline">← Back to case</span>
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-sm border border-[var(--line)] text-sm lg:hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Open conversations panel"
            >
              <MenuIcon className="h-5 w-5" />
            </button>
          )}
          {isSidebarCollapsed ? (
            <button
              type="button"
              onClick={() => setIsSidebarCollapsed(false)}
              className="hidden min-h-11 min-w-11 shrink-0 items-center justify-center rounded-sm border border-[var(--line)] text-sm lg:inline-flex focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Show conversations"
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          ) : null}
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-sm font-semibold">{conversationTitle}</h2>
            <p className="truncate text-xs text-[var(--ink-muted)]">
              {interviewStep ? (
                <>
                  Step {interviewStep.current} of {interviewStep.total} · {interviewStep.label}
                </>
              ) : (
                <>Answering in {formatLanguageLabel(languageOption)}</>
              )}
            </p>
          </div>
          <LanguageSelector compact />
          <div className="flex rounded-sm border border-[var(--line)] p-0.5" role="group" aria-label="Input mode">
            <button
              type="button"
              onClick={() => {
                voiceChat.reset();
                answerPlayback.stop();
                setChatMode("text");
              }}
              className={`min-h-11 rounded-none px-3 text-xs font-bold uppercase tracking-wide focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] ${chatMode === "text" ? "bg-[var(--signal)] text-white" : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"}`}
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
              className={`min-h-11 rounded-none px-3 text-xs font-bold uppercase tracking-wide focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] ${chatMode === "voice" ? "bg-[var(--signal)] text-white" : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"}`}
              aria-pressed={chatMode === "voice"}
            >
              Voice
            </button>
          </div>
        </div>

        {caseId ? (
          <p className="shrink-0 border-b border-[var(--line)] bg-[var(--signal-soft)] px-4 py-2 text-sm text-[var(--forest)]">
            This conversation may use official legal sources and your authorized case documents. Uploaded files are not
            official law.
          </p>
        ) : null}

        <div ref={scrollRef} className="chat-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-4 sm:px-4 md:px-8 md:py-6">
          {chatMode === "voice" && (
            <div className="mb-6">
              {!voiceSupportedForLanguage ? (
                <p className="mb-3 rounded-sm border border-[var(--line)] bg-white px-4 py-3 text-sm text-[var(--ink-muted)]">
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
                autoSend={voiceChat.autoSend}
                onAutoSendChange={voiceChat.setAutoSend}
                continuousMode={voiceChat.continuousMode}
                onContinuousModeChange={voiceChat.setContinuousMode}
                autoplayBlocked={voiceChat.autoplayBlocked}
                onUnlockAutoplay={voiceChat.unlockAutoplay}
                audioLevel={voiceChat.audioLevel}
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
            <p className="mt-16 text-center text-sm text-[var(--ink-muted)]" role="status" aria-busy="true">
              Loading conversation…
            </p>
          ) : messages.length === 0 ? (
            <div className="mx-auto mt-8 max-w-xl text-center sm:mt-12">
              {error ? (
                <div
                  className="mb-6 rounded-sm border border-[var(--warn-line)] bg-[var(--warn-bg)] px-4 py-3 text-left text-sm text-[var(--warn)]"
                  role="alert"
                >
                  <p>{error}</p>
                  <button
                    type="button"
                    onClick={() => setError(null)}
                    className="mt-2 underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                  >
                    Dismiss
                  </button>
                </div>
              ) : null}
              <h3 className="text-2xl font-semibold tracking-tight">Describe your situation</h3>
              <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
                ChatLaw currently answers from the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam. Ask a section or offence from those codes.
              </p>
              <div className="mt-6 grid gap-2 text-left">
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => applySuggestedQuestion(question)}
                    className="min-h-11 rounded-sm border border-[var(--line)] bg-white px-3 py-2 text-sm hover:border-[var(--forest)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <ChatMessageList
              messages={messages}
              isLoading={isLoading}
              loadingStepLabel={loadingStepLabel}
              chatMode={chatMode}
              draftGenerating={draftGenerating}
              speechListening={speech.isListening}
              playback={answerPlayback}
              onOpenCitation={handleOpenCitation}
              onAskAnother={handleAskAnother}
            />
          )}
        </div>

        {chatMode === "text" && (
          <div className="shrink-0 border-t border-[var(--line)] bg-[var(--background)] px-2 py-2 sm:px-3 sm:py-2">
            {error && messages.length > 0 ? (
              <div
                className="mb-2 w-full border border-[var(--warn-line)] bg-[var(--warn-bg)] px-4 py-3 text-sm text-[var(--warn)]"
                role="alert"
              >
                {error}{" "}
                <button
                  type="button"
                  onClick={() => setError(null)}
                  className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                >
                  Dismiss
                </button>
              </div>
            ) : null}
            <form onSubmit={handleSubmit} className="w-full border border-[var(--line)] bg-white">
              <div className="module-tab">Question input</div>
              <div className="flex items-end gap-2 p-2">
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
                  className="max-h-48 min-h-11 w-full resize-y bg-transparent px-3 py-2 text-sm leading-6 outline-none placeholder:text-[var(--ink-muted)] focus-visible:ring-2 focus-visible:ring-[var(--focus)] disabled:cursor-not-allowed disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={isLoading || loadingConversation || speech.isListening || !input.trim()}
                  className="min-h-11 shrink-0 bg-[var(--signal)] px-4 text-xs font-bold uppercase tracking-wide text-white disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
                  aria-label="Send message"
                >
                  {isLoading ? "Sending..." : "Send"}
                </button>
              </div>
              <div className="flex flex-col gap-2 border-t border-[var(--line)] px-2 py-2 sm:flex-row sm:items-start sm:justify-between">
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
                  <span
                    className={remainingChars < 200 ? "text-[var(--warn)]" : ""}
                    aria-live={remainingChars < 200 ? "polite" : "off"}
                  >
                    {remainingChars} characters left
                  </span>
                </div>
              </div>
            </form>
            <p className="mt-2 px-1 text-[10px] leading-5 text-[var(--ink-muted)]">
              Informational assistance only — not a substitute for a lawyer or court.
            </p>
          </div>
        )}
      </section>

      {citationPanel && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Source citation"
        >
          <button
            type="button"
            className="absolute inset-0"
            onClick={() => setCitationPanel(null)}
            aria-label="Close citation"
          />
          <div className="relative z-10 flex max-h-[min(85vh,720px)] w-full max-w-xl flex-col overflow-hidden border border-[var(--line)] bg-white shadow-lg">
            <div className="module-tab shrink-0">
              Source [{citationPanel.citation.id}]
            </div>
            <div className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--line)] px-4 py-3">
              <div className="min-w-0">
                <h3 className="text-base font-semibold leading-snug">
                  {citationPanel.citation.document || "Source unavailable"}
                </h3>
                {isCaseDocumentCitation(citationPanel.citation) ? (
                  <p className="mt-1 text-xs font-semibold text-[var(--forest)]">
                    Case document — not an official legal source
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-[var(--ink-muted)]">
                    {[
                      citationPanel.citation.section
                        ? `Section ${citationPanel.citation.section}`
                        : "Section unavailable",
                      citationPanel.citation.subsection
                        ? `Subsection ${citationPanel.citation.subsection}`
                        : null,
                      citationPanel.citation.page !== null
                        ? `Page ${citationPanel.citation.page}`
                        : null,
                      citationPanel.citation.jurisdiction_level === "CENTRAL"
                        ? "Central Law"
                        : citationPanel.citation.jurisdiction_level,
                      citationPanel.citation.domain
                        ? citationPanel.citation.domain.replace(/_/g, " ")
                        : null,
                      citationPanel.citation.source?.url ? "Official source" : null,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setCitationPanel(null)}
                className="inline-flex min-h-10 min-w-10 shrink-0 items-center justify-center rounded-sm border border-[var(--line)] text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                aria-label="Close citation"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="chat-scroll min-h-0 flex-1 overflow-y-auto px-4 py-4">
              {citationEvidenceParagraphs.length > 0 ? (
                <div className="space-y-3 text-sm leading-relaxed text-[var(--foreground)]">
                  {citationEvidenceParagraphs.map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[var(--ink-muted)]">No excerpt available for this source.</p>
              )}
            </div>
            <div className="flex shrink-0 flex-wrap gap-2 border-t border-[var(--line)] px-4 py-3">
              <button
                type="button"
                onClick={() => navigator.clipboard.writeText(composeCitationText(citationPanel.citation))}
                className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-sm"
              >
                Copy citation
              </button>
              {(() => {
                const sourceUrl = isSafeExternalUrl(citationPanel.citation.source?.url);
                return sourceUrl ? (
                  <a
                    className="inline-flex min-h-10 items-center rounded-sm border border-[var(--line)] px-3 text-sm text-[var(--forest)] underline"
                    href={sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View source
                  </a>
                ) : null;
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
