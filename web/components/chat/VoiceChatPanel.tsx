"use client";

import type { SpeechLanguageCode, VoiceChatState } from "@/lib/speech/types";
import { getEnabledSpeechLanguages } from "@/lib/speech/support";

function VoiceOrb({ state }: { state: VoiceChatState }) {
  const active = state === "listening" || state === "speaking";
  const paused = state === "paused";
  const error = state === "error";
  const reviewing = state === "ready_to_send";

  return (
    <div
      className={`relative mx-auto flex h-28 w-28 items-center justify-center rounded-full border-2 ${
        error
          ? "border-[#e3c59f] bg-[#fff5e7]"
          : reviewing
            ? "border-[var(--warm)] bg-[#fff8ef]"
            : active
              ? "border-[var(--forest)] bg-[#eef5d0]"
              : "border-[var(--line)] bg-white"
      }`}
      aria-hidden="true"
    >
      <div
        className={`h-16 w-16 rounded-full ${
          state === "listening"
            ? "animate-pulse bg-[#b42318]/20"
            : state === "speaking"
              ? "animate-pulse bg-[var(--forest)]/20"
              : paused
                ? "bg-[var(--ink-muted)]/15"
                : reviewing
                  ? "bg-[var(--warm)]/20"
                  : "bg-[var(--forest)]/10"
        }`}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        {state === "listening" ? (
          <span className="h-3 w-3 rounded-full bg-[#b42318]" title="Listening indicator" />
        ) : state === "speaking" ? (
          <span className="flex items-end gap-1" title="Speaking indicator (decorative)">
            <span className="h-3 w-1 rounded-sm bg-[var(--forest)] voice-bar" />
            <span className="h-5 w-1 rounded-sm bg-[var(--forest)] voice-bar voice-bar-delay-1" />
            <span className="h-4 w-1 rounded-sm bg-[var(--forest)] voice-bar voice-bar-delay-2" />
          </span>
        ) : (
          <svg className="h-8 w-8 text-[var(--forest)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" />
            <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
            <path d="M12 18v3" strokeLinecap="round" />
          </svg>
        )}
      </div>
    </div>
  );
}

export interface VoiceChatPanelProps {
  state: VoiceChatState;
  stateLabel: string;
  supported: boolean;
  ttsSupported: boolean;
  language: SpeechLanguageCode;
  onLanguageChange: (language: SpeechLanguageCode) => void;
  muted: boolean;
  onMutedChange: (muted: boolean) => void;
  error: string | null;
  interimText: string;
  draftText: string;
  onDraftTextChange: (text: string) => void;
  lastUserText: string;
  lastAssistantText: string;
  disabled?: boolean;
  onStartListening: () => void;
  onStopListening: () => void;
  onCancelListening: () => void;
  onConfirmSend: () => void;
  onDiscardDraft: () => void;
  onStopSpeaking: () => void;
  onPauseSpeaking: () => void;
  onResumeSpeaking: () => void;
  onReplaySpeaking: () => void;
  onClearError: () => void;
  onSwitchToText: () => void;
}

export default function VoiceChatPanel({
  state,
  stateLabel,
  supported,
  ttsSupported,
  language,
  onLanguageChange,
  muted,
  onMutedChange,
  error,
  interimText,
  draftText,
  onDraftTextChange,
  lastUserText,
  lastAssistantText,
  disabled = false,
  onStartListening,
  onStopListening,
  onCancelListening,
  onConfirmSend,
  onDiscardDraft,
  onStopSpeaking,
  onPauseSpeaking,
  onResumeSpeaking,
  onReplaySpeaking,
  onClearError,
  onSwitchToText,
}: VoiceChatPanelProps) {
  const languages = getEnabledSpeechLanguages();
  const isReady = state === "ready_to_send";
  const displayTranscript = isReady ? draftText : (interimText || lastUserText);
  const canListen = supported && !disabled && (state === "idle" || state === "error" || state === "speaking" || state === "paused");
  const isListening = state === "listening";
  const isTranscribing = state === "transcribing";
  const isThinking = state === "thinking";
  const isSpeaking = state === "speaking";
  const isPaused = state === "paused";

  return (
    <section
      className="mx-auto flex w-full max-w-xl flex-col gap-4 rounded-2xl border border-[var(--line)] bg-white p-4 sm:p-6"
      aria-label="ChatLaw voice chat"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">ChatLaw Voice</h3>
          <p className="text-xs text-[var(--ink-muted)]">
            Tap to speak, review the transcript, then send through the normal ChatLaw pipeline.
          </p>
        </div>
        <button
          type="button"
          onClick={onSwitchToText}
          className="min-h-11 rounded-lg border border-[var(--line)] px-3 text-xs font-medium hover:border-[var(--forest)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
          aria-label="Switch to text mode"
        >
          Text mode
        </button>
      </div>

      <VoiceOrb state={state} />

      <div className="text-center" aria-live="polite">
        <p className="text-sm font-medium text-[var(--foreground)]">{stateLabel}</p>
        {!supported && (
          <p className="mt-2 text-xs text-[var(--ink-muted)]">
            Voice input isn&apos;t supported in this browser.{" "}
            <button type="button" onClick={onSwitchToText} className="underline underline-offset-2">
              Use text chat
            </button>
          </p>
        )}
        {supported && !ttsSupported && (
          <p className="mt-2 text-xs text-[var(--ink-muted)]">
            Spoken responses are unavailable here. Answers will still appear on screen.
          </p>
        )}
      </div>

      {isReady ? (
        <div className="space-y-2">
          <label className="sr-only" htmlFor="voice-draft-transcript">
            Edit transcript before sending
          </label>
          <textarea
            id="voice-draft-transcript"
            value={draftText}
            onChange={(event) => onDraftTextChange(event.target.value)}
            rows={3}
            className="w-full rounded-lg border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm leading-6 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]"
            aria-label="Edit transcript before sending"
          />
          <p className="text-xs text-[var(--ink-muted)]">Review and edit before sending. ChatLaw will not rewrite legal terms for you.</p>
        </div>
      ) : displayTranscript ? (
        <blockquote className="rounded-lg border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm italic text-[var(--foreground)]">
          &ldquo;{displayTranscript}&rdquo;
        </blockquote>
      ) : null}

      {lastAssistantText && state === "idle" && (
        <div className="rounded-lg border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm leading-6 text-[var(--ink-muted)]">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ink-muted)]">Latest answer</p>
          <p className="mt-2 line-clamp-4">{lastAssistantText}</p>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-center gap-2">
        {canListen && !isListening && !isTranscribing && !isThinking && !isReady && (
          <button
            type="button"
            onClick={onStartListening}
            disabled={!supported}
            className="min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            aria-label="Start voice chat listening"
          >
            {isSpeaking || isPaused ? "Interrupt and listen" : "Start listening"}
          </button>
        )}

        {isListening && (
          <>
            <button
              type="button"
              onClick={onStopListening}
              className="min-h-11 rounded-lg border border-[#b42318] bg-[#fef3f2] px-4 text-sm font-semibold text-[#b42318] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Stop voice input recording"
            >
              Stop
            </button>
            <button
              type="button"
              onClick={onCancelListening}
              className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Cancel voice input"
            >
              Cancel
            </button>
          </>
        )}

        {isReady && (
          <>
            <button
              type="button"
              onClick={onConfirmSend}
              disabled={!draftText.trim()}
              className="min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Send voice transcript"
            >
              Send
            </button>
            <button
              type="button"
              onClick={onDiscardDraft}
              className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Discard transcript"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={onStartListening}
              className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Record again"
            >
              Re-record
            </button>
          </>
        )}

        {isSpeaking && (
          <>
            <button type="button" onClick={onPauseSpeaking} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]" aria-label="Pause speech">
              Pause
            </button>
            <button type="button" onClick={onStopSpeaking} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]" aria-label="Stop speech">
              Stop
            </button>
          </>
        )}

        {isPaused && (
          <>
            <button type="button" onClick={onResumeSpeaking} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]" aria-label="Resume speech">
              Resume
            </button>
            <button type="button" onClick={onStopSpeaking} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]" aria-label="Stop speech">
              Stop
            </button>
          </>
        )}

        {state === "idle" && lastAssistantText && ttsSupported && !muted && (
          <button type="button" onClick={onReplaySpeaking} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]" aria-label="Replay spoken response">
            Replay
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-3">
        <label className="flex min-h-11 items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={muted}
            onChange={(event) => onMutedChange(event.target.checked)}
            className="h-4 w-4 rounded border-[var(--line)]"
          />
          <span>Mute spoken responses</span>
        </label>

        <label className="sr-only" htmlFor="voice-chat-language">
          Voice language
        </label>
        <select
          id="voice-chat-language"
          value={language}
          onChange={(event) => onLanguageChange(event.target.value as SpeechLanguageCode)}
          disabled={disabled || isListening || isTranscribing || isThinking || isReady}
          className="min-h-11 rounded-lg border border-[var(--line)] bg-white px-3 text-xs text-[var(--ink-muted)]"
          aria-label="Voice language"
        >
          {languages.map((option) => (
            <option key={option.code} value={option.code}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <p className="text-sm text-[#935a1e]" role="alert">
          {error}{" "}
          <button type="button" onClick={onClearError} className="underline underline-offset-2">
            Dismiss
          </button>
        </p>
      )}
    </section>
  );
}
