import { describe, expect, it, vi, beforeEach } from "vitest";
import { POST } from "./route";
import { NextRequest } from "next/server";

describe("POST /api/voice/stt", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetAllMocks();
    process.env = { ...originalEnv, GEMINI_API_KEY: "test-gemini-key" };
  });

  it("returns 400 when no audio is sent", async () => {
    const formData = new FormData();
    formData.append("language", "ta");

    const req = new NextRequest("http://localhost:3000/api/voice/stt", {
      method: "POST",
      body: formData,
    });

    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toContain("No audio file was attached");
  });

  it("returns 400 when audio file is empty", async () => {
    const formData = new FormData();
    const emptyBlob = new Blob([], { type: "audio/webm" });
    formData.append("audio", emptyBlob);

    const req = new NextRequest("http://localhost:3000/api/voice/stt", {
      method: "POST",
      body: formData,
    });

    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toContain("empty");
  });

  it("returns 503 when GEMINI_API_KEY is not configured", async () => {
    delete process.env.GEMINI_API_KEY;

    const formData = new FormData();
    const audioBlob = new Blob(["fake audio data"], { type: "audio/webm" });
    formData.append("audio", audioBlob);

    const req = new NextRequest("http://localhost:3000/api/voice/stt", {
      method: "POST",
      body: formData,
    });

    const res = await POST(req);
    expect(res.status).toBe(503);
    const data = await res.json();
    expect(data.error).toContain("GEMINI_API_KEY missing");
  });

  it("transcribes audio and returns detected language from Gemini", async () => {
    const mockGeminiResponse = {
      candidates: [
        {
          content: {
            parts: [
              {
                text: JSON.stringify({
                  transcript: "என் வீட்டை வாடகைக்கு விட்டிருக்கிறேன்.",
                  detectedLanguage: "ta",
                  confidence: 0.98,
                }),
              },
            ],
          },
        },
      ],
    };

    // @ts-expect-error mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockGeminiResponse,
    });

    const formData = new FormData();
    const audioBlob = new Blob(["mock-pcm-audio-content"], { type: "audio/webm" });
    formData.append("audio", audioBlob);
    formData.append("language", "ta");

    const req = new NextRequest("http://localhost:3000/api/voice/stt", {
      method: "POST",
      body: formData,
    });

    const res = await POST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.transcript).toBe("என் வீட்டை வாடகைக்கு விட்டிருக்கிறேன்.");
    expect(data.detectedLanguage).toBe("ta");
    expect(data.confidence).toBe(0.98);
  });
});
