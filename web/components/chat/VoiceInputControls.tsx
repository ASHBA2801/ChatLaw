"use client";

import type { SpeechInputStatus, SpeechLanguageCode } from "@/lib/speech/types";
import { getEnabledSpeechLanguages, getSpeechRecognitionUnavailableMessage } from "@/lib/speech/support";

function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" />
      <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
      <path d="M12 18v3" strokeLinecap="round" />
    </svg>
  );
}

function StopIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
      <rect x="7" y="7" width="10" height="10" rx="1.5" />
    </svg>
  );
}

export interface VoiceInputControlsProps {
  status: SpeechInputStatus;
  supported: boolean;
  language: SpeechLanguageCode;
  onLanguageChange: (language: SpeechLanguageCode) => void;
  error: string | null;
  interimText: string;
  disabled?: boolean;
  languageSelectId?: string;
  onStart: () => void;
  onStop: () => void;
  onCancel: () => void;
  onClearError: () => void;
}

function statusLabel(status: SpeechInputStatus): string {
  switch (status) {
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
  onStart,
  onStop,
  onCancel,
  onClearError,
}: VoiceInputControlsProps) {
  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  const languages = getEnabledSpeechLanguages();

  function handleMicClick() {
    if (!supported || status === "unsupported") return;
    if (isRecording) {
      onStop();
      return;
    }
    if (isProcessing) return;
    onClearError();
    onStart();
  }

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleMicClick}
          disabled={disabled || !supported || status === "unsupported" || isProcessing}
          className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-sm border text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)] disabled:cursor-not-allowed disabled:opacity-50 ${
            isRecording
              ? "border-[#b42318] bg-[#fef3f2] text-[#b42318]"
              : "border-[var(--line)] text-[var(--foreground)] hover:border-[var(--forest)]"
          }`}
          aria-label={buttonLabel(status, supported)}
          aria-pressed={isRecording}
          title={buttonLabel(status, supported)}
        >
          {isRecording ? <StopIcon className="h-5 w-5" /> : <MicIcon className="h-5 w-5" />}
        </button>

        <label className="sr-only" htmlFor={languageSelectId}>
          Voice input language
        </label>
        <select
          id={languageSelectId}
          value={language}
          onChange={(event) => onLanguageChange(event.target.value as SpeechLanguageCode)}
          disabled={disabled || isRecording || isProcessing || !supported}
          className="hidden h-11 max-w-[9.5rem] rounded-sm border border-[var(--line)] bg-white px-2 text-xs text-[var(--ink-muted)] sm:block"
          aria-label="Voice input language"
        >
          {languages.map((option) => (
            <option key={option.code} value={option.code}>
              {option.label}
            </option>
          ))}
        </select>

        {(isRecording || isProcessing) && (
          <button
            type="button"
            onClick={onCancel}
            className="min-h-11 rounded-sm border border-[var(--line)] px-3 text-xs font-medium text-[var(--ink-muted)] hover:border-[var(--forest)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
          >
            Cancel
          </button>
        )}
      </div>

      <div className="min-h-4 px-1" aria-live="polite">
        {status !== "idle" && status !== "error" && (
          <p className="text-xs text-[var(--ink-muted)]">
            <span className={isRecording ? "font-medium text-[#b42318]" : ""}>
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
