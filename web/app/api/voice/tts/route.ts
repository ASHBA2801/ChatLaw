import { NextRequest, NextResponse } from "next/server";
import { normalizeTextForSpeech } from "@/lib/speech/speechNormalizer";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json().catch(() => ({}))) as {
      text?: string;
      language?: string;
      voice?: string;
      rate?: string;
    };

    const rawText = (body.text || "").trim();
    if (!rawText) {
      return NextResponse.json({ error: "Text is required for TTS." }, { status: 400 });
    }

    // Preprocess text using our legal normalizer (sections, currencies, abbreviations, markdown)
    const normalizedText = normalizeTextForSpeech(rawText);
    const language = (body.language || "en").toLowerCase().trim();

    const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
    const secret = process.env.RAG_API_SECRET?.trim();

    if (!baseUrl || !secret) {
      return NextResponse.json(
        { error: "RAG audio service is not configured (RAG_API_URL missing)." },
        { status: 503 },
      );
    }

    const ttsUrl = `${baseUrl}/api/voice/tts`;
    const response = await fetch(ttsUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${secret}`,
      },
      body: JSON.stringify({
        text: normalizedText,
        language,
        voice: body.voice,
        rate: body.rate,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("[TTS] RAG service error:", response.status, errText);
      return NextResponse.json(
        { error: "Neural text-to-speech service encountered an error." },
        { status: 502 },
      );
    }

    const audioArrayBuffer = await response.arrayBuffer();
    const contentType = response.headers.get("content-type") || "audio/mpeg";
    const voiceHeader = response.headers.get("x-chatlaw-voice") || "";

    return new NextResponse(audioArrayBuffer, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Length": audioArrayBuffer.byteLength.toString(),
        "X-ChatLaw-Voice": voiceHeader,
        "X-ChatLaw-Language": language,
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch (error) {
    console.error("[TTS] Unhandled error:", error);
    return NextResponse.json(
      { error: "Failed to synthesize speech audio." },
      { status: 500 },
    );
  }
}
