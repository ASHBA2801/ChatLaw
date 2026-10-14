"use client";

import { useState, type ReactNode } from "react";

import type { SpeechLanguageCode, VoiceChatState } from "@/lib/speech/types";
import { getEnabledSpeechLanguages } from "@/lib/speech/support";
import { KeyboardIcon, MicIcon, PauseIcon, PlayIcon, SlidersIcon, SpeakerIcon, StopIcon } from "@/components/chat/ChatIcons";

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

function VoiceOrb({
  state,
  audioLevel = 0,
  size,
}: {
  state: VoiceChatState;
  audioLevel?: number;
  size: "lg" | "sm";
}) {
  const listening = state === "listening";
  const speaking = state === "speaking";
  const busy = state === "transcribing" || state === "thinking";
  const error = state === "error";
  const scale = listening ? 1 + audioLevel * 0.25 : 1;
  const dims = size === "lg" ? "h-40 w-40" : "h-11 w-11";
  const core = size === "lg" ? "h-24 w-24" : "h-6 w-6";
  const tone = error
    ? "bg-[var(--warn-bg)] text-[var(--warn)]"
    : listening
      ? "bg-[var(--warn-bg)] text-[var(--warn)]"
      : "bg-[var(--accent-soft)] text-[var(--accent)]";
  const coreTone = error || listening ? "bg-[var(--warn)]/20" : "bg-[var(--accent)]/20";
  const bars = size === "lg" ? "h-8 w-2" : "h-3 w-0.5";

  return (
    <div
      className={`relative mx-auto flex shrink-0 items-center justify-center rounded-full transition-transform duration-100 ${dims} ${tone}`}
      style={{ transform: `scale(${scale})` }}
      aria-hidden="true"
    >
      <div
        className={`rounded-full ${core} ${coreTone} ${listening || speaking || busy ? "animate-pulse" : ""}`}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        {listening || speaking ? (
          <span className="flex items-center gap-1.5">
            <span className={`${bars} rounded-full bg-current voice-bar`} />
            <span className={`${bars} rounded-full bg-current voice-bar voice-bar-delay-1 ${size === "lg" ? "!h-12" : "!h-4"}`} />
            <span className={`${bars} rounded-full bg-current voice-bar voice-bar-delay-2`} />
          </span>
        ) : (
          <MicIcon className={size === "lg" ? "h-10 w-10" : "h-5 w-5"} />
        )}
      </div>
    </div>
  );
}

function SettingToggle({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="inline-flex min-h-9 cursor-pointer items-center rounded-full border border-[var(--line)] px-3.5 text-xs font-medium text-[var(--ink-muted)] hover:bg-[var(--fill)] has-[:checked]:border-[var(--accent-mid)] has-[:checked]:bg-[var(--accent-soft)] has-[:checked]:text-[var(--accent)] has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-[var(--focus)]">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="sr-only" />
      {children}
    </label>
  );
}

export interface VoiceChatPanelProps {
  state: VoiceChatState;
  stateLabel: string;
  supported: boolean;
  ttsSupported: boolean;
  /** Voice language follows the chat language chosen in the header. */
  language: SpeechLanguageCode;
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
  /** `true` once the thread has messages: the panel docks under it like the text composer. */
  compact?: boolean;
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
  compact = false,
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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const languageLabel = getEnabledSpeechLanguages().find((option) => option.code === language)?.label ?? language;
  const nativeText = getNativeVoiceText(language);
  const isReady = state === "ready_to_send";
  const displayTranscript = isReady ? draftText : interimText || lastUserText;
  const canListen = supported && !disabled && (state === "idle" || state === "error" || state === "speaking" || state === "paused");
  const isListening = state === "listening";
  const isTranscribing = state === "transcribing";
  const isThinking = state === "thinking";
  const isSpeaking = state === "speaking";
  const isPaused = state === "paused";
  const statusText = isSpeaking ? nativeText.speaking : stateLabel;

  const btn = compact ? "!min-h-10 !px-4 !text-sm" : "!min-h-12 !px-6 !text-[15px]";
  const secondary = `btn-secondary ${btn}`;
  const primary = `btn-primary ${btn}`;

  const actions = (
    <div className={`flex flex-wrap items-center gap-2 ${compact ? "w-full justify-center sm:w-auto" : "justify-center"}`}>
      {canListen && !isListening && !isTranscribing && !isThinking && !isReady && (
        <button
          type="button"
          onClick={onStartListening}
          disabled={!supported}
          className={`${primary} disabled:opacity-50`}
          aria-label="Start voice chat listening"
        >
          <MicIcon className="h-5 w-5" />
          <span>{isSpeaking || isPaused ? "Interrupt & speak" : nativeText.start}</span>
        </button>
      )}

      {isListening && (
        <>
          <button
            type="button"
            onClick={onStopListening}
            className={`inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--warn)] font-semibold text-white hover:opacity-90 ${compact ? "min-h-10 px-4 text-sm" : "min-h-12 px-6 text-[15px]"}`}
            aria-label="Stop voice input recording"
          >
            <StopIcon className="h-5 w-5" />
            <span>{nativeText.stop}</span>
          </button>
          <button type="button" onClick={onCancelListening} className={secondary} aria-label="Cancel voice input">
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
            className={`${primary} disabled:opacity-50`}
            aria-label="Send voice transcript"
          >
            Send question
          </button>
          <button type="button" onClick={onStartListening} className={secondary} aria-label="Record again">
            Re-record
          </button>
          <button type="button" onClick={onDiscardDraft} className={secondary} aria-label="Discard transcript">
            Discard
          </button>
        </>
      )}

      {isSpeaking && (
        <>
          <button type="button" onClick={onPauseSpeaking} className={secondary} aria-label="Pause speech">
            <PauseIcon className="h-4 w-4" /> Pause
          </button>
          <button type="button" onClick={onStopSpeaking} className={secondary} aria-label="Stop speech">
            <StopIcon className="h-4 w-4" /> Stop
          </button>
        </>
      )}

      {isPaused && (
        <>
          <button type="button" onClick={onResumeSpeaking} className={secondary} aria-label="Resume speech">
            <PlayIcon className="h-4 w-4" /> Resume
          </button>
          <button type="button" onClick={onStopSpeaking} className={secondary} aria-label="Stop speech">
            <StopIcon className="h-4 w-4" /> Stop
          </button>
        </>
      )}

      {state === "idle" && lastAssistantText && ttsSupported && !muted && (
        <button type="button" onClick={onReplaySpeaking} className={secondary} aria-label="Replay spoken response">
          <SpeakerIcon className="h-4 w-4" /> Replay answer
        </button>
      )}
    </div>
  );

  const settings = (
    <div className={`flex flex-wrap items-center gap-2 ${compact ? "" : "justify-center"}`}>
      <SettingToggle checked={continuousMode} onChange={(value) => onContinuousModeChange?.(value)}>
        Continuous conversation
      </SettingToggle>
      <SettingToggle checked={autoSend} onChange={(value) => onAutoSendChange?.(value)}>
        Direct voice-to-voice
      </SettingToggle>
      <SettingToggle checked={muted} onChange={onMutedChange}>
        Mute voice
      </SettingToggle>
      <span className="inline-flex min-h-9 items-center px-1 text-xs text-[var(--ink-muted)]">
        Language: {languageLabel} (change it in the top bar)
      </span>
    </div>
  );

  const review = isReady ? (
    <div className="w-full space-y-2 text-left">
      <label className="text-xs font-semibold text-[var(--ink-muted)]" htmlFor="voice-draft-transcript">
        Review your question before sending
      </label>
      <textarea
        id="voice-draft-transcript"
        value={draftText}
        onChange={(event) => onDraftTextChange(event.target.value)}
        rows={3}
        className="w-full resize-none rounded-2xl border border-[var(--line)] bg-[var(--background)] px-4 py-3 text-[15px] leading-6 outline-none focus:border-[var(--accent)]"
        aria-label="Edit transcript before sending"
      />
    </div>
  ) : null;

  const autoplayNotice = autoplayBlocked ? (
    <div className="w-full rounded-2xl border border-[var(--accent-mid)] bg-[var(--accent-soft)] p-3 text-center">
      <p className="mb-2 text-sm font-semibold text-[var(--accent)]">Your browser needs a tap before it can play audio</p>
      <button type="button" onClick={onUnlockAutoplay} className="btn-primary">
        <SpeakerIcon className="h-4 w-4" />
        <span>{nativeText.listen}</span>
      </button>
    </div>
  ) : null;

  const errorNotice = error ? (
    <div
      className="flex w-full items-center justify-between gap-3 rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] px-4 py-3 text-left text-sm text-[var(--warn)]"
      role="alert"
    >
      <p>{error}</p>
      <button type="button" onClick={onClearError} className="-my-2 inline-flex min-h-10 shrink-0 items-center px-2 font-semibold underline underline-offset-2">
        Retry
      </button>
    </div>
  ) : null;

  if (compact) {
    return (
      <section
        className="w-full rounded-3xl border border-[var(--line-strong)] bg-[var(--surface)] p-3 shadow-[var(--shadow-soft)]"
        aria-label="ChatLaw voice assistant"
      >
        <div className="flex flex-wrap items-center gap-x-3 gap-y-3">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <VoiceOrb state={state} audioLevel={audioLevel} size="sm" />
            <div className="min-w-0 flex-1" aria-live="polite">
              <p className="truncate text-sm font-semibold">{statusText}</p>
              {!isReady && displayTranscript ? (
                <p className="truncate text-xs text-[var(--ink-muted)]">&ldquo;{displayTranscript}&rdquo;</p>
              ) : null}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={() => setSettingsOpen((value) => !value)}
              aria-expanded={settingsOpen}
              aria-label="Voice settings"
              title="Voice settings"
              className={`inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-[var(--fill)] ${settingsOpen ? "bg-[var(--fill)] text-[var(--foreground)]" : "text-[var(--ink-muted)]"}`}
            >
              <SlidersIcon className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={onSwitchToText}
              aria-label="Switch to text mode"
              title="Type instead"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)]"
            >
              <KeyboardIcon className="h-5 w-5" />
            </button>
          </div>
          {actions}
        </div>
        {review || autoplayNotice || errorNotice || settingsOpen ? (
          <div className="mt-3 space-y-3">
            {review}
            {autoplayNotice}
            {settingsOpen ? <div className="border-t border-[var(--line)] pt-3">{settings}</div> : null}
            {errorNotice}
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section
      className="mx-auto flex w-full max-w-xl flex-col items-center gap-6 text-center"
      aria-label="ChatLaw voice assistant"
    >
      <VoiceOrb state={state} audioLevel={audioLevel} size="lg" />

      <div aria-live="polite">
        <p className="text-2xl font-semibold tracking-tight">{statusText}</p>
        {state === "idle" && !displayTranscript ? (
          <p className="mt-2 text-[15px] leading-7 text-[var(--ink-muted)]">
            Tap the microphone and ask your question in your own words.
          </p>
        ) : null}
      </div>

      {review ??
        (displayTranscript ? (
          <p className="max-w-md text-[15px] italic leading-7 text-[var(--foreground)]">&ldquo;{displayTranscript}&rdquo;</p>
        ) : null)}

      {lastAssistantText && state === "idle" && !isListening ? (
        <p className="line-clamp-3 max-w-md text-sm leading-6 text-[var(--ink-muted)]">{lastAssistantText}</p>
      ) : null}

      {autoplayNotice}
      {actions}
      {errorNotice}

      <div className="w-full border-t border-[var(--line)] pt-5">{settings}</div>

      <button
        type="button"
        onClick={onSwitchToText}
        className="inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)]"
        aria-label="Switch to text mode"
      >
        <KeyboardIcon className="h-5 w-5" />
        Type instead
      </button>
    </section>
  );
}
