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

export function peekStoredLanguage(): LanguageCode | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isLanguageCode(raw) ? raw : null;
  } catch {
    return null;
  }
}

export function readStoredLanguage(): LanguageCode {
  return peekStoredLanguage() ?? DEFAULT_LANGUAGE;
}

export function resolveActiveLanguage({
  override,
  stored,
  sessionLanguage,
  initialLanguage,
}: {
  override?: LanguageCode | null;
  stored?: LanguageCode | null;
  sessionLanguage?: LanguageCode | null;
  initialLanguage?: string | null;
}): LanguageCode {
  if (isLanguageCode(override)) return override;
  if (isLanguageCode(sessionLanguage)) return sessionLanguage;
  if (isLanguageCode(stored)) return stored;
  if (isLanguageCode(initialLanguage)) return initialLanguage;
  return DEFAULT_LANGUAGE;
}

export function writeStoredLanguage(code: LanguageCode): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, code);
  } catch {
    /* ignore quota / private mode */
  }
}
