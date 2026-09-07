import { mapSpeechError } from "./errors";
import { getSpeechRecognitionConstructor, resolveSpeechLocale } from "./support";
import type {
  SpeechInputStatus,
  SpeechLanguageCode,
  SpeechRecognitionErrorEventLike,
  SpeechRecognitionEventLike,
  SpeechRecognitionLike,
  SpeechWindow,
} from "./types";
import { extractTranscriptParts } from "./transcript";

export interface SpeechSessionCallbacks {
  onStatus: (status: SpeechInputStatus) => void;
  onInterim: (text: string) => void;
  onFinal: (text: string) => void;
  onError: (message: string) => void;
}

/**
 * Owns a single browser SpeechRecognition lifecycle.
 * Phase 18 can wrap this with TTS / continuous conversation without changing RAG.
 */
export class SpeechInputSession {
  private recognition: SpeechRecognitionLike | null = null;
  private intentionalStop = false;
  private sawResult = false;
  private disposed = false;

  constructor(
    private readonly language: SpeechLanguageCode,
    private readonly callbacks: SpeechSessionCallbacks,
    private readonly win: SpeechWindow | undefined = typeof window !== "undefined" ? (window as SpeechWindow) : undefined,
  ) {}

  start(): void {
    if (this.disposed) return;

    const Ctor = getSpeechRecognitionConstructor(this.win);
    if (!Ctor) {
      this.callbacks.onStatus("unsupported");
      this.callbacks.onError(mapSpeechError("unsupported"));
      return;
    }

    this.stopInternal(true);
    this.intentionalStop = false;
    this.sawResult = false;

    const recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = resolveSpeechLocale(this.language).locale;

    recognition.onstart = () => {
      if (this.disposed) return;
      this.callbacks.onStatus("recording");
    };

    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      if (this.disposed) return;
      const { finalText, interimText } = extractTranscriptParts(event.results, event.resultIndex);
      if (finalText) {
        this.sawResult = true;
        this.callbacks.onFinal(finalText);
      }
      this.callbacks.onInterim(interimText);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEventLike) => {
      if (this.disposed) return;
      if (event.error === "aborted" && this.intentionalStop) {
        return;
      }
      this.callbacks.onStatus("error");
      this.callbacks.onError(mapSpeechError(event.error));
    };

    recognition.onend = () => {
      if (this.disposed) return;
      this.recognition = null;
      if (this.intentionalStop) {
        this.callbacks.onStatus("processing");
        if (!this.sawResult) {
          this.callbacks.onError(mapSpeechError("empty"));
          this.callbacks.onStatus("error");
          return;
        }
        this.callbacks.onInterim("");
        this.callbacks.onStatus("idle");
        return;
      }
      // Unexpected end while still intending to record — return to idle safely.
      this.callbacks.onInterim("");
      this.callbacks.onStatus("idle");
    };

    this.recognition = recognition;
    try {
      recognition.start();
    } catch {
      this.recognition = null;
      this.callbacks.onStatus("error");
      this.callbacks.onError(mapSpeechError("busy"));
    }
  }

  stop(): void {
    this.intentionalStop = true;
    if (!this.recognition) {
      this.callbacks.onStatus("idle");
      return;
    }
    this.callbacks.onStatus("processing");
    try {
      this.recognition.stop();
    } catch {
      this.recognition = null;
      this.callbacks.onStatus("idle");
    }
  }

  cancel(): void {
    this.intentionalStop = true;
    this.stopInternal(true);
    this.callbacks.onInterim("");
    this.callbacks.onStatus("idle");
  }

  dispose(): void {
    this.disposed = true;
    this.intentionalStop = true;
    this.stopInternal(true);
  }

  private stopInternal(abort: boolean): void {
    if (!this.recognition) return;
    const active = this.recognition;
    this.recognition = null;
    try {
      if (abort) active.abort();
      else active.stop();
    } catch {
      // Already stopped.
    }
  }
}
