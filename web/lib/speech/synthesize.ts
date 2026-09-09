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

/**
 * Request neural speech audio for the provided text and language.
 */
export async function synthesizeSpeechAudio(
  text: string,
  language: string = "en",
  voice?: string,
): Promise<SynthesizedAudioResult> {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error("Cannot synthesize empty text.");
  }

  const response = await fetch("/api/voice/tts", {
    method: "POST",
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
  const audioUrl = URL.createObjectURL(blob);

  return {
    audioUrl,
    blob,
    voice: voiceHeader,
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
      audio.pause();
      audio.currentTime = 0;
    },
    element: audio,
  };
}
