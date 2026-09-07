"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState, type ComponentType } from "react";
import { signIn, signOut, useSession } from "next-auth/react";

import { ChevronLeftIcon, MenuIcon } from "@/components/chat/ChatIcons";
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

  return (
    <div
      className={
        isChatPage
          ? "flex h-dvh flex-col overflow-hidden bg-[var(--background)] lg:flex-row"
          : "min-h-screen bg-[var(--background)] lg:flex"
      }
    >
      <aside
        className={`${isChatPage ? "hidden" : "hidden w-56 shrink-0 flex-col border-r border-[var(--line)] bg-[var(--surface)] lg:flex"} ${
          isNavMinimized ? "lg:hidden" : ""
        }`}
        aria-label="Product menu"
        aria-hidden={isNavMinimized ? true : undefined}
      >
        <div className="flex h-12 items-center justify-between gap-2 border-b border-[var(--line)] px-2">
          <Link href="/" className="flex min-w-0 items-center gap-2 text-sm font-bold tracking-tight">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center bg-[var(--signal)] text-[10px] font-bold text-white">
              CL
            </span>
            <span className="truncate">ChatLaw</span>
          </Link>
          <button
            type="button"
            onClick={() => setNavMinimized(true)}
            className="inline-flex min-h-10 min-w-10 shrink-0 items-center justify-center border border-[var(--line)] text-sm text-[var(--ink-muted)] transition-colors hover:border-[var(--signal)] hover:text-[var(--foreground)] focus-visible:ring-2 focus-visible:ring-[var(--focus)]"
            aria-label="Minimize menu"
          >
            <ChevronLeftIcon className="h-4 w-4" />
          </button>
        </div>
        <div className="module-tab mx-0">Menu</div>
        <nav aria-label="Primary" className="flex flex-1 flex-col">
          {NAV.map((item) => {
            const active = navActive(pathname, item.href);
            const Icon = item.Icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`border-b border-[var(--line)] px-3 py-2.5 transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus)] ${
                  active
                    ? "bg-[var(--signal-soft)] text-[var(--signal)]"
                    : "text-[var(--ink-muted)] hover:bg-[var(--module-fill)] hover:text-[var(--foreground)]"
                }`}
              >
                <span className="flex items-center gap-2">
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="block text-xs font-bold uppercase tracking-wide">{item.label}</span>
                </span>
                <span className="mt-0.5 block pl-6 text-[11px] text-[var(--ink-muted)]">{item.hint}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto border-t border-[var(--line)]">
          <Link
            href="/account"
            className={`flex min-h-11 items-center gap-2 px-3 text-xs font-bold uppercase tracking-wide transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus)] ${
              pathname.startsWith("/account")
                ? "bg-[var(--signal-soft)] text-[var(--signal)]"
                : "text-[var(--ink-muted)] hover:bg-[var(--module-fill)]"
            }`}
          >
            <AccountNavIcon className="h-4 w-4 shrink-0" />
            <span>Account</span>
          </Link>
        </div>
      </aside>

      <div
        className={`flex min-w-0 flex-1 flex-col ${isChatPage ? "min-h-0 overflow-hidden pb-0" : "pb-16 lg:pb-0"}`}
      >
        <header
          className={`z-30 shrink-0 border-b border-[var(--line)] bg-[var(--surface)] ${isChatPage ? "" : "sticky top-0"}`}
        >
          <div className={`flex items-center justify-between gap-2 px-3 sm:px-4 ${isChatPage ? "h-11" : "h-12"}`}>
            <div className="flex min-w-0 items-center gap-2">
              {!isChatPage && isNavMinimized ? (
                <button
                  type="button"
                  onClick={() => setNavMinimized(false)}
                  className="hidden min-h-10 min-w-10 shrink-0 items-center justify-center border border-[var(--line)] text-sm text-[var(--ink-muted)] transition-colors hover:border-[var(--signal)] hover:text-[var(--foreground)] focus-visible:ring-2 focus-visible:ring-[var(--focus)] lg:inline-flex"
                  aria-label="Show menu"
                >
                  <MenuIcon className="h-4 w-4" />
                </button>
              ) : null}
              {isChatPage ? (
                <Link href="/" className="flex items-center gap-2 text-sm font-bold">
                  <span className="flex h-7 w-7 items-center justify-center bg-[var(--signal)] text-[10px] text-white">CL</span>
                  <span className="hidden truncate sm:inline">ChatLaw</span>
                </Link>
              ) : (
                <>
              <div className="min-w-0 lg:hidden">
                <Link href="/" className="flex items-center gap-2 text-sm font-bold">
                  <span className="flex h-7 w-7 items-center justify-center bg-[var(--signal)] text-[10px] text-white">
                    CL
                  </span>
                  <span className="truncate">ChatLaw</span>
                </Link>
              </div>
              <div className="hidden min-w-0 lg:block">
                <h1 className="truncate text-sm font-bold tracking-tight">{pageTitle}</h1>
                {subtitle ? <p className="truncate text-[11px] text-[var(--ink-muted)]">{subtitle}</p> : null}
              </div>
                </>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              {!isChatPage ? <LanguageSelector compact /> : null}
              <Link
                href="/account"
                aria-current={pathname.startsWith("/account") ? "page" : undefined}
                className={`inline-flex min-h-10 items-center border border-[var(--line)] bg-white px-2.5 text-xs font-bold uppercase tracking-wide lg:hidden ${pathname.startsWith("/account") ? "text-[var(--signal)]" : "text-[var(--ink-muted)]"}`}
              >
                Account
              </Link>
              {session.status === "authenticated" && user ? (
                <div className="flex items-center gap-1.5">
                  <Link
                    href="/account"
                    className="hidden max-w-36 truncate text-xs text-[var(--ink-muted)] hover:text-[var(--foreground)] sm:inline lg:inline"
                  >
                    {user.name || user.email}
                  </Link>
                  <button
                    type="button"
                    onClick={() => signOut({ callbackUrl: "/" })}
                    className="min-h-10 border border-[var(--line)] bg-white px-2.5 text-xs font-bold uppercase tracking-wide transition-colors hover:border-[var(--signal)] focus-visible:ring-2 focus-visible:ring-[var(--focus)]"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => signIn("google", { callbackUrl: signInTarget })}
                  className="min-h-10 bg-[var(--signal)] px-3 text-xs font-bold uppercase tracking-wide text-white"
                >
                  Sign in
                </button>
              )}
            </div>
          </div>
          {!isChatPage ? (
            <div className="border-t border-[var(--line)] px-3 py-1.5 lg:hidden">
              <p className="truncate text-xs font-bold uppercase tracking-wide">{pageTitle}</p>
              {subtitle ? <p className="truncate text-[11px] text-[var(--ink-muted)]">{subtitle}</p> : null}
            </div>
          ) : null}
        </header>

        <div className={`flex min-h-0 flex-1 flex-col ${isChatPage ? "overflow-hidden" : ""}`}>
          {children}
        </div>
      </div>

      <nav
        aria-label="Primary"
        className={`fixed inset-x-0 bottom-0 z-40 border-t border-[var(--line)] bg-[var(--surface)] lg:hidden ${isChatPage ? "" : ""}`}
      >
        <div className="grid grid-cols-4">
          {NAV.map((item) => {
            const active = navActive(pathname, item.href);
            const Icon = item.Icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-14 flex-col items-center justify-center gap-0.5 border-r border-[var(--line)] text-center text-[10px] font-bold uppercase tracking-wide last:border-r-0 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus)] ${active ? "bg-[var(--signal-soft)] text-[var(--signal)]" : "text-[var(--ink-muted)]"}`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
