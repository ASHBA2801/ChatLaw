/** Merge a speech transcript into the existing composer text. */

export function mergeTranscript(existing: string, transcript: string, limit: number): string {
  const next = transcript.trim();
  if (!next) return existing.slice(0, limit);

  const base = existing.trimEnd();
  if (!base) return next.slice(0, limit);

  const joined = `${base} ${next}`;
  return joined.slice(0, limit);
}

export function extractTranscriptParts(
  results: { readonly length: number; readonly [index: number]: { readonly isFinal: boolean; readonly length: number; readonly [index: number]: { readonly transcript: string } } },
  resultIndex = 0,
): { finalText: string; interimText: string } {
  let finalText = "";
  let interimText = "";

  for (let i = resultIndex; i < results.length; i += 1) {
    const result = results[i];
    if (!result || result.length === 0) continue;
    const piece = result[0]?.transcript ?? "";
    if (!piece) continue;
    if (result.isFinal) finalText += piece;
    else interimText += piece;
  }

  return {
    finalText: finalText.trim(),
    interimText: interimText.trim(),
  };
}
