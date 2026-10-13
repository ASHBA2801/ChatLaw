import { afterEach, describe, expect, it, vi } from "vitest";

const resolvers: Array<(value: { audioUrl: string; blob: Blob; voice: string; cleanup: () => void }) => void> = [];
const played: string[] = [];

vi.mock("./synthesize", () => ({
  synthesizeSpeechAudio: vi.fn(
    () =>
      new Promise((resolve) => {
        resolvers.push(resolve as never);
      }),
  ),
  playSynthesizedAudio: vi.fn((url: string, options: { onStart?: () => void }) => {
    played.push(url);
    options.onStart?.();
    return { pause: vi.fn(), resume: vi.fn(), stop: vi.fn(), element: {} };
  }),
}));

import { SpeechOutputSession } from "./SpeechOutputSession";

function audio(url: string) {
  return { audioUrl: url, blob: new Blob(), voice: "v", cleanup: vi.fn() };
}

describe("SpeechOutputSession single voice", () => {
  afterEach(() => {
    resolvers.length = 0;
    played.length = 0;
    vi.unstubAllGlobals();
  });

  it("plays only the latest request when speak() is called repeatedly", async () => {
    vi.stubGlobal("window", {});
    vi.stubGlobal("fetch", vi.fn());
    const loading = vi.fn();
    const session = new SpeechOutputSession(
      { onLoading: loading, onStart: vi.fn(), onEnd: vi.fn(), onPause: vi.fn(), onResume: vi.fn(), onError: vi.fn() },
      { speechSynthesis: undefined },
    );

    session.speak("first answer", "en-IN");
    session.speak("first answer", "en-IN");
    session.speak("second answer", "en-IN");
    expect(loading).toHaveBeenCalledTimes(3);

    // Responses arrive out of order; only the newest may play.
    resolvers[2](audio("blob:third"));
    resolvers[0](audio("blob:first"));
    resolvers[1](audio("blob:second"));
    await Promise.resolve();
    await Promise.resolve();

    expect(played).toEqual(["blob:third"]);
  });

  it("does not play audio that finishes loading after stop()", async () => {
    vi.stubGlobal("window", {});
    vi.stubGlobal("fetch", vi.fn());
    const session = new SpeechOutputSession(
      { onStart: vi.fn(), onEnd: vi.fn(), onPause: vi.fn(), onResume: vi.fn(), onError: vi.fn() },
      { speechSynthesis: undefined },
    );
    session.speak("hello there", "en-IN");
    session.stop();
    resolvers[0](audio("blob:late"));
    await Promise.resolve();
    await Promise.resolve();
    expect(played).toEqual([]);
  });
});
