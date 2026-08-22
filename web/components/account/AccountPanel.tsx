"use client";

import Link from "next/link";
import { signIn, signOut, useSession } from "next-auth/react";

import LanguageSelector from "@/components/layout/LanguageSelector";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import { formatLanguageLabel } from "@/lib/i18n/languages";

export default function AccountPanel() {
  const session = useSession();
  const { languageOption } = useLanguage();
  const user = session.data?.user;

  if (session.status === "loading") {
    return <div className="h-48 animate-pulse rounded-2xl border border-[var(--line)] bg-white" aria-busy="true" />;
  }

  if (session.status !== "authenticated" || !user) {
    return (
      <div className="rounded-2xl border border-[var(--line)] bg-white px-6 py-10">
        <h1 className="text-2xl font-semibold tracking-tight">Account</h1>
        <p className="mt-3 max-w-lg text-sm leading-6 text-[var(--ink-muted)]">
          Sign in to save document drafts, case workspaces, and your preferred language across devices. Chat and Research
          remain available without an account.
        </p>
        <button
          type="button"
          onClick={() => signIn("google", { callbackUrl: "/account" })}
          className="mt-6 min-h-11 rounded-full bg-[var(--forest)] px-5 text-sm font-semibold text-white"
        >
          Sign in with Google
        </button>
        <div className="mt-8 border-t border-[var(--line)] pt-6">
          <h2 className="text-sm font-semibold">Language on this device</h2>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">Saved locally until you sign in.</p>
          <div className="mt-3">
            <LanguageSelector />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-[var(--line)] bg-white px-6 py-8">
        <h1 className="text-2xl font-semibold tracking-tight">Account</h1>
        <dl className="mt-6 space-y-4 text-sm">
          <div>
            <dt className="text-[var(--ink-muted)]">Name</dt>
            <dd className="mt-1 font-medium">{user.name || "—"}</dd>
          </div>
          <div>
            <dt className="text-[var(--ink-muted)]">Email</dt>
            <dd className="mt-1 font-medium">{user.email || "—"}</dd>
          </div>
        </dl>
        <button
          type="button"
          onClick={() => signOut({ callbackUrl: "/" })}
          className="mt-6 min-h-11 rounded-full border border-[var(--line)] px-4 text-sm font-medium hover:border-[var(--forest)]"
        >
          Sign out
        </button>
      </div>

      <div className="rounded-2xl border border-[var(--line)] bg-white px-6 py-8">
        <h2 className="text-lg font-semibold">Language preference</h2>
        <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">
          Chat clarifications and answers use this language. Citations keep official Act and section names.
        </p>
        <p className="mt-3 text-sm">
          Current: <span className="font-semibold">{formatLanguageLabel(languageOption)}</span>
        </p>
        <div className="mt-4">
          <LanguageSelector />
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--line)] bg-white px-6 py-8">
        <h2 className="text-lg font-semibold">Your workspaces</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/cases" className="min-h-11 rounded-full border border-[var(--line)] px-4 text-sm font-medium hover:border-[var(--forest)]">
            My cases
          </Link>
          <Link href="/documents" className="min-h-11 rounded-full border border-[var(--line)] px-4 text-sm font-medium hover:border-[var(--forest)]">
            Documents
          </Link>
          <Link href="/chat" className="min-h-11 rounded-full bg-[var(--forest)] px-4 text-sm font-semibold text-white">
            Open Chat
          </Link>
        </div>
      </div>
    </div>
  );
}
