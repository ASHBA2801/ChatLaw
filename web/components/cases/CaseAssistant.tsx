"use client";

import { FormEvent, useState } from "react";
import type { Citation } from "@/lib/api/rag";
import { isCaseDocumentCitation } from "@/lib/api/rag";
import { useAnswerPlayback, useSpeechInput } from "@/lib/speech";
import AnswerPlaybackControls from "@/components/chat/AnswerPlaybackControls";
import VoiceInputControls from "@/components/chat/VoiceInputControls";

type AssistantMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  error?: boolean;
};

const SUGGESTIONS = [
  "What documents mention the security deposit?",
  "What does my agreement say about termination?",
  "Which legal provisions may be relevant?",
];

function citationLabel(citation: Citation) {
  if (isCaseDocumentCitation(citation)) {
    return `Case Document — ${citation.document || "Uploaded file"}${citation.page != null ? ` — Page ${citation.page}` : ""}`;
  }
  return [
    citation.document || "Legal source",
    citation.section ? `Section ${citation.section}` : null,
    citation.page != null ? `Page ${citation.page}` : null,
  ].filter(Boolean).join(" — ");
}

export default function CaseAssistant({ caseId }: { caseId: string }) {
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const speech = useSpeechInput({
    value: input,
    onChange: setInput,
    limit: 4000,
    disabled: loading,
  });
  const answerPlayback = useAnswerPlayback();

  async function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    speech.cancel();
    answerPlayback.stop();
    setLoading(true);
    setError("");
    setInput("");
    const userMessage: AssistantMessage = { id: `u-${crypto.randomUUID()}`, role: "user", content: trimmed };
    setMessages((current) => [...current, userMessage]);
    try {
      const response = await fetch(`/api/cases/${caseId}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, conversationId }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "The question could not be answered.");
      }
      if (typeof payload.conversation_id === "string") setConversationId(payload.conversation_id);
      const citations = Array.isArray(payload.citations) ? payload.citations as Citation[] : [];
      setMessages((current) => [
        ...current,
        {
          id: payload.assistant_message?.id || `a-${crypto.randomUUID()}`,
          role: "assistant",
          content: payload.answer || "I couldn't find sufficiently relevant information in the available legal sources or this case's documents.",
          citations,
        },
      ]);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "The question could not be answered.";
      setError(message);
      setMessages((current) => [...current, { id: `e-${crypto.randomUUID()}`, role: "assistant", content: message, error: true }]);
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(input);
  }

  const composerValue = speech.isListening ? speech.displayValue : input;

  return (
    <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
      <h2 className="text-lg font-semibold">AI assistant</h2>
      <p className="mt-1 text-sm text-[var(--ink-muted)]">
        Ask about this case by text or voice. Answers use official legal sources and your authorized case documents. Case files are never shown as statutes.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {SUGGESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => void ask(question)}
            disabled={loading || speech.isListening}
            className="min-h-10 rounded-lg border border-[var(--line)] px-3 text-left text-sm hover:border-[var(--forest)] disabled:opacity-50"
          >
            {question}
          </button>
        ))}
      </div>
      <div className="mt-4 max-h-80 space-y-3 overflow-y-auto">
        {messages.length === 0 ? (
          <p className="rounded-xl border border-dashed border-[var(--line)] p-4 text-sm text-[var(--ink-muted)]">
            Ask about this case to combine official legal evidence with your authorized documents. Try a suggestion above, or use the microphone to speak.
          </p>
        ) : messages.map((message) => (
          <article
            key={message.id}
            className={message.role === "user"
              ? "ml-auto max-w-[90%] rounded-2xl bg-[var(--forest)] px-4 py-3 text-sm text-white"
              : `rounded-2xl border px-4 py-3 text-sm ${message.error ? "border-[#e3c59f] bg-[#fff5e7]" : "border-[var(--line)] bg-[var(--background)]"}`}
          >
            <p className="whitespace-pre-wrap leading-6">{message.content}</p>
            {message.citations && message.citations.length > 0 && (
              <ul className="mt-3 space-y-1 text-xs">
                {message.citations.map((citation) => (
                  <li key={`${citation.id}-${citation.chunk_id}`}>
                    [{citation.id}] {citationLabel(citation)}
                    {isCaseDocumentCitation(citation) ? " · User case document" : " · Legal source"}
                  </li>
                ))}
              </ul>
            )}
            {message.role === "assistant" && !message.error && (
              <AnswerPlaybackControls
                messageId={message.id}
                text={message.content}
                status={answerPlayback.status}
                activeMessageId={answerPlayback.activeMessageId}
                supported={answerPlayback.supported}
                disabled={loading || speech.isListening}
                onPlay={answerPlayback.play}
                onPause={answerPlayback.pause}
                onResume={answerPlayback.resume}
                onStop={answerPlayback.stop}
              />
            )}
          </article>
        ))}
        {loading && <p className="text-sm text-[var(--ink-muted)]" role="status">Reviewing legal sources and case documents...</p>}
      </div>
      <form onSubmit={submit} className="mt-4 flex flex-col gap-2">
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor={`case-ask-${caseId}`}>Ask about this case</label>
          <input
            id={`case-ask-${caseId}`}
            value={composerValue}
            onChange={(event) => setInput(event.target.value.slice(0, 4000))}
            disabled={loading || speech.isListening}
            placeholder="Ask about this case..."
            className="h-11 min-w-0 flex-1 rounded-lg border border-[var(--line)] px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)] disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || speech.isListening || !input.trim()}
            className="min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50"
          >
            {loading ? "Asking..." : "Ask"}
          </button>
        </div>
        <VoiceInputControls
          status={speech.status}
          supported={speech.supported}
          language={speech.language}
          onLanguageChange={speech.setLanguage}
          error={speech.error}
          interimText={speech.interimText}
          disabled={loading}
          languageSelectId={`case-speech-language-${caseId}`}
          onStart={speech.start}
          onStop={speech.stop}
          onCancel={speech.cancel}
          onClearError={speech.clearError}
        />
        <p className="text-xs text-[var(--ink-muted)]">
          Speak, review the transcript, then Ask. For full Voice mode, open full chat with this case.
        </p>
      </form>
      {error && <p className="mt-2 text-sm text-[#935a1e]" role="alert">{error}</p>}
      {answerPlayback.error && (
        <p className="mt-2 text-sm text-[#935a1e]" role="alert">
          {answerPlayback.error}{" "}
          <button type="button" onClick={answerPlayback.clearError} className="underline underline-offset-2">
            Dismiss
          </button>
        </p>
      )}
    </section>
  );
}
