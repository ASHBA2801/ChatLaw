/**
 * High-fidelity neural TTS client synthesis and audio playback.
 * Connects to /api/voice/tts with seamless fallback to browser SpeechSynthesis.
 */

export interface SynthesizedAudioResult {
  audioUrl: string;
  blob: Blob;
  voice: string;
  cleanup: () => void;
}

export interface AudioPlayHandle {
  pause: () => void;
  resume: () => Promise<void>;
  stop: () => void;
  element: HTMLAudioElement;
}

export interface PlaySpeechOptions {
  onStart?: () => void;
  onEnded?: () => void;
  onError?: (err: Error) => void;
  onAutoplayBlocked?: () => void;
}

const AUDIO_CACHE_LIMIT = 8;
const audioCache = new Map<string, { blob: Blob; voice: string }>();

function resultFromBlob(blob: Blob, voice: string): SynthesizedAudioResult {
  const audioUrl = URL.createObjectURL(blob);
  return {
    audioUrl,
    blob,
    voice,
    cleanup: () => {
      try {
        URL.revokeObjectURL(audioUrl);
      } catch {
        // ignore
      }
    },
  };
}

/**
 * Request neural speech audio for the provided text and language.
 */
export async function synthesizeSpeechAudio(
  text: string,
  language: string = "en",
  voice?: string,
  signal?: AbortSignal,
): Promise<SynthesizedAudioResult> {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error("Cannot synthesize empty text.");
  }

  const cacheKey = `${language}|${voice ?? ""}|${trimmed}`;
  const cached = audioCache.get(cacheKey);
  if (cached) return resultFromBlob(cached.blob, cached.voice);

  const response = await fetch("/api/voice/tts", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: trimmed,
      language,
      voice,
    }),
  });

  if (!response.ok) {
    let errorMsg = "Text-to-speech synthesis failed.";
    try {
      const data = await response.json();
      if (data.error) errorMsg = data.error;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  const blob = await response.blob();
  const voiceHeader = response.headers.get("x-chatlaw-voice") || "";
  audioCache.set(cacheKey, { blob, voice: voiceHeader });
  if (audioCache.size > AUDIO_CACHE_LIMIT) {
    const oldest = audioCache.keys().next().value;
    if (oldest !== undefined) audioCache.delete(oldest);
  }
  return resultFromBlob(blob, voiceHeader);
}

/**
 * Play a synthesized audio URL using an HTMLAudioElement with autoplay block handling.
 */
export function playSynthesizedAudio(
  audioUrl: string,
  options: PlaySpeechOptions = {},
): AudioPlayHandle {
  const audio = new Audio(audioUrl);

  audio.onplay = () => {
    options.onStart?.();
  };

  audio.onended = () => {
    options.onEnded?.();
  };

  audio.onerror = () => {
    const err = new Error("Audio playback failed on this device.");
    options.onError?.(err);
  };

  // Attempt to play immediately
  const playPromise = audio.play();
  if (playPromise !== undefined) {
    playPromise.catch((err: unknown) => {
      if (err && typeof err === "object" && (err as { name?: string }).name === "NotAllowedError") {
        options.onAutoplayBlocked?.();
      } else {
        options.onError?.(err instanceof Error ? err : new Error(String(err)));
      }
    });
  }

  return {
    pause: () => {
      audio.pause();
    },
    resume: async () => {
      await audio.play();
    },
    stop: () => {
      audio.onplay = null;
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
      audio.currentTime = 0;
    },
    element: audio,
  };
}
