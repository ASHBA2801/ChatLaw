"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { mapSpeechError } from "./errors";
import { DEFAULT_SPEECH_LANGUAGE, isSpeechRecognitionSupported } from "./support";
import { SpeechInputSession } from "./SpeechInputSession";
import { mergeTranscript } from "./transcript";
import type { SpeechInputStatus, SpeechLanguageCode } from "./types";

function subscribeToNothing() {
  return () => undefined;
}

function getSpeechSupportSnapshot() {
  return isSpeechRecognitionSupported();
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
    };
  }, []);

  const resolvedStatus: SpeechInputStatus = !supported ? "unsupported" : status;
  const isListening = resolvedStatus === "recording" || resolvedStatus === "processing";

  const clearError = useCallback(() => setError(null), []);

  const start = useCallback(() => {
    if (disabled) return;
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
    sessionRef.current?.stop();
  }, []);

  const cancel = useCallback(() => {
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
