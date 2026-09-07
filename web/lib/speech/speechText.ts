/**
 * Deterministic text preparation for text-to-speech.
 * Strips citations, URLs, and markdown without calling an LLM.
 */

/** Remove citation markers such as [1], [SOURCE 1], [12]. */
export function stripCitationMarkers(text: string): string {
  return text
    .replace(/\[SOURCE\s+\d+\]/gi, "")
    .replace(/\[\d+\]/g, "")
    .replace(/\(\s*\d+\s*\)/g, (match) => (match.length <= 5 ? "" : match));
}

/** Remove URLs and bare domain-like tokens unsuitable for speech. */
export function stripUrls(text: string): string {
  return text
    .replace(/https?:\/\/[^\s]+/gi, "")
    .replace(/www\.[^\s]+/gi, "");
}

/** Flatten common markdown to plain prose. */
export function stripMarkdown(text: string): string {
  return text
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/^\s*>\s+/gm, "")
    .replace(/\|/g, " ")
    .replace(/-{3,}/g, " ");
}

/** Collapse whitespace for natural TTS pacing. */
export function normalizeWhitespace(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/**
 * Produce a speech-friendly version of an assistant answer.
 * Visual citations remain in the UI; spoken output is answer prose only.
 */
export function prepareTextForSpeech(answer: string): string {
  if (!answer.trim()) return "";

  let text = answer;
  text = stripCitationMarkers(text);
  text = stripUrls(text);
  text = stripMarkdown(text);
  text = normalizeWhitespace(text);

  return text;
}

/** Default max characters per SpeechSynthesis utterance chunk. */
export const SPEECH_SEGMENT_MAX_CHARS = 450;

/**
 * Split prepared prose into short utterance segments for more reliable TTS.
 * Does not summarize or alter legal meaning — only sentence-aware chunking.
 */
export function segmentSpeechText(
  text: string,
  maxChars: number = SPEECH_SEGMENT_MAX_CHARS,
): string[] {
  const normalized = normalizeWhitespace(text);
  if (!normalized) return [];
  if (normalized.length <= maxChars) return [normalized];

  const sentences = normalized.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [normalized];
  const segments: string[] = [];
  let current = "";

  for (const raw of sentences) {
    const sentence = raw.trim();
    if (!sentence) continue;

    if (sentence.length > maxChars) {
      if (current) {
        segments.push(current);
        current = "";
      }
      for (let i = 0; i < sentence.length; i += maxChars) {
        segments.push(sentence.slice(i, i + maxChars).trim());
      }
      continue;
    }

    const next = current ? `${current} ${sentence}` : sentence;
    if (next.length > maxChars) {
      segments.push(current);
      current = sentence;
    } else {
      current = next;
    }
  }

  if (current) segments.push(current);
  return segments.filter(Boolean);
}
