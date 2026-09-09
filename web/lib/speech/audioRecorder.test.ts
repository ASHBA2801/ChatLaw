import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  AudioRecorderSession,
  getSupportedAudioMimeType,
  isAudioRecordingSupported,
} from "./audioRecorder";

describe("audioRecorder - MIME type and capability detection", () => {
  it("identifies supported MIME types from candidate list", () => {
    const mockRecorder = {
      isTypeSupported: vi.fn((type: string) => type === "audio/webm;codecs=opus"),
    } as unknown as typeof MediaRecorder;

    expect(getSupportedAudioMimeType(mockRecorder)).toBe("audio/webm;codecs=opus");
  });

  it("falls back to empty string when no mime is supported", () => {
    const mockRecorder = {
      isTypeSupported: vi.fn(() => false),
    } as unknown as typeof MediaRecorder;

    expect(getSupportedAudioMimeType(mockRecorder)).toBe("");
  });

  it("checks audio recording support on a window object", () => {
    const win = {
      navigator: {
        mediaDevices: {
          getUserMedia: vi.fn(),
        },
      },
      MediaRecorder: class {},
    } as unknown as Window;

    expect(isAudioRecordingSupported(win)).toBe(true);
    expect(isAudioRecordingSupported(undefined)).toBe(false);
  });
});

describe("audioRecorder - Recording lifecycle & errors", () => {
  let mockTrack: { stop: ReturnType<typeof vi.fn> };
  let mockStream: { getTracks: () => Array<{ stop: ReturnType<typeof vi.fn> }> };
  let mockWin: Window;

  beforeEach(() => {
    mockTrack = { stop: vi.fn() };
    mockStream = { getTracks: () => [mockTrack] };

    class MockRecorder {
      state = "inactive";
      mimeType = "audio/webm";
      ondataavailable: ((e: { data: Blob }) => void) | null = null;
      onstop: (() => void) | null = null;
      onerror: (() => void) | null = null;

      static isTypeSupported = vi.fn().mockReturnValue(true);

      start() {
        this.state = "recording";
      }

      stop() {
        this.state = "inactive";
        if (this.ondataavailable) {
          this.ondataavailable({ data: new Blob(["audio-data"], { type: "audio/webm" }) });
        }
        if (this.onstop) {
          this.onstop();
        }
      }
    }

    mockWin = {
      isSecureContext: true,
      location: { hostname: "localhost" },
      navigator: {
        mediaDevices: {
          getUserMedia: vi.fn().mockResolvedValue(mockStream),
        },
      },
      MediaRecorder: MockRecorder,
    } as unknown as Window;
  });

  it("records audio, stops, and yields blob with duration", async () => {
    const onStart = vi.fn();
    const onStop = vi.fn();
    const session = new AudioRecorderSession({ onStart, onStop }, 60_000, mockWin);

    await session.start();
    expect(session.active).toBe(true);
    expect(onStart).toHaveBeenCalled();

    const result = await session.stop();
    expect(result).not.toBeNull();
    expect(result?.blob.size).toBeGreaterThan(0);
    expect(session.active).toBe(false);
    expect(mockTrack.stop).toHaveBeenCalled();
  });

  it("handles microphone permission denied error cleanly", async () => {
    const permError = new Error("Permission denied");
    permError.name = "NotAllowedError";
    mockWin.navigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(permError);

    const onError = vi.fn();
    const session = new AudioRecorderSession({ onError }, 60_000, mockWin);

    await session.start();
    expect(onError).toHaveBeenCalledWith(
      expect.stringContaining("ChatLaw cannot access your microphone"),
    );
    expect(session.active).toBe(false);
  });

  it("handles missing microphone error cleanly", async () => {
    const notFoundError = new Error("No device");
    notFoundError.name = "NotFoundError";
    mockWin.navigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(notFoundError);

    const onError = vi.fn();
    const session = new AudioRecorderSession({ onError }, 60_000, mockWin);

    await session.start();
    expect(onError).toHaveBeenCalledWith(
      expect.stringContaining("No microphone was detected on this device"),
    );
  });

  it("cancels recording and releases hardware stream immediately", async () => {
    const session = new AudioRecorderSession({}, 60_000, mockWin);
    await session.start();
    expect(session.active).toBe(true);

    session.cancel();
    expect(session.active).toBe(false);
    expect(mockTrack.stop).toHaveBeenCalled();
  });
});
