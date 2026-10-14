"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentType } from "react";
import { signIn, signOut, useSession } from "next-auth/react";

import { CloseIcon, PlusIcon, SidebarIcon } from "@/components/chat/ChatIcons";
import BrandMark from "@/components/layout/BrandMark";
import { ChatSidebarContext, type ChatSidebarContextValue } from "@/components/layout/ChatSidebarContext";
import LanguageSelector from "@/components/layout/LanguageSelector";
import {
  AccountNavIcon,
  CasesNavIcon,
  ChatNavIcon,
  DocumentsNavIcon,
  ResearchNavIcon,
} from "@/components/layout/NavIcons";

const NAV = [
  { href: "/chat", label: "Chat", hint: "Legal assistant", Icon: ChatNavIcon },
  { href: "/documents", label: "Documents", hint: "Draft generator", Icon: DocumentsNavIcon },
  { href: "/cases", label: "Cases", hint: "Your matters", Icon: CasesNavIcon },
  { href: "/research", label: "Research", hint: "Find sources", Icon: ResearchNavIcon },
] as const satisfies ReadonlyArray<{
  href: string;
  label: string;
  hint: string;
  Icon: ComponentType<{ className?: string }>;
}>;

const NAV_MINIMIZED_KEY = "chatlaw-nav-minimized";

function navActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function AppShell({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const session = useSession();
  const user = session.data?.user;
  const [isNavMinimized, setIsNavMinimized] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [slot, setSlot] = useState<HTMLElement | null>(null);
  const newChatRef = useRef<(() => void) | null>(null);
  const signInTarget = useMemo(() => {
    const query = searchParams.toString();
    return query ? `${pathname}?${query}` : pathname;
  }, [pathname, searchParams]);
  const isChatPage = pathname.startsWith("/chat");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(NAV_MINIMIZED_KEY);
      if (stored === "1") setIsNavMinimized(true);
      const legacy = window.localStorage.getItem("chatlaw-nav-collapsed");
      if (legacy === "1") {
        setIsNavMinimized(true);
        window.localStorage.setItem(NAV_MINIMIZED_KEY, "1");
        window.localStorage.removeItem("chatlaw-nav-collapsed");
      }
    } catch {
      /* ignore */
    }
  }, []);

  const setNavMinimized = (next: boolean) => {
    setIsNavMinimized(next);
    try {
      window.localStorage.setItem(NAV_MINIMIZED_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
  };

  const pageTitle =
    title ??
    NAV.find((item) => navActive(pathname, item.href))?.label ??
    (pathname.startsWith("/account") ? "Account" : "ChatLaw");

  const accountActive = pathname.startsWith("/account");
  const authed = session.status === "authenticated" && Boolean(user);
  const signedOut = session.status === "unauthenticated";
  const accountLabel = signedOut ? "Sign in" : user?.name || user?.email || "Account";
  const initial = (user?.name || user?.email || "?").trim().charAt(0).toUpperCase();
  const registerNewChat = useCallback((handler: (() => void) | null) => {
    newChatRef.current = handler;
  }, []);
  const openSidebar = useCallback(() => setMobileOpen(true), []);
  const closeSidebar = useCallback(() => setMobileOpen(false), []);
  const sidebarContext = useMemo<ChatSidebarContextValue>(
    () => ({ slot, openSidebar, closeSidebar, registerNewChat }),
    [slot, openSidebar, closeSidebar, registerNewChat],
  );

  useEffect(() => {
    if (!mobileOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen]);

  /** Collapsed state only applies on desktop (lg+); the mobile drawer always shows full labels. */
  const labelClass = "min-w-0 truncate group-data-[compact=true]/sb:lg:hidden";
  const rowClass = (active: boolean) =>
    `flex h-10 w-full items-center gap-3 rounded-lg px-2.5 text-sm font-medium group-data-[compact=true]/sb:lg:justify-center group-data-[compact=true]/sb:lg:px-0 ${
      active
        ? "bg-[var(--accent-soft)] text-[var(--accent)]"
        : "text-[var(--foreground)] hover:bg-[var(--line)]/50"
    }`;
  const iconButton =
    "inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-[var(--ink-muted)] hover:bg-[var(--line)]/50 hover:text-[var(--foreground)]";

  const newChatLabel = (
    <>
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-[var(--on-accent)]">
        <PlusIcon className="h-4 w-4" />
      </span>
      <span className={labelClass}>New chat</span>
    </>
  );

  return (
    <ChatSidebarContext.Provider value={sidebarContext}>
    <div
      className={
        isChatPage
          ? "flex h-dvh overflow-hidden bg-[var(--background)]"
          : "min-h-screen bg-[var(--background)] lg:flex"
      }
    >
      <aside
        data-compact={isNavMinimized}
        className={`group/sb shrink-0 flex-col border-r border-[var(--line)] ${
          isChatPage
            ? `fixed inset-y-0 left-0 z-[60] flex w-[85%] max-w-xs bg-[var(--background)] pt-[env(safe-area-inset-top)] transition-[transform,visibility] duration-200 ease-out lg:static lg:z-auto lg:h-full lg:w-64 lg:max-w-none lg:translate-x-0 lg:pt-0 lg:visible ${
                mobileOpen ? "visible translate-x-0 shadow-[var(--shadow-raised)]" : "invisible -translate-x-full"
              }`
            : "hidden bg-[var(--surface)] lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64"
        } lg:data-[compact=true]:w-[4.25rem]`}
        aria-label="Product menu"
      >
        <div className="flex h-14 shrink-0 items-center justify-between gap-2 px-3 group-data-[compact=true]/sb:lg:h-auto group-data-[compact=true]/sb:lg:flex-col group-data-[compact=true]/sb:lg:justify-center group-data-[compact=true]/sb:lg:py-3">
          <BrandMark labelClassName="group-data-[compact=true]/sb:lg:hidden" />
          <button
            type="button"
            onClick={() => setNavMinimized(!isNavMinimized)}
            aria-label={isNavMinimized ? "Expand sidebar" : "Collapse sidebar"}
            title={isNavMinimized ? "Expand sidebar" : "Collapse sidebar"}
            className={`${iconButton} max-lg:hidden`}
          >
            <SidebarIcon className="h-5 w-5" />
          </button>
          {isChatPage ? (
            <button type="button" onClick={closeSidebar} aria-label="Close menu" className={`${iconButton} lg:hidden`}>
              <CloseIcon className="h-5 w-5" />
            </button>
          ) : null}
        </div>

        <div className="shrink-0 px-2 pb-1 pt-1">
          {isChatPage ? (
            <button
              type="button"
              onClick={() => newChatRef.current?.()}
              title="New chat"
              className={`${rowClass(false)} !font-semibold`}
            >
              {newChatLabel}
            </button>
          ) : (
            <Link href="/chat" title="New chat" className={`${rowClass(false)} !font-semibold`}>
              {newChatLabel}
            </Link>
          )}
        </div>

        <nav aria-label="Primary" className="flex shrink-0 flex-col gap-0.5 px-2 pt-1">
          {NAV.map((item) => {
            const active = navActive(pathname, item.href);
            const Icon = item.Icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeSidebar}
                aria-current={active ? "page" : undefined}
                title={`${item.label} — ${item.hint}`}
                className={rowClass(active)}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className={labelClass}>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {isChatPage ? (
          <div ref={setSlot} className="flex min-h-0 flex-1 flex-col group-data-[compact=true]/sb:lg:hidden" />
        ) : (
          <div className="flex-1" />
        )}

        <div className="mt-auto shrink-0 border-t border-[var(--line)] p-2">
          {!signedOut ? (
            <Link
              href="/account"
              onClick={closeSidebar}
              aria-current={accountActive ? "page" : undefined}
              title={accountLabel}
              className={rowClass(accountActive)}
            >
              <span
                aria-hidden="true"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-semibold text-[var(--on-accent)]"
              >
                {user ? initial : <AccountNavIcon className="h-4 w-4" />}
              </span>
              <span className={labelClass}>{accountLabel}</span>
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => signIn("google", { callbackUrl: signInTarget })}
              title="Sign in"
              className={rowClass(false)}
            >
              <AccountNavIcon className="h-5 w-5 shrink-0" />
              <span className={labelClass}>Sign in</span>
            </button>
          )}
        </div>
      </aside>
      {isChatPage && mobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-[55] bg-[#12151c]/45 lg:hidden"
          onClick={closeSidebar}
          aria-label="Close menu"
        />
      ) : null}

      {/* Below lg the fixed bottom navigation covers the bottom 3.5rem, plus the home indicator. */}
      <div
        className={`flex min-w-0 flex-1 flex-col ${
          isChatPage ? "min-h-0 overflow-hidden" : "pb-[calc(4rem+env(safe-area-inset-bottom))] lg:pb-0"
        }`}
      >
        {isChatPage ? null : (
          <header className="sticky top-0 z-30 shrink-0 border-b border-[var(--line)] bg-[var(--surface)] pt-[env(safe-area-inset-top)]">
            <div className="flex h-14 items-center justify-between gap-2 px-3 sm:px-5">
              <div className="flex min-w-0 items-center gap-2">
                <div className="min-w-0 lg:hidden">
                  <BrandMark />
                </div>
                {title ? (
                  <div className="hidden min-w-0 lg:block">
                    <p className="truncate text-base font-semibold tracking-tight">{pageTitle}</p>
                    {subtitle ? <p className="truncate text-xs text-[var(--ink-muted)]">{subtitle}</p> : null}
                  </div>
                ) : null}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <LanguageSelector compact />
                {authed ? (
                  <button
                    type="button"
                    onClick={() => signOut({ callbackUrl: "/" })}
                    className="btn-secondary btn-sm !font-medium"
                  >
                    Sign out
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => signIn("google", { callbackUrl: signInTarget })}
                    className="btn-primary btn-sm"
                  >
                    Sign in
                  </button>
                )}
              </div>
            </div>
            {title ? (
              <div className="border-t border-[var(--line)] px-4 py-2 lg:hidden">
                <p className="truncate text-sm font-semibold">{pageTitle}</p>
                {subtitle ? <p className="truncate text-xs text-[var(--ink-muted)]">{subtitle}</p> : null}
              </div>
            ) : null}
          </header>
        )}

        <div className={`flex min-h-0 flex-1 flex-col ${isChatPage ? "overflow-hidden" : ""}`}>
          {children}
        </div>
      </div>

      {isChatPage ? null : (
      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--line)] bg-[var(--surface)]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
      >
        <div className="grid grid-cols-5">
          {[...NAV, { href: "/account", label: signedOut ? "Sign in" : "Account", hint: "", Icon: AccountNavIcon }].map((item) => {
            const active = navActive(pathname, item.href);
            const Icon = item.Icon;
            return (
              <Link
                key={item.href}
                href={signedOut && item.href === "/account" ? `/signin?callbackUrl=${encodeURIComponent(signInTarget)}` : item.href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-14 flex-col items-center justify-center gap-1 text-center text-[11px] font-medium ${active ? "text-[var(--accent)]" : "text-[var(--ink-muted)]"}`}
              >
                <span className={`flex h-7 w-12 items-center justify-center rounded-full ${active ? "bg-[var(--accent-soft)]" : ""}`}>
                  <Icon className="h-5 w-5" />
                </span>
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
      )}
    </div>
    </ChatSidebarContext.Provider>
  );
}
