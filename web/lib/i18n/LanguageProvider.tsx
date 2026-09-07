"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { useSession } from "next-auth/react";

import {
  getLanguage,
  isLanguageCode,
  peekStoredLanguage,
  resolveActiveLanguage,
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

function readLanguageSnapshot(): LanguageCode | null {
  return peekStoredLanguage();
}

function getServerSnapshot(): LanguageCode | null {
  return null;
}

export function LanguageProvider({
  children,
  initialLanguage,
}: {
  children: React.ReactNode;
  initialLanguage?: string | null;
}) {
  const session = useSession();
  const updateSession = session.update;
  const [override, setOverride] = useState<LanguageCode | null>(null);
  const stored = useSyncExternalStore(subscribeLanguage, readLanguageSnapshot, getServerSnapshot);
  const sessionLanguage =
    session.status === "authenticated" &&
    isLanguageCode((session.data?.user as { preferredLanguage?: string } | undefined)?.preferredLanguage)
      ? ((session.data?.user as { preferredLanguage?: string }).preferredLanguage as LanguageCode)
      : null;
  const language = resolveActiveLanguage({
    override,
    stored,
    sessionLanguage,
    initialLanguage,
  });

  useEffect(() => {
    document.documentElement.lang = getLanguage(language).bcp47;
  }, [language]);

  const setLanguage = useCallback(
    (code: LanguageCode) => {
      setOverride(code);
      writeStoredLanguage(code);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("chatlaw-language-change"));
      }
      if (session.status === "authenticated") {
        void fetch("/api/account/language", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ language: code }),
        })
          .then((response) => {
            if (response.ok) return updateSession();
          })
          .catch(() => {
            /* preference sync is best-effort */
          });
      }
    },
    [session.status, updateSession],
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
