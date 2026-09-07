/**
 * Client service for server-side multilingual speech-to-text.
 */

export interface TranscribeAudioResult {
  transcript: string;
  detectedLanguage: string;
  confidence: number;
}

export async function transcribeAudio(
  audioBlob: Blob,
  languageHint?: string,
): Promise<TranscribeAudioResult> {
  const formData = new FormData();
  const ext = audioBlob.type.includes("mp4") ? "mp4" : audioBlob.type.includes("ogg") ? "ogg" : "webm";
  formData.append("audio", audioBlob, `audio-recording.${ext}`);
  if (languageHint) {
    formData.append("language", languageHint);
  }

  const response = await fetch("/api/voice/stt", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = "Speech recognition failed.";
    try {
      const data = await response.json();
      if (data.error) errorDetail = data.error;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  const result = (await response.json()) as TranscribeAudioResult;
  return {
    transcript: (result.transcript || "").trim(),
    detectedLanguage: (result.detectedLanguage || languageHint || "en").toLowerCase(),
    confidence: typeof result.confidence === "number" ? result.confidence : 0.95,
  };
}
