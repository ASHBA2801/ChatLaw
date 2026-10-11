import Link from "next/link";
import { redirect } from "next/navigation";

import { auth, authConfigurationStatus, signIn } from "@/auth";
import BrandMark from "@/components/layout/BrandMark";
import { safeCallbackUrl } from "@/lib/auth/config";

export const dynamic = "force-dynamic";

export default async function SignInPage({ searchParams }: { searchParams: Promise<{ callbackUrl?: string; error?: string }> }) {
  const session = await auth();
  const params = await searchParams;
  const callbackUrl = safeCallbackUrl(params.callbackUrl);
  if (session?.user) redirect(callbackUrl);

  const hasAuthError = Boolean(params.error);

  return (
    <main className="min-h-dvh bg-[var(--background)]">
      <div className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-4 py-12 sm:px-6">
        <BrandMark />
        <div className="rise-in mt-8 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-[var(--shadow-raised)] sm:p-8">
          <h1 className="text-2xl font-semibold tracking-tight">Sign in to your workspace</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
            Document drafts and case workspaces are stored against your signed-in account. Research chat remains
            available without signing in.
          </p>
          {hasAuthError ? (
            <div role="alert" className="mt-6 rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] p-4 text-sm leading-6 text-[var(--warn)]">
              <p className="font-semibold">We couldn&apos;t complete Google sign-in.</p>
              <p className="mt-1">The sign-in session may have expired, or this local environment may need its OAuth settings checked. Start a fresh attempt below.</p>
              <Link href={`/signin?callbackUrl=${encodeURIComponent(callbackUrl)}`} className="mt-3 inline-flex min-h-11 items-center rounded-lg border border-[var(--warn)] px-4 font-semibold hover:bg-[var(--surface)]">Try again</Link>
            </div>
          ) : authConfigurationStatus.googleConfigured ? (
            <form
              className="mt-6"
              action={async () => {
                "use server";
                await signIn("google", { redirectTo: callbackUrl });
              }}
            >
              <button type="submit" className="btn-primary w-full !min-h-12">
                Continue with Google
              </button>
            </form>
          ) : (
            <p role="status" className="mt-6 rounded-xl border border-[var(--line)] bg-[var(--fill)] p-4 text-sm leading-6">
              Google sign-in is not ready on this server. {authConfigurationStatus.issues.join(" ")} Restart the app after updating `web/.env`.
            </p>
          )}
          <p className="mt-6 text-xs leading-5 text-[var(--ink-faint)]">
            Informational assistance only — not a substitute for a lawyer or court.
          </p>
        </div>
        <Link href="/" className="mt-6 self-center text-sm text-[var(--ink-muted)] hover:text-[var(--foreground)]">
          ← Back to home
        </Link>
      </div>
    </main>
  );
}
