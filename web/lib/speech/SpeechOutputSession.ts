import type { SpeechLanguageCode, SpeechOutputWindow, SpeechSynthesisLike, SpeechSynthesisUtteranceLike } from "./types";
import { resolveSpeechLocale } from "./support";
import { segmentSpeechText } from "./speechText";

export interface SpeechOutputCallbacks {
  onStart: () => void;
  onEnd: () => void;
  onPause: () => void;
  onResume: () => void;
  onError: (message: string) => void;
}

function mapTtsError(event: SpeechSynthesisErrorEvent): string {
  switch (event.error) {
    case "canceled":
      return "Speech was stopped.";
    case "interrupted":
      return "Speech was interrupted.";
    case "audio-busy":
      return "Audio output is busy. Try again in a moment.";
    case "audio-hardware":
      return "Audio output is unavailable on this device.";
    case "network":
      return "Speech output could not reach the voice service.";
    case "synthesis-unavailable":
    case "synthesis-failed":
      return "Speech output is unavailable in this browser.";
    case "text-too-long":
      return "The answer is too long to read aloud in one pass.";
    case "language-unavailable":
      return "Speech output could not use the selected language.";
    default:
      return "Unable to speak the response. You can read it on screen.";
  }
}

/**
 * Browser SpeechSynthesis wrapper — independent from STT and RAG.
 * Long answers are split into sequential utterance segments.
 */
export class SpeechOutputSession {
  private utterance: SpeechSynthesisUtteranceLike | null = null;
  private queue: string[] = [];
  private lastText = "";
  private lastLang: SpeechLanguageCode = "en-IN";
  private disposed = false;
  private started = false;
  private stopping = false;
  private startTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private readonly callbacks: SpeechOutputCallbacks,
    private readonly win: SpeechOutputWindow | undefined = typeof window !== "undefined"
      ? { speechSynthesis: window.speechSynthesis as unknown as SpeechSynthesisLike | undefined }
      : undefined,
  ) {}

  get synthesis() {
    return this.win?.speechSynthesis ?? null;
  }

  isSupported(): boolean {
    return Boolean(this.synthesis && typeof this.synthesis.speak === "function");
  }

  speak(text: string, lang: SpeechLanguageCode): void {
    if (this.disposed) return;
    const synth = this.synthesis;
    if (!synth) {
      this.callbacks.onError("Speech output isn't supported in this browser.");
      return;
    }
    const trimmed = text.trim();
    if (!trimmed) {
      this.callbacks.onError("There is nothing to read aloud.");
      return;
    }

    this.stopping = false;
    synth.cancel();
    try {
      synth.resume?.();
    } catch {
      // Some browsers expose resume only after a user gesture.
    }
    this.lastText = trimmed;
    this.lastLang = resolveSpeechLocale(lang).locale;
    this.queue = segmentSpeechText(trimmed);
    this.started = false;
    this.speakNext();
  }

  private clearStartTimeout(): void {
    if (this.startTimeout !== null) {
      clearTimeout(this.startTimeout);
      this.startTimeout = null;
    }
  }

  private armStartTimeout(): void {
    this.clearStartTimeout();
    this.startTimeout = setTimeout(() => {
      this.startTimeout = null;
      if (this.disposed || this.stopping || this.started) return;
      this.queue = [];
      this.utterance = null;
      this.synthesis?.cancel();
      this.callbacks.onError("Speech output did not start. You can read the answer on screen.");
    }, 3000);
  }

  private speakNext(): void {
    if (this.disposed || this.stopping) return;
    const synth = this.synthesis;
    if (!synth) {
      this.callbacks.onError("Speech output isn't supported in this browser.");
      return;
    }

    const next = this.queue.shift();
    if (!next) {
      this.utterance = null;
      this.clearStartTimeout();
      this.callbacks.onEnd();
      return;
    }

    const UtteranceCtor = (globalThis as { SpeechSynthesisUtterance?: new (text: string) => SpeechSynthesisUtteranceLike }).SpeechSynthesisUtterance;
    if (!UtteranceCtor) {
      this.callbacks.onError("Speech output isn't supported in this browser.");
      return;
    }

    const utterance = new UtteranceCtor(next);
    utterance.lang = this.lastLang;
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      if (this.disposed || this.stopping) return;
      this.clearStartTimeout();
      if (!this.started) {
        this.started = true;
        this.callbacks.onStart();
      }
    };
    utterance.onend = () => {
      if (this.disposed || this.stopping) return;
      this.utterance = null;
      this.speakNext();
    };
    utterance.onerror = (event) => {
      if (this.disposed || this.stopping) return;
      this.utterance = null;
      this.queue = [];
      this.clearStartTimeout();
      if (event.error === "canceled" || event.error === "interrupted") {
        this.callbacks.onEnd();
        return;
      }
      this.callbacks.onError(mapTtsError(event));
    };
    utterance.onpause = () => {
      if (this.disposed || this.stopping) return;
      this.callbacks.onPause();
    };
    utterance.onresume = () => {
      if (this.disposed || this.stopping) return;
      this.callbacks.onResume();
    };

    this.utterance = utterance;
    if (!this.started) {
      this.armStartTimeout();
    }
    synth.speak(utterance);
  }

  pause(): void {
    if (this.disposed) return;
    this.synthesis?.pause();
  }

  resume(): void {
    if (this.disposed) return;
    this.synthesis?.resume();
  }

  stop(): void {
    if (this.disposed) return;
    this.stopping = true;
    this.clearStartTimeout();
    this.queue = [];
    this.utterance = null;
    this.synthesis?.cancel();
  }

  replay(): void {
    if (this.disposed || !this.lastText) return;
    this.speak(this.lastText, this.lastLang);
  }

  dispose(): void {
    this.disposed = true;
    this.stop();
  }
}
