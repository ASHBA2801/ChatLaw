"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";

import LanguageSelector from "@/components/layout/LanguageSelector";

/** Lightweight header for pages outside the product AppShell (rarely used). */
const links = [
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/cases", label: "Cases" },
  { href: "/research", label: "Research" },
];

export default function AppHeader({ subtitle }: { subtitle?: string }) {
  const pathname = usePathname();
  const session = useSession();
  const user = session.data?.user;
  const signInTarget =
    pathname.startsWith("/documents") || pathname.startsWith("/cases") ? pathname : "/documents";

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--line)] bg-[var(--background)]/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-6">
          <Link href="/" className="flex shrink-0 items-center gap-3 font-semibold tracking-tight">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--forest)] text-xs text-[var(--lime)]">
              CL
            </span>
            <span>ChatLaw</span>
          </Link>
          <nav aria-label="Primary" className="hidden items-center gap-1 sm:flex">
            {links.map((link) => {
              const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded-full px-3 py-2 text-sm font-medium ${active ? "bg-white text-[var(--forest)]" : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"}`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex min-w-0 items-center gap-3">
          <LanguageSelector compact />
          {subtitle ? (
            <span className="hidden rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs font-medium text-[var(--ink-muted)] md:inline">
              {subtitle}
            </span>
          ) : null}
          {session.status === "authenticated" && user ? (
            <button
              type="button"
              onClick={() => signOut({ callbackUrl: "/" })}
              className="min-h-11 rounded-full border border-[var(--line)] bg-white px-3 text-sm font-medium"
            >
              Sign out
            </button>
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
    </header>
  );
}
