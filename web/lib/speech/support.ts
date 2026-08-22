import catalog from "@/lib/i18n/catalog.json";
import type { SpeechLanguageOption, SpeechRecognitionConstructor, SpeechOutputWindow, SpeechWindow } from "./types";

/**
 * Locales with strong Web Speech support on Chromium-based browsers in India.
 * Other Eighth Schedule locales remain enabled for best-effort attempts.
 */
const STRONG_SUPPORT = new Set([
  "en-IN",
  "en-US",
  "hi-IN",
  "ta-IN",
  "te-IN",
  "kn-IN",
  "ml-IN",
  "mr-IN",
  "bn-IN",
  "gu-IN",
  "pa-IN",
  "ur-IN",
]);

/** Fallback BCP-47 tags when the catalog locale is unlikely to be installed. */
const SPEECH_FALLBACK: Record<string, string> = {
  "as-IN": "hi-IN",
  "brx-IN": "hi-IN",
  "doi-IN": "hi-IN",
  "ks-IN": "ur-IN",
  "kok-IN": "mr-IN",
  "mai-IN": "hi-IN",
  "mni-IN": "en-IN",
  "ne-IN": "hi-IN",
  "or-IN": "hi-IN",
  "sa-IN": "hi-IN",
  "sat-IN": "hi-IN",
  "sd-IN": "ur-IN",
};

export const SPEECH_LANGUAGE_OPTIONS: SpeechLanguageOption[] = [
  { code: "en-US", label: "English (US)", enabled: true, chatLanguageCode: "en" },
  ...catalog.map((lang) => ({
    code: lang.bcp47,
    label: lang.code === "en" ? "English (India)" : `${lang.nativeName} — ${lang.name}`,
    // Enable every Eighth Schedule language for best-effort STT/TTS.
    enabled: true,
    chatLanguageCode: lang.code,
  })),
];

export const DEFAULT_SPEECH_LANGUAGE = "en-IN";

export function chatLanguageToSpeechCode(chatCode: string): string {
  const match = SPEECH_LANGUAGE_OPTIONS.find((option) => option.chatLanguageCode === chatCode);
  return match?.code ?? DEFAULT_SPEECH_LANGUAGE;
}

export function speechCodeToChatLanguage(speechCode: string): string {
  const match = SPEECH_LANGUAGE_OPTIONS.find((option) => option.code === speechCode);
  return match?.chatLanguageCode ?? "en";
}

export function resolveSpeechLocale(preferred: string): { locale: string; usedFallback: boolean } {
  if (STRONG_SUPPORT.has(preferred)) return { locale: preferred, usedFallback: false };
  const voices =
    typeof window !== "undefined"
      ? (((window as unknown as SpeechOutputWindow).speechSynthesis?.getVoices() ?? []) as Array<{
          lang: string;
        }>)
      : [];
  const exact = voices.some((voice) => voice.lang.toLowerCase() === preferred.toLowerCase());
  if (exact) return { locale: preferred, usedFallback: false };
  const prefix = preferred.split("-")[0]?.toLowerCase();
  const prefixMatch = voices.find((voice) => voice.lang.toLowerCase().startsWith(`${prefix}-`));
  if (prefixMatch) return { locale: prefixMatch.lang, usedFallback: prefixMatch.lang !== preferred };
  const mapped = SPEECH_FALLBACK[preferred];
  if (mapped) return { locale: mapped, usedFallback: true };
  return { locale: DEFAULT_SPEECH_LANGUAGE, usedFallback: true };
}

export function isSpeechLocaleLikelySupported(bcp47: string): boolean {
  if (STRONG_SUPPORT.has(bcp47)) return true;
  if (typeof window === "undefined") return false;
  const voices = (window as unknown as SpeechOutputWindow).speechSynthesis?.getVoices() ?? [];
  const prefix = bcp47.split("-")[0]?.toLowerCase();
  return voices.some(
    (voice) =>
      voice.lang.toLowerCase() === bcp47.toLowerCase() ||
      voice.lang.toLowerCase().startsWith(`${prefix}-`),
  );
}

export function getSpeechRecognitionConstructor(
  win: SpeechWindow | undefined = typeof window !== "undefined" ? (window as SpeechWindow) : undefined,
): SpeechRecognitionConstructor | null {
  if (!win) return null;
  return win.SpeechRecognition ?? win.webkitSpeechRecognition ?? null;
}

export function isSpeechRecognitionSupported(
  win: SpeechWindow | undefined = typeof window !== "undefined" ? (window as SpeechWindow) : undefined,
): boolean {
  return getSpeechRecognitionConstructor(win) !== null;
}

export function getEnabledSpeechLanguages(): SpeechLanguageOption[] {
  return SPEECH_LANGUAGE_OPTIONS.filter((option) => option.enabled);
}
