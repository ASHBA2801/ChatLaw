import { describe, expect, it, vi } from "vitest";
import { SpeechOutputSession } from "@/lib/speech/SpeechOutputSession";
import {
  prepareTextForSpeech,
  segmentSpeechText,
  stripCitationMarkers,
  stripUrls,
} from "@/lib/speech/speechText";
import { canStartVoiceListening, canTransition, isVoiceBusy, voiceStateLabel } from "@/lib/speech/voiceState";
import type { SpeechOutputWindow, SpeechSynthesisUtteranceLike } from "@/lib/speech/types";

describe("speechText", () => {
  it("removes citation markers and urls for spoken output", () => {
    const raw = "The punishment is stated in [1] and [SOURCE 2]. See https://example.com/law";
    expect(stripCitationMarkers(raw)).not.toContain("[1]");
    expect(stripUrls(raw)).not.toContain("https://");
    expect(prepareTextForSpeech(raw)).toBe("The punishment is stated in and . See");
  });

  it("flattens markdown while preserving readable prose", () => {
    const raw = "## Punishment\n\nTheft is punishable under **Section 303** [1].";
    expect(prepareTextForSpeech(raw)).toBe("Punishment Theft is punishable under Section 303 .");
  });

  it("returns empty string for blank answers", () => {
    expect(prepareTextForSpeech("   ")).toBe("");
  });

  it("segments long text into utterance-sized chunks", () => {
    const long = "First sentence. ".repeat(40) + "Final clause.";
    const segments = segmentSpeechText(long, 80);
    expect(segments.length).toBeGreaterThan(1);
    expect(segments.every((part) => part.length <= 80)).toBe(true);
    expect(segments.join(" ")).toContain("Final clause");
  });

  it("keeps short text as a single segment", () => {
    expect(segmentSpeechText("Short answer.")).toEqual(["Short answer."]);
  });
});

describe("voiceState", () => {
  it("allows deterministic transitions including ready_to_send", () => {
    expect(canTransition("idle", "listening")).toBe(true);
    expect(canTransition("listening", "transcribing")).toBe(true);
    expect(canTransition("transcribing", "ready_to_send")).toBe(true);
    expect(canTransition("ready_to_send", "thinking")).toBe(true);
    expect(canTransition("thinking", "speaking")).toBe(true);
    expect(canTransition("speaking", "idle")).toBe(true);
    expect(canTransition("speaking", "listening")).toBe(true);
    expect(canTransition("listening", "speaking")).toBe(false);
    expect(canTransition("transcribing", "thinking")).toBe(false);
  });

  it("labels states for screen readers", () => {
    expect(voiceStateLabel("listening")).toBe("Listening…");
    expect(voiceStateLabel("ready_to_send")).toBe("Review transcript");
    expect(voiceStateLabel("speaking")).toBe("Speaking…");
  });

  it("tracks busy states", () => {
    expect(isVoiceBusy("idle")).toBe(false);
    expect(isVoiceBusy("ready_to_send")).toBe(false);
    expect(isVoiceBusy("thinking")).toBe(true);
  });

  it("allows case voice without a conversation id", () => {
    expect(canStartVoiceListening(null, true)).toBe(true);
    expect(canStartVoiceListening(null, false)).toBe(false);
    expect(canStartVoiceListening("conv-1", false)).toBe(true);
  });
});

function installMockUtterance() {
  class MockUtterance implements SpeechSynthesisUtteranceLike {
    text = "";
    lang = "";
    rate = 1;
    pitch = 1;
    volume = 1;
    onstart = null;
    onend = null;
    onerror = null;
    onpause = null;
    onresume = null;
    constructor(text: string) {
      this.text = text;
    }
  }
  (globalThis as { SpeechSynthesisUtterance?: typeof MockUtterance }).SpeechSynthesisUtterance = MockUtterance;
  return MockUtterance;
}

describe("SpeechOutputSession", () => {
  it("speaks cleaned text and returns to idle on end", () => {
    const utterances: SpeechSynthesisUtteranceLike[] = [];
    const synth = {
      speaking: false,
      paused: false,
      pending: false,
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      speak: vi.fn((utterance: SpeechSynthesisUtteranceLike) => {
        utterances.push(utterance);
        utterance.onstart?.(new Event("start"));
        utterance.onend?.(new Event("end"));
      }),
      getVoices: vi.fn(() => []),
    };

    installMockUtterance();

    const starts: string[] = [];
    const ends: string[] = [];
    const session = new SpeechOutputSession(
      {
        onStart: () => starts.push("start"),
        onEnd: () => ends.push("end"),
        onPause: () => undefined,
        onResume: () => undefined,
        onError: () => undefined,
      },
      { speechSynthesis: synth } as unknown as SpeechOutputWindow,
    );

    session.speak("The punishment for theft is imprisonment.", "en-IN");
    expect(synth.speak).toHaveBeenCalledOnce();
    expect(utterances[0]?.text).toContain("punishment");
    expect(starts).toEqual(["start"]);
    expect(ends).toEqual(["end"]);
  });

  it("queues long answers as sequential utterances", () => {
    const utterances: SpeechSynthesisUtteranceLike[] = [];
    const synth = {
      speaking: false,
      paused: false,
      pending: false,
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      speak: vi.fn((utterance: SpeechSynthesisUtteranceLike) => {
        utterances.push(utterance);
        utterance.onstart?.(new Event("start"));
        utterance.onend?.(new Event("end"));
      }),
      getVoices: vi.fn(() => []),
    };

    installMockUtterance();

    const ends: string[] = [];
    const session = new SpeechOutputSession(
      {
        onStart: () => undefined,
        onEnd: () => ends.push("end"),
        onPause: () => undefined,
        onResume: () => undefined,
        onError: () => undefined,
      },
      { speechSynthesis: synth } as unknown as SpeechOutputWindow,
    );

    const long = "Sentence one is here. ".repeat(30) + "Done.";
    session.speak(long, "en-IN");
    expect(synth.speak.mock.calls.length).toBeGreaterThan(1);
    expect(ends).toEqual(["end"]);
  });

  it("clears remaining queue on stop", () => {
    const synth = {
      speaking: true,
      paused: false,
      pending: false,
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      speak: vi.fn((utterance: SpeechSynthesisUtteranceLike) => {
        utterance.onstart?.(new Event("start"));
        // Do not auto-end — simulate mid-playback stop
      }),
      getVoices: vi.fn(() => []),
    };

    installMockUtterance();

    const session = new SpeechOutputSession(
      {
        onStart: () => undefined,
        onEnd: () => undefined,
        onPause: () => undefined,
        onResume: () => undefined,
        onError: () => undefined,
      },
      { speechSynthesis: synth } as unknown as SpeechOutputWindow,
    );

    session.speak("Sentence one. ".repeat(40), "en-IN");
    expect(synth.speak).toHaveBeenCalledOnce();
    session.stop();
    expect(synth.cancel).toHaveBeenCalled();
  });

  it("supports pause, resume, stop, and replay", () => {
    const synth = {
      speaking: true,
      paused: false,
      pending: false,
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      speak: vi.fn(),
      getVoices: vi.fn(() => []),
    };

    installMockUtterance();

    const session = new SpeechOutputSession(
      {
        onStart: () => undefined,
        onEnd: () => undefined,
        onPause: () => undefined,
        onResume: () => undefined,
        onError: () => undefined,
      },
      { speechSynthesis: synth } as unknown as SpeechOutputWindow,
    );

    session.speak("Answer text", "en-IN");
    session.pause();
    session.resume();
    session.stop();
    session.replay();
    expect(synth.pause).toHaveBeenCalled();
    expect(synth.resume).toHaveBeenCalled();
    expect(synth.cancel).toHaveBeenCalled();
    expect(synth.speak).toHaveBeenCalledTimes(2);
  });
});
