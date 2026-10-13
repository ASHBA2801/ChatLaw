"use client";

import { FormEvent, KeyboardEvent, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { createPortal } from "react-dom";
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
import {
  ArrowUpIcon,
  ChevronLeftIcon,
  CloseIcon,
  HistoryIcon,
  MenuIcon,
  PlusIcon,
  SearchIcon,
  TrashIcon,
  WaveformIcon,
} from "@/components/chat/ChatIcons";
import { composeCitationText, formatCitationEvidence, groupConversationsByDate, runConversationBoot, type CitationPanelState } from "@/components/chat/chatUtils";
import { useChatSidebar } from "@/components/layout/ChatSidebarContext";
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

/** `initialPrompt` pre-fills the composer (used by the landing page prompt box); it is never sent automatically. */
export default function ChatInterface({ caseId, initialPrompt }: { caseId?: string; initialPrompt?: string }) {
  const router = useRouter();
  const sidebar = useChatSidebar();
  const closeSidebar = sidebar?.closeSidebar;
  const registerNewChat = sidebar?.registerNewChat;
  const { language, languageOption } = useLanguage();
  const speechLang = useMemo(() => chatLanguageToSpeechCode(language), [language]);
  const voiceSupportedForLanguage = useMemo(() => isSpeechLocaleLikelySupported(speechLang), [speechLang]);

  const [input, setInput] = useState(() => initialPrompt?.slice(0, MESSAGE_LIMIT) ?? "");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [loadingConversation, setLoadingConversation] = useState(true);
  const [sidebarSearch, setSidebarSearch] = useState("");
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
    closeSidebar?.();
    if (caseId) {
      window.localStorage.removeItem(`chatlaw-case-conversation:${caseId}`);
      setConversationId(null);
      setMessages([]);
      setError(null);
      setCitationPanel(null);
      inputRef.current?.focus();
      return;
    }
    if (conversationId && messages.length === 0) {
      /* Already on an empty conversation: reuse it instead of creating another. */
      setChatMode("text");
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
      closeSidebar?.();
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
  const activeTitle = history.find((item) => item.id === conversationId)?.title;
  const conversationTitle = caseId
    ? "Case conversation"
    : activeTitle && activeTitle !== "New conversation"
      ? activeTitle
      : "New chat";
  /** Empty text chat: greeting and composer sit in the middle of the page, like other chat apps. */
  const showHero = chatMode === "text" && messages.length === 0;
  /** Empty voice chat: the voice stage is centred like the hero. With messages it docks under the thread. */
  const showVoiceStage = chatMode === "voice" && messages.length === 0;
  const centred = showHero || showVoiceStage;

  /*
   * The answer card and voice panel are lazy chunks. If one first loads while rendering, React suspends up to the
   * layout-level boundary, hides the whole shell and re-runs effects — which disposes an in-flight spoken answer and
   * re-boots the conversation. Preload them, and keep a local Suspense boundary around each (below).
   */
  useEffect(() => {
    void import("@/components/chat/LegalAnswerCard");
    void import("@/components/chat/VoiceChatPanel");
  }, []);

  const focusedInitialRef = useRef(false);
  useEffect(() => {
    if (!initialPrompt || loadingConversation || focusedInitialRef.current) return;
    focusedInitialRef.current = true;
    inputRef.current?.focus();
  }, [initialPrompt, loadingConversation]);

  const startNewChatRef = useRef(startNewChat);
  useEffect(() => {
    startNewChatRef.current = startNewChat;
  });
  useEffect(() => {
    registerNewChat?.(() => void startNewChatRef.current());
    return () => registerNewChat?.(null);
  }, [registerNewChat]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 208)}px`;
  }, [composerValue, showHero, chatMode]);

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

  const historyPanel = (
    <div className="mt-2 flex min-h-0 flex-1 flex-col border-t border-[var(--line)] pt-3">
      <div className="shrink-0 px-3 pb-2">
        <label className="relative block">
          <span className="sr-only">Search conversations</span>
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ink-faint)]" />
          <input
            value={sidebarSearch}
            onChange={(event) => setSidebarSearch(event.target.value)}
            placeholder="Search chats"
            type="search"
            className="h-9 w-full rounded-lg border border-[var(--line)] bg-[var(--surface)] pl-9 pr-3 text-sm outline-none placeholder:text-[var(--ink-muted)]"
          />
        </label>
      </div>
      <div className="chat-scroll min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {loadingConversation && history.length === 0 ? (
          <p className="px-3 py-4 text-sm text-[var(--ink-muted)]" role="status">
            Loading chats…
          </p>
        ) : filteredHistory.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <HistoryIcon className="mx-auto h-6 w-6 text-[var(--ink-faint)]" />
            <p className="mt-2 text-sm text-[var(--ink-muted)]">
              {caseId
                ? "Case chats stay on this matter."
                : sidebarSearch
                  ? "No chats match your search."
                  : "Your chats will appear here."}
            </p>
          </div>
        ) : (
          groupedHistory.map((group) => (
            <section key={group.label} aria-label={group.label}>
              <h3 className="px-3 pb-1 pt-3 text-xs font-medium text-[var(--ink-muted)]">{group.label}</h3>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const active = item.id === conversationId;
                  return (
                    <li
                      key={item.id}
                      className={`group relative rounded-lg ${active ? "bg-[var(--line)]/70" : "hover:bg-[var(--line)]/50"}`}
                    >
                      <button
                        type="button"
                        onClick={() => void openChat(item.id)}
                        aria-current={active ? "true" : undefined}
                        title={item.title}
                        className={`flex h-10 w-full items-center rounded-lg pl-3 pr-10 text-left text-sm lg:pr-3 lg:group-focus-within:pr-10 lg:group-hover:pr-10 ${active ? "font-medium" : ""}`}
                      >
                        <span className="truncate">{item.title === "New conversation" ? "New chat" : item.title}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDeleteConversation(item.id)}
                        className="absolute right-1 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-[var(--ink-faint)] hover:bg-[var(--warn-bg)] hover:text-[var(--warn)] focus-visible:opacity-100 lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100"
                        aria-label={`Delete chat: ${item.title}`}
                        title="Delete chat"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))
        )}
      </div>
    </div>
  );

  const composer = (
    <form
      onSubmit={handleSubmit}
      onMouseDown={(event) => {
        // Clicking any empty part of the rounded composer focuses the text area.
        if ((event.target as HTMLElement).closest("button, a, input, select, textarea, [role='listbox'], [role='menu']")) return;
        event.preventDefault();
        inputRef.current?.focus();
      }}
      className="w-full cursor-text rounded-3xl border border-[var(--line-strong)] bg-[var(--surface)] shadow-[var(--shadow-soft)] focus-within:border-[var(--accent)]"
    >
      <label className="sr-only" htmlFor="chatlaw-message">
        Message input
      </label>
      <textarea
        id="chatlaw-message"
        ref={inputRef}
        value={composerValue}
        onChange={(event) => setInput(event.target.value.slice(0, MESSAGE_LIMIT))}
        onKeyDown={handleInputKeyDown}
        rows={1}
        disabled={isLoading || loadingConversation || speech.isListening}
        placeholder={messages.length === 0 ? "Describe your situation in your own words..." : "Ask a follow-up..."}
        className="block max-h-52 min-h-14 w-full resize-none rounded-t-3xl bg-transparent px-5 pb-1 pt-4 text-[15px] leading-6 outline-none placeholder:text-[var(--ink-muted)] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
      />
      <div className="flex items-center gap-1 px-2.5 pb-2.5 pt-1">
        <div className="min-w-0 flex-1">
          <VoiceInputControls
            variant="composer"
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
        </div>
        {remainingChars < 1000 ? (
          <span
            className={`shrink-0 px-1 text-xs ${remainingChars < 200 ? "text-[var(--warn)]" : "text-[var(--ink-muted)]"}`}
            aria-live={remainingChars < 200 ? "polite" : "off"}
          >
            {remainingChars.toLocaleString("en-IN")} left
          </span>
        ) : null}
        <button
          type="button"
          onClick={() => {
            speech.cancel();
            answerPlayback.stop();
            setChatMode("voice");
          }}
          disabled={isLoading || loadingConversation}
          className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-full px-3 text-sm font-medium text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)] disabled:opacity-50"
          aria-label="Start a voice conversation"
          title="Voice conversation"
        >
          <WaveformIcon className="h-5 w-5" />
          <span className="hidden sm:inline">Voice</span>
        </button>
        <button
          type="submit"
          disabled={isLoading || loadingConversation || speech.isListening || !input.trim()}
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-[var(--on-accent)] hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--line)] disabled:text-[var(--ink-faint)] sm:h-10 sm:w-10"
          aria-label={isLoading ? "Sending message" : "Send message"}
          title="Send (Enter)"
        >
          <ArrowUpIcon className="h-5 w-5" />
        </button>
      </div>
    </form>
  );

  const iconButton =
    "inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)]";

  return (
    <div className="flex h-full min-h-0 w-full overflow-hidden">
      {sidebar?.slot ? createPortal(historyPanel, sidebar.slot) : null}

      <section className="flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--surface)]">
        <header className="flex h-14 shrink-0 items-center gap-2 px-2 sm:px-4">
          {caseId ? (
            <Link href={`/cases/${caseId}`} className="btn-secondary btn-sm shrink-0 !px-3">
              <ChevronLeftIcon className="h-4 w-4" />
              <span className="sm:hidden">Case</span>
              <span className="hidden sm:inline">Back to case</span>
            </Link>
          ) : (
            <button type="button" onClick={sidebar?.openSidebar} className={`${iconButton} lg:hidden`} aria-label="Open menu">
              <MenuIcon className="h-5 w-5" />
            </button>
          )}
          <div className="min-w-0 flex-1 px-1">
            <h1 className="truncate text-[15px] font-semibold leading-tight">{conversationTitle}</h1>
            {messages.length > 0 && interviewStep ? (
              <p className="truncate text-xs leading-tight text-[var(--ink-muted)]">
                Step {interviewStep.current} of {interviewStep.total} · {interviewStep.label}
              </p>
            ) : null}
          </div>
          <LanguageSelector compact variant="ghost" />
          {caseId ? null : (
            <button type="button" onClick={() => void startNewChat()} className={`${iconButton} lg:hidden`} aria-label="New chat">
              <PlusIcon className="h-5 w-5" />
            </button>
          )}
        </header>

        {caseId ? (
          <p className="shrink-0 border-y border-[var(--accent-mid)] bg-[var(--accent-soft)] px-4 py-2 text-[13px] text-[var(--accent)]">
            This conversation may use official legal sources and your authorized case documents. Uploaded files are not
            official law.
          </p>
        ) : null}

        <div
          className={`flex min-h-0 flex-1 flex-col ${centred ? "overflow-y-auto pb-[6vh] [&>*:first-child]:mt-auto [&>*:last-child]:mb-auto" : ""}`}
        >
          {showHero ? (
            <div className="rise-in mx-auto w-full max-w-3xl shrink-0 px-5 pt-6 text-center">
              <Image
                src="/ChatLaw Logo.png"
                alt=""
                width={112}
                height={112}
                priority
                className="mx-auto h-14 w-14 rounded-full object-contain"
              />
              <h2 className="mt-5 text-[1.75rem] font-semibold leading-tight tracking-tight sm:text-[2rem]">
                What legal question can I help with?
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-[15px] leading-7 text-[var(--ink-muted)]">
                ChatLaw currently answers from the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and
                Bharatiya Sakshya Adhiniyam. Ask a section or offence from those codes.
              </p>
            </div>
          ) : null}

          {centred ? null : (
            <div
              ref={scrollRef}
              className="chat-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-6 pt-2 sm:px-5"
            >
              {loadingConversation ? (
                <p className="mt-16 text-center text-sm text-[var(--ink-muted)]" role="status" aria-busy="true">
                  Loading conversation…
                </p>
              ) : (
                <Suspense
                  fallback={
                    <p className="mt-16 text-center text-sm text-[var(--ink-muted)]" role="status" aria-busy="true">
                      Loading…
                    </p>
                  }
                >
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
                </Suspense>
              )}
            </div>
          )}

          {chatMode === "text" ? (
            <div className={`shrink-0 px-3 sm:px-5 ${showHero ? "pb-3 pt-6" : "pb-3 pt-1"}`}>
              <div className="mx-auto w-full max-w-3xl">
                {error ? (
                  <div
                    className="mb-3 w-full rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] px-4 py-3 text-sm text-[var(--warn)]"
                    role="alert"
                  >
                    {error}{" "}
                    <button
                      type="button"
                      onClick={() => setError(null)}
                      className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
                    >
                      Dismiss
                    </button>
                  </div>
                ) : null}
                {composer}
                {showHero ? (
                  <div className="mt-4 grid gap-2 sm:grid-cols-2">
                    {SUGGESTED_QUESTIONS.map((question, index) => (
                      <button
                        key={question}
                        type="button"
                        onClick={() => applySuggestedQuestion(question)}
                        className={`${index >= 2 ? "hidden sm:block" : ""} rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-left text-sm leading-6 hover:bg-[var(--fill)]`}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                ) : null}
                <p className="mt-3 px-1 text-center text-xs leading-5 text-[var(--ink-faint)]">
                  Informational assistance only — not a substitute for a lawyer or court.
                </p>
              </div>
            </div>
          ) : null}
          {chatMode === "voice" ? (
            <div className={`shrink-0 px-3 sm:px-5 ${showVoiceStage ? "pb-3 pt-6" : "pb-3 pt-1"}`}>
              <div className="mx-auto w-full max-w-3xl">
                {!voiceSupportedForLanguage ? (
                  <p className="mb-3 rounded-xl border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm text-[var(--ink-muted)]">
                    Voice may not be available for {formatLanguageLabel(languageOption)} in this browser. Text chat
                    still works in your selected language.
                  </p>
                ) : null}
                <Suspense fallback={<div className="h-40" aria-busy="true" />}>
                  <VoiceChatPanel
                    compact={!showVoiceStage}
                    state={voiceChat.state === "thinking" && isLoading ? "thinking" : voiceChat.state}
                    stateLabel={voiceChat.state === "thinking" && isLoading ? "Researching…" : voiceChat.stateLabel}
                    supported={voiceChat.supported}
                    ttsSupported={voiceChat.ttsSupported}
                    language={voiceChat.language}
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
                </Suspense>
                <p className="mt-3 px-1 text-center text-xs leading-5 text-[var(--ink-faint)]">
                  Informational assistance only — not a substitute for a lawyer or court.
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      {citationPanel && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#12151c]/45 p-4"
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
          <div className="relative z-10 flex max-h-[min(85vh,720px)] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow-raised)]">
            <div className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--line)] px-4 py-3">
              <div className="min-w-0">
                <p className="mb-1 text-xs font-semibold text-[var(--accent)]">Source [{citationPanel.citation.id}]</p>
                <h3 className="text-base font-semibold leading-snug">
                  {citationPanel.citation.document || "Source unavailable"}
                </h3>
                {isCaseDocumentCitation(citationPanel.citation) ? (
                  <p className="mt-1 text-xs font-semibold text-[var(--accent)]">
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
                className="inline-flex min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg text-[var(--ink-muted)] hover:bg-[var(--fill)]"
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
                className="btn-secondary !min-h-10 !px-3.5 !text-[13px]"
              >
                Copy citation
              </button>
              {(() => {
                const sourceUrl = isSafeExternalUrl(citationPanel.citation.source?.url);
                return sourceUrl ? (
                  <a
                    className="btn-secondary !min-h-10 !px-3.5 !text-[13px] !text-[var(--accent)]"
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
