"use client";

import type { SpeechLanguageCode, VoiceChatState } from "@/lib/speech/types";
import { getEnabledSpeechLanguages } from "@/lib/speech/support";

const NATIVE_VOICE_LABELS: Record<string, { start: string; stop: string; listen: string; speaking: string }> = {
  ta: {
    start: "பேச தொடங்குங்கள்",
    stop: "பேசி முடித்தேன்",
    listen: "பதிலை கேளுங்கள்",
    speaking: "ChatLaw பேசுகிறது…",
  },
  hi: {
    start: "बोलना शुरू करें",
    stop: "बोलना पूरा हुआ",
    listen: "उत्तर सुनें",
    speaking: "ChatLaw बोल रहा है…",
  },
  te: {
    start: "మాట్లాడటం ప్రారంభించండి",
    stop: "మాట్లాడటం పూర్తయింది",
    listen: "సమాధానం వినండి",
    speaking: "ChatLaw మాట్లాడుతోంది…",
  },
  kn: {
    start: "ಮಾತನಾಡಲು ಪ್ರಾರಂಭಿಸಿ",
    stop: "ಮಾತನಾಡುವುದು ಮುಗಿಯಿತು",
    listen: "ಉತ್ತರವನ್ನು ಕೇಳಿ",
    speaking: "ChatLaw ಮಾತನಾಡುತ್ತಿದೆ…",
  },
  ml: {
    start: "സംസാരിച്ചു തുടങ്ങൂ",
    stop: "സംസാരം കഴിഞ്ഞു",
    listen: "മറുപടി കേൾക്കൂ",
    speaking: "ChatLaw സംസാരിക്കുന്നു…",
  },
  mr: {
    start: "बोलण्यास प्रारंभ करा",
    stop: "बोलणे पूर्ण झाले",
    listen: "उत्तर ऐका",
    speaking: "ChatLaw बोलत आहे…",
  },
  bn: {
    start: "কথা বলা শুরু করুন",
    stop: "কথা বলা শেষ",
    listen: "উত্তর শুনুন",
    speaking: "ChatLaw কথা বলছে…",
  },
  gu: {
    start: "બોલવાનું શરૂ કરો",
    stop: "બોલવાનું પૂરું થયું",
    listen: "જવાબ સાંભળો",
    speaking: "ChatLaw બોલી રહ્યું છે…",
  },
  pa: {
    start: "ਬੋਲਣਾ ਸ਼ੁਰੂ ਕਰੋ",
    stop: "ਬੋਲਣਾ ਪੂਰਾ ਹੋਇਆ",
    listen: "ਜਵਾਬ ਸੁਣੋ",
    speaking: "ChatLaw ਬੋਲ ਰਿਹਾ ਹੈ…",
  },
  ur: {
    start: "بولنا شروع کریں",
    stop: "بولنا ختم ہوا",
    listen: "جواب سنیں",
    speaking: "ChatLaw بول رہا ہے…",
  },
  en: {
    start: "Tap & Speak",
    stop: "Done Speaking",
    listen: "Listen to Answer",
    speaking: "ChatLaw is speaking…",
  },
};

function getNativeVoiceText(langCode: string) {
  const primary = langCode.split("-")[0]?.toLowerCase() || "en";
  return NATIVE_VOICE_LABELS[primary] || NATIVE_VOICE_LABELS.en;
}

function VoiceOrb({ state, audioLevel = 0 }: { state: VoiceChatState; audioLevel?: number }) {
  const active = state === "listening" || state === "speaking";
  const paused = state === "paused";
  const error = state === "error";
  const reviewing = state === "ready_to_send";
  const scale = state === "listening" ? 1 + audioLevel * 0.4 : 1;

  return (
    <div
      className={`relative mx-auto flex h-32 w-32 items-center justify-center rounded-full border-4 transition-transform duration-100 ${
        error
          ? "border-[var(--warn-line)] bg-[var(--warn-bg)] shadow-md"
          : reviewing
            ? "border-[var(--warm)] bg-[#fff8ef] shadow-md"
            : active
              ? "border-[var(--forest)] bg-[var(--signal-soft)] shadow-lg"
              : "border-[var(--line)] bg-white shadow-sm"
      }`}
      style={{ transform: `scale(${scale})` }}
      aria-hidden="true"
    >
      <div
        className={`h-20 w-20 rounded-full transition-all ${
          state === "listening"
            ? "animate-pulse bg-[#b42318]/25"
            : state === "speaking"
              ? "animate-pulse bg-[var(--forest)]/25"
              : paused
                ? "bg-[var(--ink-muted)]/15"
                : reviewing
                  ? "bg-[var(--warm)]/20"
                  : "bg-[var(--forest)]/10"
        }`}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        {state === "listening" ? (
          <div className="flex items-center gap-1">
            <span className="h-6 w-1.5 rounded-full bg-[#b42318] animate-bounce" />
            <span className="h-10 w-1.5 rounded-full bg-[#b42318] animate-pulse" />
            <span className="h-6 w-1.5 rounded-full bg-[#b42318] animate-bounce" />
          </div>
        ) : state === "speaking" ? (
          <span className="flex items-end gap-1.5" title="Speaking indicator">
            <span className="h-4 w-1.5 rounded-full bg-[var(--forest)] voice-bar" />
            <span className="h-7 w-1.5 rounded-full bg-[var(--forest)] voice-bar voice-bar-delay-1" />
            <span className="h-5 w-1.5 rounded-full bg-[var(--forest)] voice-bar voice-bar-delay-2" />
          </span>
        ) : (
          <svg className="h-10 w-10 text-[var(--forest)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeLinecap="round" />
            <line x1="12" x2="12" y1="19" y2="22" strokeLinecap="round" />
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
  autoSend?: boolean;
  onAutoSendChange?: (autoSend: boolean) => void;
  continuousMode?: boolean;
  onContinuousModeChange?: (continuous: boolean) => void;
  autoplayBlocked?: boolean;
  onUnlockAutoplay?: () => void;
  audioLevel?: number;
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
  autoSend = true,
  onAutoSendChange,
  continuousMode = true,
  onContinuousModeChange,
  autoplayBlocked = false,
  onUnlockAutoplay,
  audioLevel = 0,
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
  const nativeText = getNativeVoiceText(language);
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
      className="mx-auto flex w-full max-w-xl flex-col gap-5 rounded-md border-2 border-[var(--line)] bg-white p-5 sm:p-7 shadow-sm"
      aria-label="ChatLaw Voice Assistant"
    >
      <div className="flex items-center justify-between gap-3 border-b border-[var(--line)] pb-3">
        <div>
          <h3 className="text-lg font-bold text-[var(--foreground)] flex items-center gap-2">
            <span>🎙️</span>
            <span>ChatLaw Voice Assistant</span>
          </h3>
          <p className="text-xs text-[var(--ink-muted)] mt-0.5">
            Voice-to-Voice legal assistance in Indian languages with authentic legal reasoning.
          </p>
        </div>
        <button
          type="button"
          onClick={onSwitchToText}
          className="min-h-11 rounded-sm border border-[var(--line)] px-3 text-xs font-semibold hover:border-[var(--forest)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
          aria-label="Switch to text mode"
        >
          ⌨️ Text mode
        </button>
      </div>

      <VoiceOrb state={state} audioLevel={audioLevel} />

      <div className="text-center" aria-live="polite">
        <p className="text-base font-bold text-[var(--foreground)]">
          {isSpeaking ? nativeText.speaking : stateLabel}
        </p>

        {autoplayBlocked && (
          <div className="mt-3 rounded-sm border-2 border-[var(--signal)] bg-[var(--signal-soft)] p-3 text-center">
            <p className="text-sm font-semibold text-[var(--signal)] mb-2">
              🔊 Autoplay requires user permission
            </p>
            <button
              type="button"
              onClick={onUnlockAutoplay}
              className="inline-flex min-h-11 items-center gap-2 rounded-sm bg-[var(--forest)] px-5 text-sm font-bold text-white shadow-sm hover:opacity-95"
            >
              <span>🔊</span>
              <span>{nativeText.listen} (Tap to Listen)</span>
            </button>
          </div>
        )}
      </div>

      {isReady ? (
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-[var(--ink-muted)]" htmlFor="voice-draft-transcript">
            Review your question before sending:
          </label>
          <textarea
            id="voice-draft-transcript"
            value={draftText}
            onChange={(event) => onDraftTextChange(event.target.value)}
            rows={3}
            className="w-full rounded-sm border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm leading-6 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]"
            aria-label="Edit transcript before sending"
          />
        </div>
      ) : displayTranscript ? (
        <blockquote className="rounded-sm border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm italic text-[var(--foreground)]">
          &ldquo;{displayTranscript}&rdquo;
        </blockquote>
      ) : null}

      {lastAssistantText && state === "idle" && !isListening && (
        <div className="rounded-sm border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-sm leading-6 text-[var(--ink-muted)]">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--ink-muted)]">Latest spoken response</p>
          <p className="mt-1 line-clamp-3 text-[var(--foreground)]">{lastAssistantText}</p>
        </div>
      )}

      {/* Primary Voice Actions with High Visibility & Native Indian Language Labels */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {canListen && !isListening && !isTranscribing && !isThinking && !isReady && (
          <button
            type="button"
            onClick={onStartListening}
            disabled={!supported}
            className="min-h-14 min-w-[200px] rounded-sm bg-[var(--forest)] px-6 text-base font-bold text-white shadow-md hover:opacity-95 disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)] flex items-center justify-center gap-2"
            aria-label="Start voice chat listening"
          >
            <span>🎙️</span>
            <span>{isSpeaking || isPaused ? "Interrupt & Speak" : `${nativeText.start}`}</span>
          </button>
        )}

        {isListening && (
          <>
            <button
              type="button"
              onClick={onStopListening}
              className="min-h-14 min-w-[180px] rounded-sm border-2 border-[#b42318] bg-[#fef3f2] px-6 text-base font-bold text-[#b42318] shadow-md hover:bg-[#fee4e2] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)] flex items-center justify-center gap-2"
              aria-label="Stop voice input recording"
            >
              <span>⏹️</span>
              <span>{nativeText.stop}</span>
            </button>
            <button
              type="button"
              onClick={onCancelListening}
              className="min-h-14 rounded-sm border border-[var(--line)] px-5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
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
              className="min-h-14 rounded-sm bg-[var(--forest)] px-6 text-base font-bold text-white shadow-md disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
              aria-label="Send voice transcript"
            >
              Send Question
            </button>
            <button
              type="button"
              onClick={onDiscardDraft}
              className="min-h-14 rounded-sm border border-[var(--line)] px-5 text-sm font-semibold"
              aria-label="Discard transcript"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={onStartListening}
              className="min-h-14 rounded-sm border border-[var(--line)] px-5 text-sm font-semibold"
              aria-label="Record again"
            >
              Re-record
            </button>
          </>
        )}

        {isSpeaking && (
          <>
            <button
              type="button"
              onClick={onPauseSpeaking}
              className="min-h-12 rounded-sm border border-[var(--line)] px-4 text-sm font-semibold"
              aria-label="Pause speech"
            >
              ⏸ Pause
            </button>
            <button
              type="button"
              onClick={onStopSpeaking}
              className="min-h-12 rounded-sm border border-[var(--line)] px-4 text-sm font-semibold"
              aria-label="Stop speech"
            >
              ⏹ Stop
            </button>
            <button
              type="button"
              onClick={onStartListening}
              className="min-h-12 rounded-sm bg-[#b42318] px-4 text-sm font-bold text-white shadow-sm"
              aria-label="Interrupt and speak"
            >
              🎙️ Interrupt & Speak
            </button>
          </>
        )}

        {isPaused && (
          <>
            <button
              type="button"
              onClick={onResumeSpeaking}
              className="min-h-12 rounded-sm border border-[var(--line)] px-4 text-sm font-semibold"
              aria-label="Resume speech"
            >
              ▶ Resume
            </button>
            <button
              type="button"
              onClick={onStopSpeaking}
              className="min-h-12 rounded-sm border border-[var(--line)] px-4 text-sm font-semibold"
              aria-label="Stop speech"
            >
              ⏹ Stop
            </button>
          </>
        )}

        {state === "idle" && lastAssistantText && ttsSupported && !muted && (
          <button
            type="button"
            onClick={onReplaySpeaking}
            className="min-h-12 rounded-sm border border-[var(--line)] px-4 text-sm font-semibold hover:border-[var(--forest)]"
            aria-label="Replay spoken response"
          >
            🔊 Replay Spoken Answer
          </button>
        )}
      </div>

      {/* Settings & Voice Conversation Modes */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[var(--line)] pt-4 text-sm">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={continuousMode}
              onChange={(e) => onContinuousModeChange?.(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--line)] text-[var(--forest)]"
            />
            <span className="text-xs font-semibold">Continuous conversation</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoSend}
              onChange={(e) => onAutoSendChange?.(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--line)] text-[var(--forest)]"
            />
            <span className="text-xs font-semibold">Direct Voice-to-Voice</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={muted}
              onChange={(event) => onMutedChange(event.target.checked)}
              className="h-4 w-4 rounded border-[var(--line)] text-[var(--forest)]"
            />
            <span className="text-xs font-semibold">Mute voice</span>
          </label>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-[var(--ink-muted)]" htmlFor="voice-chat-language">
            Language:
          </label>
          <select
            id="voice-chat-language"
            value={language}
            onChange={(event) => onLanguageChange(event.target.value as SpeechLanguageCode)}
            disabled={disabled || isListening || isTranscribing || isThinking || isReady}
            className="min-h-10 rounded-sm border border-[var(--line)] bg-white px-3 text-xs font-medium text-[var(--foreground)]"
            aria-label="Voice language"
          >
            {languages.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-sm border border-red-200 bg-red-50 p-3 text-xs text-red-700 flex items-center justify-between" role="alert">
          <p>{error}</p>
          <button type="button" onClick={onClearError} className="underline font-bold ml-2">
            Retry
          </button>
        </div>
      )}
    </section>
  );
}
