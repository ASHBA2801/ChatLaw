import { describe, expect, it, vi } from "vitest";
import { mapSpeechError } from "@/lib/speech/errors";
import {
  getEnabledSpeechLanguages,
  getSpeechRecognitionConstructor,
  isSpeechRecognitionSupported,
} from "@/lib/speech/support";
import { extractTranscriptParts, mergeTranscript } from "@/lib/speech/transcript";
import { SpeechInputSession } from "@/lib/speech/SpeechInputSession";
import type { SpeechRecognitionLike, SpeechWindow } from "@/lib/speech/types";

function createMockRecognition(): SpeechRecognitionLike & {
  triggerStart: () => void;
  triggerResult: (finalText: string, interimText?: string) => void;
  triggerError: (error: string) => void;
  triggerEnd: () => void;
} {
  const recognition = {
    continuous: false,
    interimResults: false,
    lang: "",
    maxAlternatives: 1,
    start: vi.fn(),
    stop: vi.fn(function (this: SpeechRecognitionLike) {
      this.onend?.(new Event("end"));
    }),
    abort: vi.fn(function (this: SpeechRecognitionLike) {
      this.onend?.(new Event("end"));
    }),
    onstart: null as SpeechRecognitionLike["onstart"],
    onresult: null as SpeechRecognitionLike["onresult"],
    onerror: null as SpeechRecognitionLike["onerror"],
    onend: null as SpeechRecognitionLike["onend"],
    triggerStart() {
      this.onstart?.(new Event("start"));
    },
    triggerResult(finalText: string, interimText = "") {
      const results = [] as Array<{ isFinal: boolean; length: number; 0: { transcript: string } }>;
      if (finalText) results.push({ isFinal: true, length: 1, 0: { transcript: finalText } });
      if (interimText) results.push({ isFinal: false, length: 1, 0: { transcript: interimText } });
      this.onresult?.({
        resultIndex: 0,
        results: Object.assign(results, { length: results.length }),
      });
    },
    triggerError(error: string) {
      this.onerror?.({ error });
    },
    triggerEnd() {
      this.onend?.(new Event("end"));
    },
  };
  return recognition;
}

describe("speech support", () => {
  it("detects unsupported browsers", () => {
    expect(isSpeechRecognitionSupported({} as SpeechWindow)).toBe(false);
    expect(getSpeechRecognitionConstructor({} as SpeechWindow)).toBeNull();
  });

  it("detects SpeechRecognition and webkitSpeechRecognition", () => {
    const Ctor = vi.fn();
    expect(isSpeechRecognitionSupported({ SpeechRecognition: Ctor } as unknown as SpeechWindow)).toBe(true);
    expect(isSpeechRecognitionSupported({ webkitSpeechRecognition: Ctor } as unknown as SpeechWindow)).toBe(true);
  });

  it("exposes Eighth Schedule speech locales including major Indian languages", () => {
    const enabled = getEnabledSpeechLanguages();
    expect(enabled.every((item) => item.enabled)).toBe(true);
    const codes = enabled.map((item) => item.code);
    expect(codes).toContain("en-IN");
    expect(codes).toContain("en-US");
    expect(codes).toContain("hi-IN");
    expect(codes).toContain("ta-IN");
    expect(codes).toContain("as-IN");
    expect(codes).not.toContain("de-DE");
  });

  it("maps chat language codes to BCP-47 speech locales with fallbacks", async () => {
    const { chatLanguageToSpeechCode, speechCodeToChatLanguage, resolveSpeechLocale } = await import(
      "@/lib/speech/support"
    );
    expect(chatLanguageToSpeechCode("ta")).toBe("ta-IN");
    expect(chatLanguageToSpeechCode("hi")).toBe("hi-IN");
    expect(speechCodeToChatLanguage("te-IN")).toBe("te");
    expect(resolveSpeechLocale("ta-IN")).toEqual({ locale: "ta-IN", usedFallback: false });
    expect(resolveSpeechLocale("mai-IN").usedFallback).toBe(true);
  });
});

describe("speech errors", () => {
  it("maps permission and empty failures without leaking internals", () => {
    expect(mapSpeechError("not-allowed")).toContain("denied");
    expect(mapSpeechError("unsupported")).toContain("isn't supported");
    expect(mapSpeechError("empty")).toContain("Nothing was transcribed");
    expect(mapSpeechError("mysterious-stack")).not.toContain("mysterious");
  });
});

describe("transcript helpers", () => {
  it("merges and truncates transcripts for the composer", () => {
    expect(mergeTranscript("", "Hello world", 100)).toBe("Hello world");
    expect(mergeTranscript("Hello", "world", 100)).toBe("Hello world");
    expect(mergeTranscript("abc", "def", 5)).toBe("abc d");
  });

  it("extracts final and interim parts", () => {
    const results = Object.assign(
      [
        { isFinal: true, length: 1, 0: { transcript: "Section 303 " } },
        { isFinal: false, length: 1, 0: { transcript: "theft" } },
      ],
      { length: 2 },
    );
    expect(extractTranscriptParts(results)).toEqual({
      finalText: "Section 303",
      interimText: "theft",
    });
  });
});

describe("SpeechInputSession", () => {
  it("moves idle → recording → idle and emits transcript", () => {
    const recognition = createMockRecognition();
    const Ctor = vi.fn(() => recognition);
    const statuses: string[] = [];
    const finals: string[] = [];

    const session = new SpeechInputSession(
      "en-IN",
      {
        onStatus: (status) => statuses.push(status),
        onInterim: () => undefined,
        onFinal: (text) => finals.push(text),
        onError: () => undefined,
      },
      { SpeechRecognition: Ctor } as unknown as SpeechWindow,
    );

    session.start();
    expect(Ctor).toHaveBeenCalledOnce();
    recognition.triggerStart();
    expect(statuses).toContain("recording");
    recognition.triggerResult("What is the punishment for theft?");
    session.stop();
    expect(statuses).toContain("processing");
    expect(finals).toEqual(["What is the punishment for theft?"]);
    expect(statuses.at(-1)).toBe("idle");
  });

  it("returns to error then usable state on permission failure", () => {
    const recognition = createMockRecognition();
    const Ctor = vi.fn(() => recognition);
    const statuses: string[] = [];
    const errors: string[] = [];

    const session = new SpeechInputSession(
      "en-IN",
      {
        onStatus: (status) => statuses.push(status),
        onInterim: () => undefined,
        onFinal: () => undefined,
        onError: (message) => errors.push(message),
      },
      { SpeechRecognition: Ctor } as unknown as SpeechWindow,
    );

    session.start();
    recognition.triggerStart();
    recognition.triggerError("not-allowed");
    expect(statuses).toContain("error");
    expect(errors[0]).toContain("denied");
    recognition.triggerEnd();
    expect(statuses.at(-1)).toBe("idle");
  });

  it("cancels without leaving a stuck recording state", () => {
    const recognition = createMockRecognition();
    const Ctor = vi.fn(() => recognition);
    const statuses: string[] = [];

    const session = new SpeechInputSession(
      "en-IN",
      {
        onStatus: (status) => statuses.push(status),
        onInterim: () => undefined,
        onFinal: () => undefined,
        onError: () => undefined,
      },
      { SpeechRecognition: Ctor } as unknown as SpeechWindow,
    );

    session.start();
    recognition.triggerStart();
    session.cancel();
    expect(recognition.abort).toHaveBeenCalled();
    expect(statuses.at(-1)).toBe("idle");
  });

  it("reports unsupported when recognition constructor is missing", () => {
    const statuses: string[] = [];
    const errors: string[] = [];
    const session = new SpeechInputSession(
      "en-IN",
      {
        onStatus: (status) => statuses.push(status),
        onInterim: () => undefined,
        onFinal: () => undefined,
        onError: (message) => errors.push(message),
      },
      {} as SpeechWindow,
    );

    session.start();
    expect(statuses).toEqual(["unsupported"]);
    expect(errors[0]).toContain("isn't supported");
  });

  it("treats empty stop as a recoverable error", () => {
    const recognition = createMockRecognition();
    const Ctor = vi.fn(() => recognition);
    const statuses: string[] = [];
    const errors: string[] = [];

    const session = new SpeechInputSession(
      "en-IN",
      {
        onStatus: (status) => statuses.push(status),
        onInterim: () => undefined,
        onFinal: () => undefined,
        onError: (message) => errors.push(message),
      },
      { SpeechRecognition: Ctor } as unknown as SpeechWindow,
    );

    session.start();
    recognition.triggerStart();
    session.stop();
    expect(errors[0]).toContain("Nothing was transcribed");
    expect(statuses).toContain("error");
  });
});
