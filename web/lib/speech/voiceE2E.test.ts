import { describe, expect, it, vi, beforeEach } from "vitest";
import { normalizeTextForSpeech } from "./speechNormalizer";
import { AudioRecorderSession, isAudioRecordingSupported } from "./audioRecorder";
import { canTransition, voiceStateLabel } from "./voiceState";

describe("Voice Pipeline End-to-End Test Matrix", () => {
  describe("Multilingual Legal Speech Normalization", () => {
    it("normalizes English legal text with currency and section numbers", () => {
      const input = "Under Section 303(2) of BNS, the penalty is ₹18,000 [1]. See https://chatlaw.in";
      const normalized = normalizeTextForSpeech(input);
      expect(normalized).toContain("Section 303, sub-section 2");
      expect(normalized).toContain("Bharatiya Nyaya Sanhita");
      expect(normalized).toContain("eighteen thousand rupees");
      expect(normalized).not.toContain("[1]");
      expect(normalized).not.toContain("https://");
    });

    it("normalizes Tamil legal text and currency symbols", () => {
      const input = "மாத வாடகை ₹25,000 மற்றும் முன்வைப்பு ₹1,50,000 [2].";
      const normalized = normalizeTextForSpeech(input);
      expect(normalized).toContain("twenty five thousand rupees");
      expect(normalized).toContain("one lakh fifty thousand rupees");
      expect(normalized).not.toContain("₹");
      expect(normalized).not.toContain("[2]");
    });

    it("normalizes Hindi legal text with acts and sections", () => {
      const input = "धारा 138 of NI Act के तहत चेक बाउंस का जुर्माना ₹50,000 है [3].";
      const normalized = normalizeTextForSpeech(input);
      expect(normalized).toContain("Negotiable Instruments Act");
      expect(normalized).toContain("fifty thousand rupees");
      expect(normalized).not.toContain("[3]");
    });

    it("normalizes Telugu legal text with legal currency amounts", () => {
      const input = "భారతీయ న్యాయ సంహిత Section 303(1) ప్రకారం ₹5,00,000 జరిమానా.";
      const normalized = normalizeTextForSpeech(input);
      expect(normalized).toContain("Section 303, sub-section 1");
      expect(normalized).toContain("five lakh rupees");
      expect(normalized).not.toContain("₹");
    });
  });

  describe("Brave Browser & Privacy Environment Compatibility", () => {
    it("successfully enables voice recording via MediaRecorder in Brave environment where SpeechRecognition is blocked", () => {
      // In Brave, navigator.brave is truthy and SpeechRecognition is absent/disabled
      const mockBraveWindow = {
        navigator: {
          userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
          brave: {
            isBrave: async () => true,
          },
          mediaDevices: {
            getUserMedia: vi.fn().mockResolvedValue({
              getTracks: () => [{ stop: vi.fn(), enabled: true }],
            }),
          },
        },
        MediaRecorder: class {
          static isTypeSupported = vi.fn().mockReturnValue(true);
          state = "inactive";
          start() { this.state = "recording"; }
          stop() { this.state = "inactive"; }
          addEventListener() {}
          removeEventListener() {}
        },
      } as unknown as Window;

      expect(isAudioRecordingSupported(mockBraveWindow)).toBe(true);

      const recorder = new AudioRecorderSession(
        {
          onStart: vi.fn(),
          onError: vi.fn(),
        },
        mockBraveWindow,
        mockBraveWindow.MediaRecorder as unknown as typeof MediaRecorder,
      );

      expect(recorder).toBeDefined();
    });
  });

  describe("Continuous Voice-to-Voice State Transitions & Interruption", () => {
    it("allows direct transition from transcribing to thinking without manual review", () => {
      expect(canTransition("transcribing", "thinking")).toBe(true);
    });

    it("allows interruption from speaking directly to listening", () => {
      expect(canTransition("speaking", "listening")).toBe(true);
    });

    it("allows interruption from paused directly to listening", () => {
      expect(canTransition("paused", "listening")).toBe(true);
    });

    it("provides human-readable labels for all voice states", () => {
      expect(voiceStateLabel("listening")).toBe("Listening…");
      expect(voiceStateLabel("transcribing")).toBe("Transcribing…");
      expect(voiceStateLabel("thinking")).toBe("Researching…");
      expect(voiceStateLabel("speaking")).toBe("Speaking…");
      expect(voiceStateLabel("ready_to_send")).toBe("Review transcript");
    });
  });
});
