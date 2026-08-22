"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";
import { useSession } from "next-auth/react";

import {
  DEFAULT_LANGUAGE,
  getLanguage,
  isLanguageCode,
  LANGUAGE_STORAGE_KEY,
  writeStoredLanguage,
  type LanguageCode,
  type LanguageOption,
} from "./languages";

type LanguageContextValue = {
  language: LanguageCode;
  languageOption: LanguageOption;
  setLanguage: (code: LanguageCode) => void;
  ready: boolean;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function subscribeLanguage(onStoreChange: () => void) {
  if (typeof window === "undefined") return () => undefined;
  const handler = () => onStoreChange();
  window.addEventListener("storage", handler);
  window.addEventListener("chatlaw-language-change", handler as EventListener);
  return () => {
    window.removeEventListener("storage", handler);
    window.removeEventListener("chatlaw-language-change", handler as EventListener);
  };
}

function readLanguageSnapshot(): LanguageCode {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  try {
    const raw = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isLanguageCode(raw) ? raw : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

function getServerSnapshot(): LanguageCode {
  return DEFAULT_LANGUAGE;
}

export function LanguageProvider({
  children,
  initialLanguage,
}: {
  children: React.ReactNode;
  initialLanguage?: string | null;
}) {
  const session = useSession();
  const stored = useSyncExternalStore(subscribeLanguage, readLanguageSnapshot, getServerSnapshot);
  const sessionLanguage =
    session.status === "authenticated" &&
    isLanguageCode((session.data?.user as { preferredLanguage?: string } | undefined)?.preferredLanguage)
      ? ((session.data?.user as { preferredLanguage?: string }).preferredLanguage as LanguageCode)
      : null;
  const language: LanguageCode = sessionLanguage
    ?? (isLanguageCode(initialLanguage) ? initialLanguage : stored);

  const setLanguage = useCallback(
    (code: LanguageCode) => {
      writeStoredLanguage(code);
      if (typeof document !== "undefined") {
        document.documentElement.lang = getLanguage(code).bcp47;
      }
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("chatlaw-language-change"));
      }
      if (session.status === "authenticated") {
        void fetch("/api/account/language", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ language: code }),
        }).catch(() => {
          /* preference sync is best-effort */
        });
      }
    },
    [session.status],
  );

  const value = useMemo(
    () => ({
      language,
      languageOption: getLanguage(language),
      setLanguage,
      ready: typeof window !== "undefined",
    }),
    [language, setLanguage],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return ctx;
}
