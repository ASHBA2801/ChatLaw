import Link from "next/link";
import { redirect } from "next/navigation";

import { auth, authConfigurationStatus, signIn } from "@/auth";
import { safeCallbackUrl } from "@/lib/auth/config";

export const dynamic = "force-dynamic";

export default async function SignInPage({ searchParams }: { searchParams: Promise<{ callbackUrl?: string; error?: string }> }) {
  const session = await auth();
  const params = await searchParams;
  const callbackUrl = safeCallbackUrl(params.callbackUrl);
  if (session?.user) redirect(callbackUrl);

  const hasAuthError = Boolean(params.error);

  return (
    <main className="min-h-screen bg-[var(--background)]">
      <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-16">
        <Link href="/" className="flex items-center gap-3 font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--forest)] text-xs text-[var(--lime)]">CL</span>
          ChatLaw
        </Link>
        <p className="mt-10 text-xs font-bold uppercase tracking-[0.18em] text-[var(--forest)]">Secure legal workspace</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">Sign in to your workspace</h1>
        <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
          Document drafts are stored against your signed-in account. Research chat remains available without signing in.
        </p>
        {hasAuthError ? (
          <div role="alert" className="mt-8 rounded-2xl border border-[#e8c9a5] bg-[#fff8ed] p-4 text-sm leading-6 text-[#704616]">
            <p className="font-semibold">We couldn&apos;t complete Google sign-in.</p>
            <p className="mt-1">The sign-in session may have expired, or this local environment may need its OAuth settings checked. Start a fresh attempt below.</p>
            <Link href={`/signin?callbackUrl=${encodeURIComponent(callbackUrl)}`} className="mt-3 inline-flex min-h-11 items-center rounded-full border border-[#c99b5e] px-4 font-semibold hover:bg-[#fff0d7]">Try again</Link>
          </div>
        ) : authConfigurationStatus.googleConfigured ? (
          <form
            className="mt-8"
            action={async () => {
              "use server";
              await signIn("google", { redirectTo: callbackUrl });
            }}
          >
              <button type="submit" className="min-h-12 w-full rounded-full bg-[var(--forest)] text-sm font-semibold text-white transition hover:bg-[#0f3929] focus-visible:ring-2 focus-visible:ring-[var(--warm)]">
              Continue with Google
            </button>
          </form>
        ) : (
          <p role="status" className="mt-8 rounded-xl border border-[var(--line)] bg-white p-4 text-sm leading-6">
            Google sign-in is not ready on this server. {authConfigurationStatus.issues.join(" ")} Restart the app after updating `web/.env`.
          </p>
        )}
      </div>
    </main>
  );
}
