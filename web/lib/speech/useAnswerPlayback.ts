"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DEFAULT_SPEECH_LANGUAGE } from "./support";
import { SpeechOutputSession } from "./SpeechOutputSession";
import { prepareTextForSpeech } from "./speechText";
import type { SpeechLanguageCode } from "./types";

export type AnswerPlaybackStatus = "idle" | "speaking" | "paused" | "unsupported" | "error";

export interface UseAnswerPlaybackResult {
  status: AnswerPlaybackStatus;
  activeMessageId: string | null;
  supported: boolean;
  error: string | null;
  clearError: () => void;
  play: (messageId: string, text: string, language?: SpeechLanguageCode) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
}

/**
 * Single-owner answer TTS for text-mode message lists.
 * Only one answer can speak at a time.
 */
export function useAnswerPlayback(): UseAnswerPlaybackResult {
  const [status, setStatus] = useState<AnswerPlaybackStatus>("idle");
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sessionRef = useRef<SpeechOutputSession | null>(null);
  const activeIdRef = useRef<string | null>(null);

  const supported = typeof window !== "undefined" && Boolean(window.speechSynthesis);

  useEffect(() => {
    sessionRef.current = new SpeechOutputSession({
      onStart: () => setStatus("speaking"),
      onEnd: () => {
        setStatus("idle");
        setActiveMessageId(null);
        activeIdRef.current = null;
      },
      onPause: () => setStatus("paused"),
      onResume: () => setStatus("speaking"),
      onError: (message) => {
        setError(message);
        setStatus("error");
        setActiveMessageId(null);
        activeIdRef.current = null;
      },
    });

    return () => {
      sessionRef.current?.dispose();
      sessionRef.current = null;
    };
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    if (status === "error") setStatus("idle");
  }, [status]);

  const stop = useCallback(() => {
    sessionRef.current?.stop();
    setStatus("idle");
    setActiveMessageId(null);
    activeIdRef.current = null;
  }, []);

  const play = useCallback((messageId: string, text: string, language: SpeechLanguageCode = DEFAULT_SPEECH_LANGUAGE) => {
    if (!supported) {
      setStatus("unsupported");
      setError("Voice playback isn't available in this browser.");
      return;
    }
    const spoken = prepareTextForSpeech(text);
    if (!spoken) {
      setError("There is nothing to read aloud.");
      setStatus("error");
      return;
    }
    setError(null);
    activeIdRef.current = messageId;
    setActiveMessageId(messageId);
    sessionRef.current?.speak(spoken, language);
  }, [supported]);

  const pause = useCallback(() => {
    if (status !== "speaking") return;
    sessionRef.current?.pause();
  }, [status]);

  const resume = useCallback(() => {
    if (status !== "paused") return;
    sessionRef.current?.resume();
  }, [status]);

  return {
    status,
    activeMessageId,
    supported,
    error,
    clearError,
    play,
    pause,
    resume,
    stop,
  };
}
