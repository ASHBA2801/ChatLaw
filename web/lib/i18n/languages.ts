import catalog from "./catalog.json";

export type LanguageCode =
  | "en"
  | "as"
  | "bn"
  | "brx"
  | "doi"
  | "gu"
  | "hi"
  | "kn"
  | "ks"
  | "kok"
  | "mai"
  | "ml"
  | "mni"
  | "mr"
  | "ne"
  | "or"
  | "pa"
  | "sa"
  | "sat"
  | "sd"
  | "ta"
  | "te"
  | "ur";

export type LanguageOption = {
  code: LanguageCode;
  name: string;
  nativeName: string;
  bcp47: string;
  pinned: boolean;
};

export const LANGUAGE_STORAGE_KEY = "chatlaw-language";
export const DEFAULT_LANGUAGE: LanguageCode = "en";

export const LANGUAGES = catalog as LanguageOption[];

const byCode = new Map(LANGUAGES.map((lang) => [lang.code, lang]));

export function isLanguageCode(value: string | null | undefined): value is LanguageCode {
  return Boolean(value && byCode.has(value as LanguageCode));
}

export function getLanguage(code: string | null | undefined): LanguageOption {
  if (isLanguageCode(code)) return byCode.get(code)!;
  return byCode.get(DEFAULT_LANGUAGE)!;
}

export function getPinnedLanguages(): LanguageOption[] {
  return LANGUAGES.filter((lang) => lang.pinned);
}

export function formatLanguageLabel(lang: LanguageOption): string {
  if (lang.code === "en") return lang.nativeName;
  return `${lang.nativeName} — ${lang.name}`;
}

export function readStoredLanguage(): LanguageCode {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  try {
    const raw = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isLanguageCode(raw) ? raw : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

export function writeStoredLanguage(code: LanguageCode): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, code);
  } catch {
    /* ignore quota / private mode */
  }
}
