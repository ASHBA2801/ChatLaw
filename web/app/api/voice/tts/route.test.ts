import { describe, expect, it, vi, beforeEach } from "vitest";
import { POST } from "./route";
import { NextRequest } from "next/server";

describe("POST /api/voice/tts", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetAllMocks();
    process.env = {
      ...originalEnv,
      RAG_API_URL: "http://127.0.0.1:8000",
      RAG_API_SECRET: "test-rag-secret",
    };
  });

  it("returns 400 when text is empty", async () => {
    const req = new NextRequest("http://localhost:3000/api/voice/tts", {
      method: "POST",
      body: JSON.stringify({ text: "   ", language: "ta" }),
    });

    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toContain("Text is required");
  });

  it("returns 503 when RAG_API_URL is missing", async () => {
    delete process.env.RAG_API_URL;

    const req = new NextRequest("http://localhost:3000/api/voice/tts", {
      method: "POST",
      body: JSON.stringify({ text: "Hello", language: "en" }),
    });

    const res = await POST(req);
    expect(res.status).toBe(503);
    const data = await res.json();
    expect(data.error).toContain("RAG audio service is not configured");
  });

  it("calls RAG service with normalized legal text and returns audio stream", async () => {
    const mockAudioBytes = new Uint8Array([0xff, 0xfb, 0x90, 0x64]); // fake mp3 frame
    // @ts-expect-error mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({
        "content-type": "audio/mpeg",
        "x-chatlaw-voice": "ta-IN-ValluvarNeural",
      }),
      arrayBuffer: async () => mockAudioBytes.buffer,
    });

    const req = new NextRequest("http://localhost:3000/api/voice/tts", {
      method: "POST",
      body: JSON.stringify({
        text: "Section 303(2) of BNS: rent is ₹18,000 [1].",
        language: "ta",
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toBe("audio/mpeg");
    expect(res.headers.get("x-chatlaw-voice")).toBe("ta-IN-ValluvarNeural");

    // Verify fetch was called with normalized speech text
    expect(global.fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/voice/tts",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer test-rag-secret",
        }),
        body: expect.stringContaining("Section 303, sub-section 2"),
      }),
    );
  });
});
