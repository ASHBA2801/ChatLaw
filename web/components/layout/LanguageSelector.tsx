"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

import { useLanguage } from "@/lib/i18n/LanguageProvider";
import {
  formatLanguageLabel,
  getPinnedLanguages,
  LANGUAGES,
  type LanguageCode,
} from "@/lib/i18n/languages";

export default function LanguageSelector({ compact = false }: { compact?: boolean }) {
  const { language, languageOption, setLanguage } = useLanguage();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      const pinned = getPinnedLanguages();
      const rest = LANGUAGES.filter((lang) => !lang.pinned);
      return [...pinned, ...rest];
    }
    return LANGUAGES.filter(
      (lang) =>
        lang.name.toLowerCase().includes(q) ||
        lang.nativeName.toLowerCase().includes(q) ||
        lang.code.toLowerCase().includes(q),
    );
  }, [query]);

  function choose(code: LanguageCode) {
    setLanguage(code);
    setOpen(false);
    setQuery("");
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-11 items-center gap-2 rounded-full border border-[var(--line)] bg-white px-3 text-sm font-medium text-[var(--foreground)] hover:border-[var(--forest)] focus-visible:ring-2 focus-visible:ring-[var(--warm)] ${compact ? "max-w-[9.5rem]" : ""}`}
      >
        <span className="truncate" title={formatLanguageLabel(languageOption)}>
          {compact ? languageOption.nativeName : formatLanguageLabel(languageOption)}
        </span>
        <span aria-hidden className="text-[var(--ink-muted)]">▾</span>
      </button>
      {open ? (
        <div
          id={listId}
          role="listbox"
          aria-label="Language"
          className="absolute right-0 z-50 mt-2 w-[min(18rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-[var(--line)] bg-white shadow-[0_12px_40px_rgba(23,73,54,0.12)]"
        >
          <div className="border-b border-[var(--line)] p-2">
            <label className="sr-only" htmlFor={`${listId}-search`}>
              Search languages
            </label>
            <input
              id={`${listId}-search`}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search languages"
              className="min-h-11 w-full rounded-xl border border-[var(--line)] bg-[var(--background)] px-3 text-sm outline-none focus:border-[var(--forest)]"
              autoFocus
            />
          </div>
          <ul className="max-h-72 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <li className="px-4 py-3 text-sm text-[var(--ink-muted)]">No matching language</li>
            ) : (
              filtered.map((lang) => {
                const selected = lang.code === language;
                return (
                  <li key={lang.code}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={selected}
                      onClick={() => choose(lang.code)}
                      className={`flex min-h-11 w-full items-center justify-between px-4 text-left text-sm ${selected ? "bg-[#eef5d0] font-semibold text-[var(--forest)]" : "hover:bg-[var(--background)]"}`}
                    >
                      <span>{formatLanguageLabel(lang)}</span>
                      {lang.pinned && !query ? (
                        <span className="text-[10px] uppercase tracking-wide text-[var(--ink-muted)]">Common</span>
                      ) : null}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
