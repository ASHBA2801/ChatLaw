/** Browser speech recognition types (vendor-prefixed APIs vary). */

export type SpeechInputStatus =
  | "idle"
  | "unsupported"
  | "recording"
  | "processing"
  | "error";

/** BCP-47 tags used with Web Speech APIs. */
export type SpeechLanguageCode = string;

export interface SpeechLanguageOption {
  code: SpeechLanguageCode;
  label: string;
  /** Whether this locale is offered in the UI. */
  enabled: boolean;
  chatLanguageCode?: string;
}

export interface SpeechRecognitionResultLike {
  readonly isFinal: boolean;
  readonly length: number;
  readonly [index: number]: { readonly transcript: string };
}

export interface SpeechRecognitionEventLike {
  readonly resultIndex: number;
  readonly results: {
    readonly length: number;
    readonly [index: number]: SpeechRecognitionResultLike;
  };
}

export interface SpeechRecognitionErrorEventLike {
  readonly error: string;
  readonly message?: string;
}

export interface SpeechRecognitionLike {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: ((event: Event) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: ((event: Event) => void) | null;
}

export type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

export interface SpeechWindow extends Window {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
}

export type VoiceChatState =
  | "idle"
  | "listening"
  | "transcribing"
  | "ready_to_send"
  | "thinking"
  | "speaking"
  | "paused"
  | "error";

export type ChatInputMode = "text" | "voice";

export interface SpeechSynthesisUtteranceLike {
  text: string;
  lang: string;
  rate: number;
  pitch: number;
  volume: number;
  onstart: ((event: Event) => void) | null;
  onend: ((event: Event) => void) | null;
  onerror: ((event: SpeechSynthesisErrorEvent) => void) | null;
  onpause: ((event: Event) => void) | null;
  onresume: ((event: Event) => void) | null;
}

export interface SpeechSynthesisLike {
  speaking: boolean;
  paused: boolean;
  pending: boolean;
  cancel: () => void;
  pause: () => void;
  resume: () => void;
  speak: (utterance: SpeechSynthesisUtteranceLike) => void;
  getVoices: () => Array<{ lang: string; name: string; default?: boolean }>;
}

export interface SpeechOutputWindow {
  speechSynthesis?: SpeechSynthesisLike;
}
