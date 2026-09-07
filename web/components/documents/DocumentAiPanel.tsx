"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { STATUS_LABELS } from "@/lib/documents/constants";
import type { DocumentStatus, DocumentWarning, GeneratedDocumentPayload } from "@/lib/documents/types";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import {
  AudioRecorderSession,
  chatLanguageToSpeechCode,
  isAudioRecordingSupported,
  SpeechOutputSession,
  transcribeAudio,
} from "@/lib/speech";

type VersionSummary = {
  id: string;
  versionNumber: number;
  status: string;
  title: string;
  createdAt: string;
};

type ChatItem = { role: "user" | "assistant"; content: string };

export default function DocumentAiPanel({
  payload,
  status,
  versions,
  busy,
  messages,
  pendingRevise,
  onStatus,
  onRestore,
  onRevise,
  onAcceptRevise,
  onRejectRevise,
}: {
  payload: GeneratedDocumentPayload;
  status: DocumentStatus;
  versions: VersionSummary[];
  busy: string | null;
  messages: ChatItem[];
  pendingRevise: GeneratedDocumentPayload | null;
  onStatus: (status: DocumentStatus) => void;
  onRestore: (versionNumber: number) => void;
  onRevise: (instruction: string) => void;
  onAcceptRevise: () => void;
  onRejectRevise: () => void;
}) {
  const [instruction, setInstruction] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeakingIndex, setIsSpeakingIndex] = useState<number | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const recorderRef = useRef<AudioRecorderSession | null>(null);
  const outputSessionRef = useRef<SpeechOutputSession | null>(null);

  const { language } = useLanguage();
  const speechLang = useMemo(() => chatLanguageToSpeechCode(language), [language]);

  useEffect(() => {
    outputSessionRef.current = new SpeechOutputSession({
      onStart: () => {},
      onEnd: () => setIsSpeakingIndex(null),
      onPause: () => {},
      onResume: () => {},
      onError: () => setIsSpeakingIndex(null),
    });

    return () => {
      recorderRef.current?.cancel();
      outputSessionRef.current?.dispose();
    };
  }, []);

  function speakMessage(index: number, text: string) {
    if (isSpeakingIndex === index) {
      outputSessionRef.current?.stop();
      setIsSpeakingIndex(null);
      return;
    }
    setIsSpeakingIndex(index);
    outputSessionRef.current?.speak(text, speechLang);
  }

  async function toggleRecording() {
    if (isRecording) {
      setIsRecording(false);
      try {
        const recordingResult = await recorderRef.current?.stop();
        if (recordingResult?.blob && recordingResult.blob.size > 0) {
          const stt = await transcribeAudio(recordingResult.blob, speechLang);
          if (stt.transcript.trim()) {
            setInstruction(stt.transcript.trim());
          }
        }
      } catch (err) {
        setVoiceError(err instanceof Error ? err.message : "Voice input failed.");
      }
      return;
    }

    if (!isAudioRecordingSupported()) {
      setVoiceError("Microphone recording is not supported in this browser.");
      return;
    }

    outputSessionRef.current?.stop();
    setIsSpeakingIndex(null);
    setVoiceError(null);

    const recorder = new AudioRecorderSession({
      onStart: () => setIsRecording(true),
      onError: (msg) => {
        setIsRecording(false);
        setVoiceError(msg);
      },
    });
    recorderRef.current = recorder;
    await recorder.start();
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = instruction.trim();
    if (!text) return;
    onRevise(text);
    setInstruction("");
  }

  return (
    <div className="space-y-4">
      <div className="rounded-sm border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">AI Assistant</h2>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
          Ask for document revisions by text or voice. Suggestions are previewed before replacing your draft.
        </p>

        <div className="mt-3 max-h-48 space-y-2 overflow-auto" aria-live="polite">
          {messages.length === 0 ? (
            <p className="text-sm text-[var(--ink-muted)]">Examples: &ldquo;Make the termination period 30 days&rdquo; or &ldquo;Add a confidentiality clause.&rdquo;</p>
          ) : (
            messages.map((item, index) => (
              <div key={`${item.role}-${index}`} className={`rounded-sm px-3 py-2 text-sm ${item.role === "user" ? "bg-[var(--signal-soft)]" : "bg-[var(--module-fill)]"}`}>
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink-muted)]">{item.role === "user" ? "You" : "Assistant"}</p>
                  {item.role === "assistant" && (
                    <button
                      type="button"
                      onClick={() => speakMessage(index, item.content)}
                      className="text-xs text-[var(--forest)] hover:underline flex items-center gap-1 font-medium"
                      aria-label={isSpeakingIndex === index ? "Stop reading" : "Read aloud"}
                    >
                      <span>{isSpeakingIndex === index ? "⏹️ Stop" : "🔊 Listen"}</span>
                    </button>
                  )}
                </div>
                <p className="mt-1 whitespace-pre-wrap">{item.content}</p>
              </div>
            ))
          )}
        </div>

        {pendingRevise ? (
          <div className="mt-3 rounded-sm border border-[var(--line)] bg-[#f8faf6] p-3">
            <p className="text-sm font-medium">Pending document changes</p>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">
              {pendingRevise.sections.length} sections in proposal. Accept to apply locally, then save a version.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button type="button" onClick={onAcceptRevise} disabled={busy !== null} className="min-h-11 rounded-sm bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
                Accept
              </button>
              <button type="button" onClick={onRejectRevise} disabled={busy !== null} className="min-h-11 rounded-sm border border-[var(--line)] bg-white px-4 text-sm">
                Reject
              </button>
            </div>
          </div>
        ) : null}

        <form onSubmit={submit} className="mt-3 space-y-2">
          <label htmlFor="doc-ai-instruction" className="sr-only">Document change instruction</label>
          <div className="flex flex-wrap gap-1.5 pb-1">
            <span className="text-[10px] uppercase font-semibold text-[var(--ink-muted)] w-full">Quick suggestions:</span>
            {[
              "Add a 60-day notice period",
              "Include a pet restriction clause",
              "Add late payment interest of 18% p.a.",
              "Add lock-in period of 6 months",
              "Translate active clause to Tamil",
            ].map((tip) => (
              <button
                key={tip}
                type="button"
                onClick={() => setInstruction(tip)}
                className="rounded-xs border border-[var(--line)] bg-[var(--canvas)] px-2 py-1 text-[11px] text-[var(--ink-muted)] hover:border-[var(--forest)] hover:text-[var(--foreground)]"
              >
                {tip}
              </button>
            ))}
          </div>

          <div className="relative">
            <textarea
              id="doc-ai-instruction"
              value={instruction}
              onChange={(event) => setInstruction(event.target.value)}
              rows={3}
              placeholder="Describe the clause change or speak your instruction..."
              className="w-full rounded-sm border border-[var(--line)] p-3 text-sm focus:border-[var(--forest)] focus:outline-none"
              disabled={busy !== null}
            />
          </div>

          {voiceError && (
            <p className="text-xs text-red-600">{voiceError}</p>
          )}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleRecording}
              disabled={busy !== null}
              className={`min-h-11 rounded-sm px-4 text-sm font-semibold transition-colors flex items-center justify-center gap-1.5 ${
                isRecording
                  ? "bg-red-600 text-white animate-pulse"
                  : "border border-[var(--line)] bg-[var(--canvas)] text-[var(--foreground)] hover:border-[var(--forest)]"
              }`}
              title={isRecording ? "Stop recording" : "Speak instruction"}
              aria-label={isRecording ? "Stop recording instruction" : "Speak instruction with microphone"}
            >
              <span>{isRecording ? "⏹️" : "🎙️"}</span>
              <span>{isRecording ? "Done" : "Voice"}</span>
            </button>
            <button
              type="submit"
              disabled={busy !== null || !instruction.trim()}
              className="min-h-11 flex-1 rounded-sm bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60"
            >
              {busy === "revise" ? "Working…" : "Propose targeted changes"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-sm border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">Warnings and legal context</h2>
        <ul className="mt-3 space-y-2">
          {(payload.warnings as DocumentWarning[]).map((warning) => (
            <li key={`${warning.code}-${warning.message.slice(0, 24)}`} className="text-sm leading-6">{warning.message}</li>
          ))}
        </ul>
        {payload.sections.some((section) => section.legal_basis?.length) ? (
          <div className="mt-4">
            <h3 className="text-sm font-medium">Citations</h3>
            <ul className="mt-2 space-y-1 text-sm text-[var(--ink-muted)]">
              {payload.sections.flatMap((section) =>
                (section.legal_basis || []).map((item) => (
                  <li key={`${section.id}-${item.citation_id}`}>{item.label}</li>
                )),
              )}
            </ul>
          </div>
        ) : null}
      </div>

      <div className="rounded-sm border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">Draft status</h2>
        <div className="mt-2 flex items-center gap-2">
          <span className="rounded-xs bg-[var(--module-fill)] px-2 py-0.5 text-xs font-semibold">{STATUS_LABELS[status]}</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" onClick={() => onStatus("draft")} className="rounded-xs border border-[var(--line)] px-2.5 py-1 text-xs">
            Mark draft
          </button>
          <button type="button" onClick={() => onStatus("in_review")} className="rounded-xs border border-[var(--line)] px-2.5 py-1 text-xs">
            Mark in review
          </button>
          <button type="button" onClick={() => onStatus("ready_for_execution")} className="rounded-xs border border-[var(--line)] px-2.5 py-1 text-xs">
            Mark ready for execution
          </button>
        </div>
      </div>

      <div className="rounded-sm border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">Version history</h2>
        <ol className="mt-3 space-y-2 text-sm text-[var(--ink-muted)]">
          {versions.map((ver) => (
            <li key={ver.id} className="flex items-center justify-between gap-2">
              <span>v{ver.versionNumber} ({ver.status})</span>
              <button type="button" onClick={() => onRestore(ver.versionNumber)} className="text-xs text-[var(--forest)] underline">
                Restore
              </button>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
