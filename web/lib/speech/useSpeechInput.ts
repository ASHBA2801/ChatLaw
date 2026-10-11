"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { AudioRecorderSession, isAudioRecordingSupported } from "./audioRecorder";
import { mapSpeechError } from "./errors";
import { DEFAULT_SPEECH_LANGUAGE, isBraveBrowser, isSpeechRecognitionSupported } from "./support";
import { SpeechInputSession } from "./SpeechInputSession";
import { transcribeAudio } from "./transcribe";
import { mergeTranscript } from "./transcript";
import type { SpeechInputStatus, SpeechLanguageCode } from "./types";

function subscribeToNothing() {
  return () => undefined;
}

/** Browser speech recognition, or a microphone recording we can transcribe on the server. */
function getSpeechSupportSnapshot() {
  return isSpeechRecognitionSupported() || isAudioRecordingSupported();
}

/**
 * Brave exposes the Web Speech API but blocks its transcription backend, so there (and in browsers without the API)
 * dictation records audio and sends it to the server transcription route instead.
 */
function shouldUseServerTranscription() {
  return isBraveBrowser() || !isSpeechRecognitionSupported();
}

function getServerSpeechSupportSnapshot() {
  return false;
}

export interface UseSpeechInputOptions {
  value: string;
  onChange: (next: string) => void;
  limit: number;
  language?: SpeechLanguageCode;
  disabled?: boolean;
}

export interface UseSpeechInputResult {
  status: SpeechInputStatus;
  supported: boolean;
  language: SpeechLanguageCode;
  setLanguage: (language: SpeechLanguageCode) => void;
  error: string | null;
  interimText: string;
  /** Value shown in the composer while listening (includes interim text). */
  displayValue: string;
  isListening: boolean;
  start: () => void;
  stop: () => void;
  cancel: () => void;
  clearError: () => void;
}

export function useSpeechInput({
  value,
  onChange,
  limit,
  language: initialLanguage = DEFAULT_SPEECH_LANGUAGE,
  disabled = false,
}: UseSpeechInputOptions): UseSpeechInputResult {
  const supported = useSyncExternalStore(
    subscribeToNothing,
    getSpeechSupportSnapshot,
    getServerSpeechSupportSnapshot,
  );
  const [status, setStatus] = useState<SpeechInputStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [interimText, setInterimText] = useState("");
  const [baseValue, setBaseValue] = useState(value);
  const [language, setLanguage] = useState<SpeechLanguageCode>(initialLanguage);

  const sessionRef = useRef<SpeechInputSession | null>(null);
  const recorderRef = useRef<AudioRecorderSession | null>(null);
  /** Bumped on cancel so a transcription that finishes late is dropped. */
  const runIdRef = useRef(0);
  const baseValueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  const languageRef = useRef(language);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    setLanguage(initialLanguage);
  }, [initialLanguage]);

  useEffect(() => {
    languageRef.current = language;
  }, [language]);

  useEffect(() => {
    return () => {
      sessionRef.current?.dispose();
      sessionRef.current = null;
      recorderRef.current?.cancel();
      recorderRef.current = null;
    };
  }, []);

  const resolvedStatus: SpeechInputStatus = !supported ? "unsupported" : status;
  const isListening = resolvedStatus === "recording" || resolvedStatus === "processing";

  const clearError = useCallback(() => setError(null), []);

  const finishServerRecording = useCallback(
    async (recorder: AudioRecorderSession) => {
      const runId = runIdRef.current;
      setStatus("processing");
      try {
        const result = await recorder.stop();
        if (runId !== runIdRef.current) return;
        const transcript = result && result.blob.size > 0 ? (await transcribeAudio(result.blob, languageRef.current)).transcript.trim() : "";
        if (runId !== runIdRef.current) return;
        if (!transcript) {
          setError(mapSpeechError("empty"));
          return;
        }
        const next = mergeTranscript(baseValueRef.current, transcript, limit);
        baseValueRef.current = next;
        setBaseValue(next);
        onChangeRef.current(next);
      } catch (requestError) {
        if (runId !== runIdRef.current) return;
        setError(requestError instanceof Error && requestError.message ? requestError.message : mapSpeechError(null));
      } finally {
        if (runId === runIdRef.current) setStatus("idle");
      }
    },
    [limit],
  );

  const start = useCallback(() => {
    if (disabled) return;

    if (shouldUseServerTranscription()) {
      if (!isAudioRecordingSupported()) {
        setError(mapSpeechError("unsupported"));
        return;
      }
      if (recorderRef.current) return; // already starting or recording
      sessionRef.current?.dispose();
      setError(null);
      setInterimText("");
      baseValueRef.current = value;
      setBaseValue(value);
      const recorder = new AudioRecorderSession({
        onStart: () => setStatus("recording"),
        onError: (message) => {
          recorderRef.current = null;
          setError(message);
          setStatus("idle");
        },
      });
      recorderRef.current = recorder;
      void recorder.start();
      return;
    }

    if (!isSpeechRecognitionSupported()) {
      setError(mapSpeechError("unsupported"));
      return;
    }

    sessionRef.current?.dispose();
    setError(null);
    setInterimText("");
    baseValueRef.current = value;
    setBaseValue(value);

    const session = new SpeechInputSession(language, {
      onStatus: (next) => setStatus(next === "unsupported" ? "idle" : next),
      onInterim: (text) => setInterimText(text),
      onFinal: (text) => {
        const next = mergeTranscript(baseValueRef.current, text, limit);
        baseValueRef.current = next;
        setBaseValue(next);
        onChangeRef.current(next);
        setInterimText("");
      },
      onError: (message) => setError(message),
    });

    sessionRef.current = session;
    session.start();
  }, [disabled, language, limit, value]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder) {
      recorderRef.current = null;
      void finishServerRecording(recorder);
      return;
    }
    sessionRef.current?.stop();
  }, [finishServerRecording]);

  const cancel = useCallback(() => {
    runIdRef.current += 1;
    recorderRef.current?.cancel();
    recorderRef.current = null;
    sessionRef.current?.cancel();
    sessionRef.current = null;
    setInterimText("");
    setError(null);
    setStatus("idle");
  }, []);

  const displayValue = isListening ? mergeTranscript(baseValue, interimText, limit) : value;

  return {
    status: resolvedStatus,
    supported,
    language,
    setLanguage,
    error,
    interimText,
    displayValue,
    isListening,
    start,
    stop,
    cancel,
    clearError,
  };
}
