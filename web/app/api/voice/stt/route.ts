import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const GEMINI_STT_MODEL = process.env.GEMINI_STT_MODEL || "gemini-2.5-flash";
const MAX_AUDIO_BYTES = 16 * 1024 * 1024; // 16 MB

const LANGUAGE_NAME_MAP: Record<string, string> = {
  ta: "Tamil",
  hi: "Hindi",
  te: "Telugu",
  kn: "Kannada",
  ml: "Malayalam",
  mr: "Marathi",
  bn: "Bengali",
  gu: "Gujarati",
  pa: "Punjabi",
  ur: "Urdu",
  en: "English",
  as: "Assamese",
  or: "Odia",
};

function normalizeMimeType(mime: string): string {
  const base = mime.split(";")[0]?.trim().toLowerCase();
  if (base === "audio/webm" || base === "audio/mp4" || base === "audio/ogg" || base === "audio/wav") {
    return base;
  }
  if (base === "audio/x-m4a" || base === "audio/m4a") return "audio/mp4";
  return "audio/webm";
}

export async function POST(request: NextRequest) {
  try {
    const apiKey = process.env.GEMINI_API_KEY?.trim();
    if (!apiKey) {
      return NextResponse.json(
        { error: "Voice transcription service is not configured (GEMINI_API_KEY missing)." },
        { status: 503 },
      );
    }

    const formData = await request.formData();
    const audioEntry = formData.get("audio");
    const languageHint = (formData.get("language") as string | null)?.trim() || "";

    if (!audioEntry || !(audioEntry instanceof Blob)) {
      return NextResponse.json(
        { error: "No audio file was attached to the request." },
        { status: 400 },
      );
    }

    const arrayBuffer = await audioEntry.arrayBuffer();
    if (arrayBuffer.byteLength === 0) {
      return NextResponse.json(
        { error: "Uploaded audio file is empty." },
        { status: 400 },
      );
    }

    if (arrayBuffer.byteLength > MAX_AUDIO_BYTES) {
      return NextResponse.json(
        { error: "Audio file exceeds the 16 MB limit." },
        { status: 413 },
      );
    }

    const rawMime = audioEntry.type || "audio/webm";
    const mimeType = normalizeMimeType(rawMime);
    const base64Audio = Buffer.from(arrayBuffer).toString("base64");

    const langName = languageHint ? LANGUAGE_NAME_MAP[languageHint.slice(0, 2).toLowerCase()] || languageHint : "";
    const promptText = `You are ChatLaw's multilingual Indian speech recognition system.
Listen to this audio recording carefully.
Task:
1. Transcribe the spoken speech verbatim in its authentic original language and native script.
2. If the speaker speaks Tamil, transcribe in Tamil script (தமிழ்).
3. If the speaker speaks Hindi, transcribe in Devanagari script (हिन्दी).
4. If Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, or Urdu, transcribe in its native script.
5. If English, transcribe in English.
6. DO NOT translate the speech to English or any other language.
7. Preserve the exact legal terms, numbers, amounts, dates, and locations mentioned.
${langName ? `Preferred Language Hint: The user has selected ${langName} (${languageHint}). Prioritize this language if matching.` : ""}
8. If the audio is silent, unintelligible, or contains only background noise without human speech, return an empty transcript.

Return strictly a JSON object with this exact schema:
{
  "transcript": string,
  "detectedLanguage": string, // ISO 2-letter code e.g. "ta", "hi", "te", "en", "kn", "ml", "mr", "bn", "gu", "pa", "ur"
  "confidence": number // float between 0.0 and 1.0
}`;

    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_STT_MODEL}:generateContent?key=${apiKey}`;

    const response = await fetch(geminiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                inlineData: {
                  mimeType,
                  data: base64Audio,
                },
              },
              {
                text: promptText,
              },
            ],
          },
        ],
        generationConfig: {
          responseMimeType: "application/json",
          temperature: 0.0,
        },
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("[STT] Gemini API error:", response.status, errText);
      return NextResponse.json(
        { error: "Speech recognition service encountered an error. Please try again." },
        { status: 502 },
      );
    }

    const payload = (await response.json()) as {
      candidates?: Array<{
        content?: {
          parts?: Array<{ text?: string }>;
        };
      }>;
    };

    const rawJson = payload.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
    if (!rawJson) {
      return NextResponse.json({
        transcript: "",
        detectedLanguage: languageHint || "en",
        confidence: 0,
      });
    }

    let parsed: { transcript?: string; detectedLanguage?: string; confidence?: number };
    try {
      parsed = JSON.parse(rawJson);
    } catch {
      // Fallback if returned as raw string
      parsed = { transcript: rawJson, detectedLanguage: languageHint || "en", confidence: 0.9 };
    }

    const transcript = (parsed.transcript || "").trim();
    const detectedLanguage = (parsed.detectedLanguage || languageHint || "en").toLowerCase();

    return NextResponse.json({
      transcript,
      detectedLanguage,
      confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.95,
    });
  } catch (error) {
    console.error("[STT] Unhandled error:", error);
    return NextResponse.json(
      { error: "Failed to process audio recording." },
      { status: 500 },
    );
  }
}
