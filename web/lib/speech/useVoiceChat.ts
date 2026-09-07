"use client";

import { useCallback, useEffect, useRef, useState, type MutableRefObject } from "react";
import { mapSpeechError } from "./errors";
import { DEFAULT_SPEECH_LANGUAGE, isBraveBrowser, isSpeechRecognitionSupported } from "./support";
import { AudioRecorderSession, isAudioRecordingSupported } from "./audioRecorder";
import { SpeechInputSession } from "./SpeechInputSession";
import { SpeechOutputSession } from "./SpeechOutputSession";
import { prepareTextForSpeech } from "./speechText";
import { transcribeAudio } from "./transcribe";
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
  autoSend?: boolean;
  continuousMode?: boolean;
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
  autoSend: boolean;
  setAutoSend: (autoSend: boolean) => void;
  continuousMode: boolean;
  setContinuousMode: (continuous: boolean) => void;
  autoplayBlocked: boolean;
  unlockAutoplay: () => void;
  audioLevel: number;
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
  autoSend: initialAutoSend = true,
  continuousMode: initialContinuousMode = true,
  sendMessage,
  onMessagesAppended,
}: UseVoiceChatOptions): UseVoiceChatResult {
  const [state, setState] = useState<VoiceChatState>("idle");
  const [muted, setMuted] = useState(initialMuted);
  const [autoSend, setAutoSend] = useState(initialAutoSend);
  const [continuousMode, setContinuousMode] = useState(initialContinuousMode);
  const [autoplayBlocked, setAutoplayBlocked] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
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
  const audioRecorderRef = useRef<AudioRecorderSession | null>(null);
  const outputSessionRef = useRef<SpeechOutputSession | null>(null);
  const sendMessageRef = useRef(sendMessage);
  const onMessagesAppendedRef = useRef(onMessagesAppended);
  const mutedRef = useRef(muted);
  const autoSendRef = useRef(autoSend);
  const continuousModeRef = useRef(continuousMode);
  const languageRef = useRef(language);
  const conversationIdRef = useRef(conversationId);
  const allowWithoutConversationRef = useRef(allowWithoutConversation);
  const processingRef = useRef(false);
  const skipFinalizeRef = useRef(false);
  const continuousTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const recognitionSupported =
    typeof window !== "undefined" &&
    (isSpeechRecognitionSupported() || isAudioRecordingSupported());
  const ttsSupported =
    typeof window !== "undefined" &&
    (Boolean(window.speechSynthesis) || typeof fetch === "function");

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
    autoSendRef.current = autoSend;
    continuousModeRef.current = continuousMode;
    languageRef.current = language;
    conversationIdRef.current = conversationId;
    allowWithoutConversationRef.current = allowWithoutConversation;
  }, [sendMessage, onMessagesAppended, muted, autoSend, continuousMode, language, conversationId, allowWithoutConversation]);

  const stopSpeakingInternal = useCallback(() => {
    outputSessionRef.current?.stop();
    setAutoplayBlocked(false);
    if (stateRef.current === "speaking" || stateRef.current === "paused") {
      forceVoiceState(stateRef, "idle", setState);
    }
  }, []);

  const clearContinuousTimer = useCallback(() => {
    if (continuousTimeoutRef.current) {
      clearTimeout(continuousTimeoutRef.current);
      continuousTimeoutRef.current = null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    if (stateRef.current === "error") {
      forceVoiceState(stateRef, "idle", setState);
    }
  }, []);

  const unlockAutoplay = useCallback(() => {
    setAutoplayBlocked(false);
    outputSessionRef.current?.replay();
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

  // Handle continuous conversation trigger after assistant finishes speaking
  const handleSpeakingEnded = useCallback(() => {
    const current = stateRef.current;
    if (current === "speaking" || current === "paused" || current === "thinking") {
      forceVoiceState(stateRef, "idle", setState);
    }
    if (continuousModeRef.current && !mutedRef.current && !processingRef.current) {
      clearContinuousTimer();
      continuousTimeoutRef.current = setTimeout(() => {
        if (stateRef.current === "idle") {
          beginListening();
        }
      }, 600); // 600ms gap prevents microphone from capturing room reverberation
    }
  }, [clearContinuousTimer]);

  useEffect(() => {
    outputSessionRef.current = new SpeechOutputSession({
      onStart: () => {
        setAutoplayBlocked(false);
        transitionVoiceState(stateRef, "speaking", setState);
      },
      onEnd: () => {
        handleSpeakingEnded();
      },
      onPause: () => transitionVoiceState(stateRef, "paused", setState),
      onResume: () => transitionVoiceState(stateRef, "speaking", setState),
      onError: (message) => {
        setError(message);
        forceVoiceState(stateRef, "error", setState);
      },
      onAutoplayBlocked: () => {
        setAutoplayBlocked(true);
        forceVoiceState(stateRef, "idle", setState);
      },
    });

    return () => {
      clearContinuousTimer();
      inputSessionRef.current?.dispose();
      inputSessionRef.current = null;
      audioRecorderRef.current?.cancel();
      audioRecorderRef.current = null;
      outputSessionRef.current?.dispose();
      outputSessionRef.current = null;
    };
  }, [clearContinuousTimer, handleSpeakingEnded]);

  const finalizeTranscript = useCallback(async (audioBlob?: Blob | null) => {
    setAudioLevel(0);
    setInterimText("");
    inputSessionRef.current = null;
    audioRecorderRef.current = null;

    let finalTranscript = transcriptRef.current.trim();

    // If audio was recorded, use server-side Multimodal STT for superior accuracy
    if (audioBlob && audioBlob.size > 0) {
      transitionVoiceState(stateRef, "transcribing", setState);
      try {
        const sttResult = await transcribeAudio(audioBlob, languageRef.current);
        if (sttResult.transcript.trim()) {
          finalTranscript = sttResult.transcript.trim();
          if (sttResult.detectedLanguage) {
            // Update conversation language if high confidence
            languageRef.current = sttResult.detectedLanguage;
            setLanguage(sttResult.detectedLanguage);
          }
        }
      } catch {
        // If server STT failed, continue with local browser transcript if available
      }
    }

    if (!finalTranscript) {
      setError(mapSpeechError("empty"));
      forceVoiceState(stateRef, "error", setState);
      return;
    }

    setDraftText(finalTranscript);
    draftRef.current = finalTranscript;
    setLastUserText(finalTranscript);

    // Direct Voice-to-Voice: send immediately without requiring manual typing or button click
    if (autoSendRef.current) {
      void runSend(finalTranscript);
    } else {
      forceVoiceState(stateRef, "ready_to_send", setState);
    }
  }, [runSend]);

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

    clearContinuousTimer();
    stopSpeakingInternal();
    inputSessionRef.current?.dispose();
    audioRecorderRef.current?.cancel();

    setError(null);
    setAutoplayBlocked(false);
    setInterimText("");
    setDraftText("");
    draftRef.current = "";
    transcriptRef.current = "";
    processingRef.current = false;

    // 1. Initialize audio recorder for server-side multilingual transcription
    if (isAudioRecordingSupported()) {
      const recorder = new AudioRecorderSession({
        onStart: () => {
          transitionVoiceState(stateRef, "listening", setState);
        },
        onLevel: (level) => {
          setAudioLevel(level);
        },
        onError: (msg) => {
          setError(msg);
          forceVoiceState(stateRef, "error", setState);
        },
      });
      audioRecorderRef.current = recorder;
      void recorder.start();
    }

    // 2. Concurrently run browser SpeechRecognition if supported and not Brave for live interim text
    if (isSpeechRecognitionSupported() && !isBraveBrowser()) {
      const session = new SpeechInputSession(languageRef.current, {
        onStatus: (status) => {
          if (status === "recording") {
            transitionVoiceState(stateRef, "listening", setState);
          } else if (status === "processing") {
            transitionVoiceState(stateRef, "transcribing", setState);
          } else if (status === "idle") {
            if (skipFinalizeRef.current) {
              skipFinalizeRef.current = false;
            }
          } else if (status === "error") {
            // Local recognition error is non-fatal if recorder is capturing
            if (!audioRecorderRef.current?.active) {
              forceVoiceState(stateRef, "error", setState);
            }
          }
        },
        onInterim: (text) => setInterimText(text),
        onFinal: (text) => {
          transcriptRef.current = mergeTranscript(transcriptRef.current, text, 12_000);
        },
        onError: () => {
          // Fall back gracefully to audioRecorder
        },
      });

      inputSessionRef.current = session;
      session.start();
    }

    forceVoiceState(stateRef, "listening", setState);
  }, [clearContinuousTimer, disabled, recognitionSupported, stopSpeakingInternal]);

  const startListening = useCallback(() => {
    // Interrupt AI speech if currently speaking or paused
    if (stateRef.current === "speaking" || stateRef.current === "paused") {
      stopSpeakingInternal();
    }
    beginListening();
  }, [beginListening, stopSpeakingInternal]);

  const stopListening = useCallback(async () => {
    transitionVoiceState(stateRef, "transcribing", setState);
    inputSessionRef.current?.stop();

    if (audioRecorderRef.current?.active) {
      const recordingResult = await audioRecorderRef.current.stop();
      await finalizeTranscript(recordingResult?.blob);
    } else {
      await finalizeTranscript(null);
    }
  }, [finalizeTranscript]);

  const cancelListening = useCallback(() => {
    clearContinuousTimer();
    skipFinalizeRef.current = true;
    inputSessionRef.current?.cancel();
    inputSessionRef.current = null;
    audioRecorderRef.current?.cancel();
    audioRecorderRef.current = null;
    processingRef.current = false;
    setAudioLevel(0);
    setInterimText("");
    transcriptRef.current = "";
    setDraftText("");
    draftRef.current = "";
    forceVoiceState(stateRef, "idle", setState);
  }, [clearContinuousTimer]);

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
    clearContinuousTimer();
    stopSpeakingInternal();
  }, [clearContinuousTimer, stopSpeakingInternal]);

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
    clearContinuousTimer();
    skipFinalizeRef.current = true;
    inputSessionRef.current?.cancel();
    inputSessionRef.current = null;
    audioRecorderRef.current?.cancel();
    audioRecorderRef.current = null;
    processingRef.current = false;
    stopSpeakingInternal();
    setAudioLevel(0);
    setInterimText("");
    transcriptRef.current = "";
    setDraftText("");
    draftRef.current = "";
    setError(null);
    setAutoplayBlocked(false);
    forceVoiceState(stateRef, "idle", setState);
  }, [clearContinuousTimer, stopSpeakingInternal]);

  return {
    state,
    stateLabel: voiceStateLabel(state),
    supported: recognitionSupported,
    ttsSupported,
    language,
    setLanguage,
    muted,
    setMuted,
    autoSend,
    setAutoSend,
    continuousMode,
    setContinuousMode,
    autoplayBlocked,
    unlockAutoplay,
    audioLevel,
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
