"use client";

import { useCallback, useEffect, useRef, useState, type MutableRefObject } from "react";
import { mapSpeechError } from "./errors";
import { DEFAULT_SPEECH_LANGUAGE, isSpeechRecognitionSupported } from "./support";
import { SpeechInputSession } from "./SpeechInputSession";
import { SpeechOutputSession } from "./SpeechOutputSession";
import { prepareTextForSpeech } from "./speechText";
import { mergeTranscript } from "./transcript";
import type { ChatResponse } from "@/lib/api/rag";
import type { SpeechLanguageCode, VoiceChatState } from "./types";
import { canStartVoiceListening, canTransition, voiceStateLabel } from "./voiceState";

export interface VoiceChatSendResult {
  userText: string;
  assistantText: string;
  response: ChatResponse;
}

export interface UseVoiceChatOptions {
  conversationId: string | null;
  /** When true (case ask), listening may start before a conversation id exists. */
  allowWithoutConversation?: boolean;
  language?: SpeechLanguageCode;
  muted?: boolean;
  disabled?: boolean;
  sendMessage: (text: string) => Promise<VoiceChatSendResult>;
  onMessagesAppended?: (result: VoiceChatSendResult) => void;
}

export interface UseVoiceChatResult {
  state: VoiceChatState;
  stateLabel: string;
  supported: boolean;
  ttsSupported: boolean;
  language: SpeechLanguageCode;
  setLanguage: (language: SpeechLanguageCode) => void;
  muted: boolean;
  setMuted: (muted: boolean) => void;
  error: string | null;
  interimText: string;
  draftText: string;
  setDraftText: (text: string) => void;
  lastUserText: string;
  lastAssistantText: string;
  clearError: () => void;
  startListening: () => void;
  stopListening: () => void;
  cancelListening: () => void;
  confirmSend: () => void;
  discardDraft: () => void;
  stopSpeaking: () => void;
  pauseSpeaking: () => void;
  resumeSpeaking: () => void;
  replaySpeaking: () => void;
  reset: () => void;
}

function transitionVoiceState(
  stateRef: MutableRefObject<VoiceChatState>,
  next: VoiceChatState,
  setter: (value: VoiceChatState) => void,
): boolean {
  if (stateRef.current === next) return true;
  if (!canTransition(stateRef.current, next)) return false;
  stateRef.current = next;
  setter(next);
  return true;
}

function forceVoiceState(
  stateRef: MutableRefObject<VoiceChatState>,
  next: VoiceChatState,
  setter: (value: VoiceChatState) => void,
): void {
  stateRef.current = next;
  setter(next);
}

export function useVoiceChat({
  conversationId,
  allowWithoutConversation = false,
  language: initialLanguage = DEFAULT_SPEECH_LANGUAGE,
  muted: initialMuted = false,
  disabled = false,
  sendMessage,
  onMessagesAppended,
}: UseVoiceChatOptions): UseVoiceChatResult {
  const [state, setState] = useState<VoiceChatState>("idle");
  const [muted, setMuted] = useState(initialMuted);
  const [error, setError] = useState<string | null>(null);
  const [interimText, setInterimText] = useState("");
  const [draftText, setDraftText] = useState("");
  const [lastUserText, setLastUserText] = useState("");
  const [lastAssistantText, setLastAssistantText] = useState("");
  const [language, setLanguage] = useState<SpeechLanguageCode>(initialLanguage);

  const stateRef = useRef(state);
  const transcriptRef = useRef("");
  const draftRef = useRef("");
  const inputSessionRef = useRef<SpeechInputSession | null>(null);
  const outputSessionRef = useRef<SpeechOutputSession | null>(null);
  const sendMessageRef = useRef(sendMessage);
  const onMessagesAppendedRef = useRef(onMessagesAppended);
  const mutedRef = useRef(muted);
  const languageRef = useRef(language);
  const conversationIdRef = useRef(conversationId);
  const allowWithoutConversationRef = useRef(allowWithoutConversation);
  const processingRef = useRef(false);
  const skipFinalizeRef = useRef(false);

  const recognitionSupported = typeof window !== "undefined" && isSpeechRecognitionSupported();
  const ttsSupported = typeof window !== "undefined" && Boolean(window.speechSynthesis);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    draftRef.current = draftText;
  }, [draftText]);

  useEffect(() => {
    setLanguage(initialLanguage);
  }, [initialLanguage]);

  useEffect(() => {
    sendMessageRef.current = sendMessage;
    onMessagesAppendedRef.current = onMessagesAppended;
    mutedRef.current = muted;
    languageRef.current = language;
    conversationIdRef.current = conversationId;
    allowWithoutConversationRef.current = allowWithoutConversation;
  }, [sendMessage, onMessagesAppended, muted, language, conversationId, allowWithoutConversation]);

  useEffect(() => {
    outputSessionRef.current = new SpeechOutputSession({
      onStart: () => transitionVoiceState(stateRef, "speaking", setState),
      onEnd: () => {
        const current = stateRef.current;
        if (current === "speaking" || current === "paused" || current === "thinking") {
          forceVoiceState(stateRef, "idle", setState);
        }
      },
      onPause: () => transitionVoiceState(stateRef, "paused", setState),
      onResume: () => transitionVoiceState(stateRef, "speaking", setState),
      onError: (message) => {
        setError(message);
        forceVoiceState(stateRef, "error", setState);
      },
    });

    return () => {
      inputSessionRef.current?.dispose();
      inputSessionRef.current = null;
      outputSessionRef.current?.dispose();
      outputSessionRef.current = null;
    };
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    if (stateRef.current === "error") {
      forceVoiceState(stateRef, "idle", setState);
    }
  }, []);

  const stopSpeakingInternal = useCallback(() => {
    outputSessionRef.current?.stop();
    if (stateRef.current === "speaking" || stateRef.current === "paused") {
      forceVoiceState(stateRef, "idle", setState);
    }
  }, []);

  const runSend = useCallback(async (text: string) => {
    if (processingRef.current) return;
    processingRef.current = true;

    setLastUserText(text);
    setDraftText("");
    draftRef.current = "";
    transcriptRef.current = "";
    setInterimText("");
    forceVoiceState(stateRef, "thinking", setState);

    try {
      const result = await sendMessageRef.current(text);
      onMessagesAppendedRef.current?.(result);
      setLastAssistantText(result.assistantText);

      const spoken = prepareTextForSpeech(result.assistantText);
      if (!spoken || mutedRef.current || !ttsSupported) {
        forceVoiceState(stateRef, "idle", setState);
        return;
      }

      outputSessionRef.current?.speak(spoken, languageRef.current);
    } catch (requestError) {
      const message = requestError instanceof Error
        ? requestError.message
        : "Unable to complete the voice request.";
      setError(message);
      forceVoiceState(stateRef, "error", setState);
    } finally {
      processingRef.current = false;
    }
  }, [ttsSupported]);

  const finalizeTranscript = useCallback(() => {
    const text = transcriptRef.current.trim();
    setInterimText("");
    inputSessionRef.current = null;

    if (!text) {
      setError(mapSpeechError("empty"));
      forceVoiceState(stateRef, "error", setState);
      return;
    }

    setDraftText(text);
    draftRef.current = text;
    setLastUserText(text);
    forceVoiceState(stateRef, "ready_to_send", setState);
  }, []);

  const beginListening = useCallback(() => {
    if (disabled) return;
    if (!recognitionSupported) {
      setError(mapSpeechError("unsupported"));
      forceVoiceState(stateRef, "error", setState);
      return;
    }
    if (!canStartVoiceListening(conversationIdRef.current, allowWithoutConversationRef.current)) {
      setError("Your conversation is still loading. Please try again.");
      forceVoiceState(stateRef, "error", setState);
      return;
    }

    stopSpeakingInternal();
    inputSessionRef.current?.dispose();
    setError(null);
    setInterimText("");
    setDraftText("");
    draftRef.current = "";
    transcriptRef.current = "";
    processingRef.current = false;

    const session = new SpeechInputSession(languageRef.current, {
      onStatus: (status) => {
        if (status === "recording") {
          transitionVoiceState(stateRef, "listening", setState);
        } else if (status === "processing") {
          transitionVoiceState(stateRef, "transcribing", setState);
        } else if (status === "idle") {
          if (skipFinalizeRef.current) {
            skipFinalizeRef.current = false;
            return;
          }
          finalizeTranscript();
        } else if (status === "error") {
          forceVoiceState(stateRef, "error", setState);
        }
      },
      onInterim: (text) => setInterimText(text),
      onFinal: (text) => {
        transcriptRef.current = mergeTranscript(transcriptRef.current, text, 12_000);
      },
      onError: (message) => {
        setError(message);
        forceVoiceState(stateRef, "error", setState);
      },
    });

    inputSessionRef.current = session;
    forceVoiceState(stateRef, "listening", setState);
    session.start();
  }, [disabled, recognitionSupported, stopSpeakingInternal, finalizeTranscript]);

  const startListening = useCallback(() => {
    if (stateRef.current === "speaking" || stateRef.current === "paused") {
      stopSpeakingInternal();
    }
    beginListening();
  }, [beginListening, stopSpeakingInternal]);

  const stopListening = useCallback(() => {
    inputSessionRef.current?.stop();
  }, []);

  const cancelListening = useCallback(() => {
    skipFinalizeRef.current = true;
    inputSessionRef.current?.cancel();
    inputSessionRef.current = null;
    processingRef.current = false;
    setInterimText("");
    transcriptRef.current = "";
    setDraftText("");
    draftRef.current = "";
    forceVoiceState(stateRef, "idle", setState);
  }, []);

  const confirmSend = useCallback(() => {
    if (stateRef.current !== "ready_to_send") return;
    const text = draftRef.current.trim();
    if (!text) {
      setError(mapSpeechError("empty"));
      forceVoiceState(stateRef, "error", setState);
      return;
    }
    void runSend(text);
  }, [runSend]);

  const discardDraft = useCallback(() => {
    setDraftText("");
    draftRef.current = "";
    transcriptRef.current = "";
    setInterimText("");
    forceVoiceState(stateRef, "idle", setState);
  }, []);

  const updateDraftText = useCallback((text: string) => {
    const next = text.slice(0, 12_000);
    setDraftText(next);
    draftRef.current = next;
  }, []);

  const stopSpeaking = useCallback(() => {
    stopSpeakingInternal();
  }, [stopSpeakingInternal]);

  const pauseSpeaking = useCallback(() => {
    if (stateRef.current !== "speaking") return;
    outputSessionRef.current?.pause();
  }, []);

  const resumeSpeaking = useCallback(() => {
    if (stateRef.current !== "paused") return;
    outputSessionRef.current?.resume();
  }, []);

  const replaySpeaking = useCallback(() => {
    if (disabled || mutedRef.current || !ttsSupported) return;
    const spoken = prepareTextForSpeech(lastAssistantText);
    if (!spoken) return;
    stopSpeakingInternal();
    outputSessionRef.current?.speak(spoken, languageRef.current);
  }, [disabled, lastAssistantText, stopSpeakingInternal, ttsSupported]);

  const reset = useCallback(() => {
    skipFinalizeRef.current = true;
    inputSessionRef.current?.cancel();
    inputSessionRef.current = null;
    processingRef.current = false;
    stopSpeakingInternal();
    setInterimText("");
    transcriptRef.current = "";
    setDraftText("");
    draftRef.current = "";
    setError(null);
    forceVoiceState(stateRef, "idle", setState);
  }, [stopSpeakingInternal]);

  return {
    state,
    stateLabel: voiceStateLabel(state),
    supported: recognitionSupported,
    ttsSupported,
    language,
    setLanguage,
    muted,
    setMuted,
    error,
    interimText,
    draftText,
    setDraftText: updateDraftText,
    lastUserText,
    lastAssistantText,
    clearError,
    startListening,
    stopListening,
    cancelListening,
    confirmSend,
    discardDraft,
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
    replaySpeaking,
    reset,
  };
}
