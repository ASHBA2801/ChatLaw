"use client";

import { MicIcon, StopIcon } from "@/components/chat/ChatIcons";
import type { SpeechInputStatus, SpeechLanguageCode } from "@/lib/speech/types";
import { getEnabledSpeechLanguages, getSpeechRecognitionUnavailableMessage } from "@/lib/speech/support";

export interface VoiceInputControlsProps {
  status: SpeechInputStatus;
  supported: boolean;
  language: SpeechLanguageCode;
  onLanguageChange: (language: SpeechLanguageCode) => void;
  error: string | null;
  interimText: string;
  disabled?: boolean;
  languageSelectId?: string;
  /** "composer" is the borderless icon style used inside the chat composer. */
  variant?: "default" | "composer";
  onStart: () => void;
  onStop: () => void;
  onCancel: () => void;
  onClearError: () => void;
}

function statusLabel(status: SpeechInputStatus): string {
  switch (status) {
    case "starting":
      return "Starting mic…";
    case "recording":
      return "Recording…";
    case "processing":
      return "Transcribing…";
    case "unsupported":
      return "Voice unavailable";
    case "error":
      return "Voice error";
    default:
      return "";
  }
}

function buttonLabel(status: SpeechInputStatus, supported: boolean): string {
  if (!supported || status === "unsupported") return "Voice input unavailable";
  if (status === "starting") return "Cancel voice input";
  if (status === "recording") return "Stop voice input";
  if (status === "processing") return "Transcribing voice input";
  return "Start voice input";
}

export default function VoiceInputControls({
  status,
  supported,
  language,
  onLanguageChange,
  error,
  interimText,
  disabled = false,
  languageSelectId = "chatlaw-speech-language",
  variant = "default",
  onStart,
  onStop,
  onCancel,
  onClearError,
}: VoiceInputControlsProps) {
  const isStarting = status === "starting";
  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  // Starting looks like recording at once, so a tap never seems ignored while the mic opens.
  const isActive = isStarting || isRecording;
  const languages = getEnabledSpeechLanguages();
  const composer = variant === "composer";

  function handleMicClick() {
    if (!supported || status === "unsupported") return;
    if (isActive) {
      onStop();
      return;
    }
    if (isProcessing) return;
    onClearError();
    onStart();
  }

  return (
    <div className={composer ? "flex min-w-0 flex-wrap items-center gap-x-1" : "flex min-w-0 flex-col gap-1"}>
      <div className={`flex items-center ${composer ? "gap-1" : "gap-2"}`}>
        <button
          type="button"
          onClick={handleMicClick}
          disabled={disabled || !supported || status === "unsupported" || isProcessing}
          className={`inline-flex items-center justify-center text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] disabled:cursor-not-allowed disabled:opacity-50 ${
            composer
              ? `h-11 w-11 rounded-full ${
                  isActive
                    ? "bg-[var(--warn-bg)] text-[var(--warn)]"
                    : "text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)]"
                }`
              : `min-h-11 min-w-11 rounded-sm border ${
                  isActive
                    ? "border-[var(--warn)] bg-[var(--warn-bg)] text-[var(--warn)]"
                    : "border-[var(--line)] text-[var(--foreground)] hover:border-[var(--accent)]"
                }`
          }`}
          aria-label={buttonLabel(status, supported)}
          aria-pressed={isActive}
          title={buttonLabel(status, supported)}
        >
          {isActive ? (
            <StopIcon className={`h-5 w-5 ${isStarting ? "animate-pulse" : ""}`} />
          ) : (
            <MicIcon className="h-5 w-5" />
          )}
        </button>

        {composer ? null : (
          <>
          <label className="sr-only" htmlFor={languageSelectId}>
            Voice input language
          </label>
          <select
            id={languageSelectId}
            value={language}
            onChange={(event) => onLanguageChange(event.target.value as SpeechLanguageCode)}
            disabled={disabled || isActive || isProcessing || !supported}
            className="hidden h-11 max-w-[9.5rem] rounded-sm border border-[var(--line)] bg-[var(--surface)] px-2 text-xs text-[var(--ink-muted)] sm:block"
            aria-label="Voice input language"
          >
            {languages.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
          </>
        )}

        {(isActive || isProcessing) && (
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary btn-sm"
          >
            Cancel
          </button>
        )}
      </div>

      <div className={composer ? "min-w-0 px-1" : "min-h-4 px-1"} aria-live="polite">
        {status !== "idle" && status !== "error" && status !== "unsupported" && (
          <p className="text-xs text-[var(--ink-muted)]">
            <span className={isRecording ? "font-medium text-[var(--warn)]" : ""}>
              {isRecording ? "Recording…" : statusLabel(status)}
            </span>
            {isRecording && interimText ? <span className="ml-2 italic">“{interimText}”</span> : null}
          </p>
        )}
        {status === "unsupported" && (
          <p className="text-xs text-[var(--ink-muted)]">{getSpeechRecognitionUnavailableMessage()}</p>
        )}
        {error && (
          <p className="text-xs text-[var(--warn)]" role="alert">
            {error}{" "}
            <button type="button" onClick={onClearError} className="underline underline-offset-2">
              Dismiss
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
