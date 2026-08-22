"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";

import LanguageSelector from "@/components/layout/LanguageSelector";

const NAV = [
  { href: "/chat", label: "Chat", hint: "Legal assistant" },
  { href: "/documents", label: "Documents", hint: "Draft generator" },
  { href: "/cases", label: "Cases", hint: "Your matters" },
  { href: "/research", label: "Research", hint: "Find sources" },
] as const;

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
  const session = useSession();
  const user = session.data?.user;
  const signInTarget =
    pathname.startsWith("/documents") || pathname.startsWith("/cases") || pathname.startsWith("/account")
      ? pathname
      : "/account";

  const pageTitle =
    title ??
    NAV.find((item) => navActive(pathname, item.href))?.label ??
    (pathname.startsWith("/account") ? "Account" : "ChatLaw");

  return (
    <div className="min-h-screen bg-[var(--background)] lg:flex">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-[var(--line)] bg-[#fbfcf8] lg:flex">
        <div className="flex h-16 items-center gap-3 border-b border-[var(--line)] px-5">
          <Link href="/" className="flex items-center gap-3 font-semibold tracking-tight">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--forest)] text-xs text-[var(--lime)]">
              CL
            </span>
            <span>ChatLaw</span>
          </Link>
        </div>
        <nav aria-label="Primary" className="flex flex-1 flex-col gap-1 p-3">
          {NAV.map((item) => {
            const active = navActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-xl px-3 py-3 transition-colors ${active ? "bg-white text-[var(--forest)] shadow-sm ring-1 ring-[var(--line)]" : "text-[var(--ink-muted)] hover:bg-white/70 hover:text-[var(--foreground)]"}`}
              >
                <span className="block text-sm font-semibold">{item.label}</span>
                <span className="mt-0.5 block text-xs text-[var(--ink-muted)]">{item.hint}</span>
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-[var(--line)] p-3">
          <Link
            href="/account"
            className={`flex min-h-11 items-center rounded-xl px-3 text-sm font-medium ${pathname.startsWith("/account") ? "bg-white text-[var(--forest)] ring-1 ring-[var(--line)]" : "text-[var(--ink-muted)] hover:bg-white/70"}`}
          >
            Account
          </Link>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col pb-20 lg:pb-0">
        <header className="sticky top-0 z-30 border-b border-[var(--line)] bg-[var(--background)]/95 backdrop-blur-sm">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
            <div className="min-w-0 lg:hidden">
              <Link href="/" className="flex items-center gap-2 font-semibold">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--forest)] text-[10px] text-[var(--lime)]">
                  CL
                </span>
                <span className="truncate">ChatLaw</span>
              </Link>
            </div>
            <div className="hidden min-w-0 lg:block">
              <h1 className="truncate text-base font-semibold tracking-tight">{pageTitle}</h1>
              {subtitle ? <p className="truncate text-xs text-[var(--ink-muted)]">{subtitle}</p> : null}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <LanguageSelector compact />
              {session.status === "authenticated" && user ? (
                <div className="flex items-center gap-2">
                  <Link
                    href="/account"
                    className="hidden max-w-36 truncate text-sm text-[var(--ink-muted)] hover:text-[var(--foreground)] sm:inline"
                  >
                    {user.name || user.email}
                  </Link>
                  <button
                    type="button"
                    onClick={() => signOut({ callbackUrl: "/" })}
                    className="min-h-11 rounded-full border border-[var(--line)] bg-white px-3 text-sm font-medium hover:border-[var(--forest)]"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => signIn("google", { callbackUrl: signInTarget })}
                  className="min-h-11 rounded-full bg-[var(--forest)] px-4 text-sm font-semibold text-white"
                >
                  Sign in
                </button>
              )}
            </div>
          </div>
          <div className="border-t border-[var(--line)] px-4 py-2 lg:hidden">
            <p className="truncate text-sm font-semibold">{pageTitle}</p>
            {subtitle ? <p className="truncate text-xs text-[var(--ink-muted)]">{subtitle}</p> : null}
          </div>
        </header>

        <div className="min-h-0 flex-1">{children}</div>
      </div>

      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--line)] bg-[var(--background)]/95 backdrop-blur-sm lg:hidden"
      >
        <div className="grid grid-cols-4 gap-1 px-2 py-1.5">
          {NAV.map((item) => {
            const active = navActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-12 flex-col items-center justify-center rounded-xl text-center text-xs font-semibold ${active ? "bg-white text-[var(--forest)]" : "text-[var(--ink-muted)]"}`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
