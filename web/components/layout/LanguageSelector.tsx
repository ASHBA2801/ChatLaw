"use client";

import { Fragment, useEffect, useId, useMemo, useRef, useState } from "react";

import { CheckIcon, ChevronDownIcon, CloseIcon, GlobeIcon, SearchIcon } from "@/components/chat/ChatIcons";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import {
  formatLanguageLabel,
  getPinnedLanguages,
  LANGUAGES,
  type LanguageCode,
  type LanguageOption,
} from "@/lib/i18n/languages";

/**
 * Language menu: a popover under the button on tablet/desktop, a bottom sheet on phones.
 * It only closes on Escape, on choosing a language, or on an outside click/tap.
 */
export default function LanguageSelector({
  compact = false,
  placement = "bottom",
  variant = "outline",
}: {
  compact?: boolean;
  /** Which side of the button the list opens on (tablet/desktop). Use "top" near the bottom of the screen. */
  placement?: "bottom" | "top";
  /** "ghost" drops the border (used in the chat header). */
  variant?: "outline" | "ghost";
}) {
  const { language, languageOption, setLanguage } = useLanguage();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent | TouchEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("touchstart", onPointer);
    document.addEventListener("keydown", onKey);
    // Focus the search box on larger screens only; on phones it would open the keyboard over the list.
    if (window.matchMedia("(min-width: 640px)").matches) searchRef.current?.focus();
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("touchstart", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  /* After the menu closes, hand focus back to the button unless the user clicked somewhere else. */
  const wasOpenRef = useRef(false);
  useEffect(() => {
    const active = document.activeElement;
    if (wasOpenRef.current && !open && (active === document.body || rootRef.current?.contains(active))) {
      triggerRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  const sections = useMemo<Array<{ label: string | null; items: LanguageOption[] }>>(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      return [
        { label: "Common", items: getPinnedLanguages() },
        { label: "All languages", items: LANGUAGES.filter((lang) => !lang.pinned) },
      ];
    }
    return [
      {
        label: null,
        items: LANGUAGES.filter(
          (lang) =>
            lang.name.toLowerCase().includes(q) ||
            lang.nativeName.toLowerCase().includes(q) ||
            lang.code.toLowerCase().includes(q),
        ),
      },
    ];
  }, [query]);
  const hasResults = sections.some((section) => section.items.length > 0);

  function choose(code: LanguageCode) {
    setLanguage(code);
    setOpen(false);
    setQuery("");
  }

  function moveFocus(from: HTMLElement | null, direction: 1 | -1) {
    const options = Array.from(listRef.current?.querySelectorAll<HTMLElement>('[role="option"]') ?? []);
    if (options.length === 0) return;
    const index = from ? options.indexOf(from) : -1;
    const next = options[index + direction];
    if (next) next.focus();
    else if (direction === -1) searchRef.current?.focus();
  }

  const triggerStyle =
    variant === "ghost"
      ? "hover:bg-[var(--fill)]"
      : "border border-[var(--line-strong)] bg-[var(--surface)] hover:border-[var(--accent)]";

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        aria-label={`Language: ${formatLanguageLabel(languageOption)}`}
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex min-h-10 items-center rounded-lg text-sm font-medium text-[var(--foreground)] ${triggerStyle} ${compact ? "max-w-[7.5rem] gap-1.5 px-2 sm:max-w-[11rem] sm:gap-2 sm:px-3" : "gap-2 px-3"}`}
      >
        <GlobeIcon className="h-4 w-4 shrink-0 text-[var(--ink-muted)]" />
        <span className="truncate" lang={languageOption.bcp47}>
          {compact ? languageOption.nativeName : formatLanguageLabel(languageOption)}
        </span>
        <ChevronDownIcon className={`h-4 w-4 shrink-0 text-[var(--ink-muted)] transition-transform ${open ? "rotate-180" : ""} ${compact ? "hidden sm:block" : ""}`} />
      </button>

      {open ? (
        <>
          <div aria-hidden="true" className="fixed inset-0 z-[65] bg-[#12151c]/40 sm:hidden" onClick={() => setOpen(false)} />
          <div
            id={panelId}
            className={`fixed inset-x-0 bottom-0 z-[70] flex max-h-[80dvh] flex-col overflow-hidden rounded-t-3xl border border-[var(--line)] bg-[var(--surface)] pb-[env(safe-area-inset-bottom)] shadow-[var(--shadow-raised)] sm:absolute sm:inset-x-auto sm:bottom-auto sm:right-0 sm:z-50 sm:max-h-[26rem] sm:w-80 sm:rounded-2xl sm:pb-0 ${
              placement === "top" ? "sm:bottom-full sm:top-auto sm:mb-2" : "sm:top-full sm:mt-2"
            }`}
          >
            <div className="flex items-center justify-between px-4 pt-4 sm:hidden">
              <h2 className="text-base font-semibold">Language</h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close language menu"
                className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-[var(--ink-muted)] hover:bg-[var(--fill)]"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="shrink-0 p-3">
              <label className="relative block">
                <span className="sr-only">Search languages</span>
                <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ink-faint)]" />
                <input
                  ref={searchRef}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      const first = sections.flatMap((section) => section.items)[0];
                      if (first) choose(first.code);
                    } else if (event.key === "ArrowDown") {
                      event.preventDefault();
                      moveFocus(null, 1);
                    }
                  }}
                  placeholder="Search languages"
                  type="search"
                  autoComplete="off"
                  className="h-10 w-full rounded-lg border border-[var(--line)] bg-[var(--background)] pl-9 pr-3 text-sm outline-none placeholder:text-[var(--ink-muted)] focus:border-[var(--accent)] focus-visible:outline-none!"
                />
              </label>
            </div>
            <ul
              ref={listRef}
              role="listbox"
              aria-label="Language"
              onKeyDown={(event) => {
                if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                  event.preventDefault();
                  moveFocus(document.activeElement as HTMLElement, event.key === "ArrowDown" ? 1 : -1);
                }
              }}
              className="chat-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-2 pb-2"
            >
              {hasResults ? (
                sections.map((section) => (
                  <Fragment key={section.label ?? "results"}>
                    {section.label ? (
                      <li role="presentation" className="px-3 pb-1 pt-3 text-xs font-medium text-[var(--ink-muted)]">
                        {section.label}
                      </li>
                    ) : null}
                    {section.items.map((lang) => {
                      const selected = lang.code === language;
                      return (
                        <li key={lang.code} role="presentation">
                          <button
                            type="button"
                            role="option"
                            aria-selected={selected}
                            onClick={() => choose(lang.code)}
                            className={`flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-left text-[15px] ${
                              selected
                                ? "bg-[var(--accent-soft)] font-semibold text-[var(--accent)]"
                                : "hover:bg-[var(--fill)] focus-visible:bg-[var(--fill)]"
                            }`}
                          >
                            <span className="min-w-0 flex-1 truncate" lang={lang.bcp47}>
                              {lang.nativeName}
                            </span>
                            {lang.code !== "en" ? (
                              <span className={`shrink-0 text-xs font-normal ${selected ? "text-[var(--accent)]" : "text-[var(--ink-muted)]"}`}>
                                {lang.name}
                              </span>
                            ) : null}
                            {selected ? <CheckIcon className="h-4 w-4 shrink-0" /> : null}
                          </button>
                        </li>
                      );
                    })}
                  </Fragment>
                ))
              ) : (
                <li role="presentation" className="px-4 py-6 text-center text-sm text-[var(--ink-muted)]">
                  No matching language
                </li>
              )}
            </ul>
          </div>
        </>
      ) : null}
    </div>
  );
}
