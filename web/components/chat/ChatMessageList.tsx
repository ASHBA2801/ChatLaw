"use client";

import { memo, useMemo } from "react";
import dynamic from "next/dynamic";
import type { ChatResponse, StoredMessage } from "@/lib/api/rag";
import type { UseAnswerPlaybackResult } from "@/lib/speech/useAnswerPlayback";
import type { ChatInputMode } from "@/lib/speech/types";

const ClarificationCard = dynamic(() =>
  import("@/components/chat/LegalAnswerCard").then((mod) => ({ default: mod.ClarificationCard })),
);
const DocumentDraftCard = dynamic(() =>
  import("@/components/chat/LegalAnswerCard").then((mod) => ({ default: mod.DocumentDraftCard })),
);
const LegalAnswerCard = dynamic(() =>
  import("@/components/chat/LegalAnswerCard").then((mod) => ({ default: mod.LegalAnswerCard })),
);

export type ChatMessage =
  | StoredMessage
  | { id: string; role: "assistant"; content: string; response?: ChatResponse; error?: boolean };

function buildPriorUserTexts(messages: ChatMessage[]): string[] {
  let lastUser = "";
  return messages.map((message) => {
    if (message.role === "user") {
      lastUser = message.content;
      return "";
    }
    const prior = lastUser;
    return prior;
  });
}

function responseFromStoredMessage(message: ChatMessage): ChatResponse | undefined {
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

  if (
    kind === "clarification" ||
    kind === "document_clarification" ||
    kind === "document_unsupported" ||
    kind === "document_ready"
  ) {
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
    citations: citations as ChatResponse["citations"],
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

type ChatMessageItemProps = {
  message: ChatMessage;
  priorUserText: string;
  chatMode: ChatInputMode;
  draftGenerating: boolean;
  isLoading: boolean;
  speechListening: boolean;
  playback: UseAnswerPlaybackResult;
  onOpenCitation: (citation: ChatResponse["citations"][number]) => void;
  onAskAnother?: () => void;
};

const ChatMessageItem = memo(function ChatMessageItem({
  message,
  priorUserText,
  chatMode,
  draftGenerating,
  isLoading,
  speechListening,
  playback,
  onOpenCitation,
  onAskAnother,
}: ChatMessageItemProps) {
  const response =
    message.role === "assistant" ? message.response || responseFromStoredMessage(message) : undefined;

  return (
    <article
      className={
        message.role === "user"
          ? "ml-auto w-full max-w-[96%] rounded-sm rounded-br-md bg-[var(--forest)] px-4 py-3 text-sm text-white sm:max-w-[80%] [content-visibility:auto]"
          : `w-full rounded-sm rounded-bl-md border px-4 py-4 text-[var(--foreground)] [content-visibility:auto] ${message.error ? "border-[var(--warn-line)] bg-[var(--warn-bg)]" : "border-[var(--line)] bg-white"}`
      }
    >
      {message.role === "user" ? (
        <p className="whitespace-pre-wrap leading-6">{message.content}</p>
      ) : message.error ? (
        <div role="alert">
          <p className="leading-6">{message.content}</p>
        </div>
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
          onOpenCitation={onOpenCitation}
          onAskAnother={onAskAnother}
          playback={playback}
          chatMode={chatMode}
          disabledPlayback={isLoading || speechListening}
        />
      ) : (
        <p className="whitespace-pre-wrap leading-6">{message.content}</p>
      )}
    </article>
  );
});

export type ChatMessageListProps = {
  messages: ChatMessage[];
  isLoading: boolean;
  loadingStepLabel: string;
  chatMode: ChatInputMode;
  draftGenerating: boolean;
  speechListening: boolean;
  playback: UseAnswerPlaybackResult;
  onOpenCitation: (citation: ChatResponse["citations"][number]) => void;
  onAskAnother?: () => void;
};

const ChatMessageList = memo(function ChatMessageList({
  messages,
  isLoading,
  loadingStepLabel,
  chatMode,
  draftGenerating,
  speechListening,
  playback,
  onOpenCitation,
  onAskAnother,
}: ChatMessageListProps) {
  const priorUserTexts = useMemo(() => buildPriorUserTexts(messages), [messages]);

  return (
    <div className="mx-auto flex w-full flex-col gap-4">
      {messages.map((message, index) => (
        <ChatMessageItem
          key={message.id}
          message={message}
          priorUserText={priorUserTexts[index] ?? ""}
          chatMode={chatMode}
          draftGenerating={draftGenerating}
          isLoading={isLoading}
          speechListening={speechListening}
          playback={playback}
          onOpenCitation={onOpenCitation}
          onAskAnother={onAskAnother}
        />
      ))}
      {isLoading && (
        <div
          className="w-full rounded-sm rounded-bl-md border border-[var(--line)] bg-white px-4 py-4 text-sm text-[var(--ink-muted)]"
          role="status"
          aria-busy="true"
        >
          {loadingStepLabel}
        </div>
      )}
    </div>
  );
});

export default ChatMessageList;
