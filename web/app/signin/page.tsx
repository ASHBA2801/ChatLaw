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
      <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-16 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-sm font-bold">
          <span className="flex h-7 w-7 items-center justify-center bg-[var(--signal)] text-[10px] text-white">CL</span>
          ChatLaw
        </Link>
        <div className="mt-8 border border-[var(--line)] bg-[var(--surface)]">
          <div className="module-tab">Secure legal workspace</div>
          <div className="p-5">
            <h1 className="text-2xl font-bold tracking-tight">Sign in to your workspace</h1>
            <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
              Document drafts are stored against your signed-in account. Research chat remains available without signing in.
            </p>
            {hasAuthError ? (
              <div role="alert" className="mt-6 border border-[var(--warn-line)] bg-[var(--warn-bg)] p-4 text-sm leading-6 text-[var(--warn)]">
                <p className="font-semibold">We couldn&apos;t complete Google sign-in.</p>
                <p className="mt-1">The sign-in session may have expired, or this local environment may need its OAuth settings checked. Start a fresh attempt below.</p>
                <Link href={`/signin?callbackUrl=${encodeURIComponent(callbackUrl)}`} className="mt-3 inline-flex min-h-11 items-center border border-[var(--warn)] px-4 font-semibold hover:bg-[var(--signal-soft)]">Try again</Link>
              </div>
            ) : authConfigurationStatus.googleConfigured ? (
              <form
                className="mt-6"
                action={async () => {
                  "use server";
                  await signIn("google", { redirectTo: callbackUrl });
                }}
              >
                <button type="submit" className="min-h-12 w-full bg-[var(--signal)] text-sm font-bold uppercase tracking-wide text-white transition hover:bg-[#a01010] focus-visible:ring-2 focus-visible:ring-[var(--focus)]">
                  Continue with Google
                </button>
              </form>
            ) : (
              <p role="status" className="mt-6 border border-[var(--line)] bg-[var(--module-fill)] p-4 text-sm leading-6">
                Google sign-in is not ready on this server. {authConfigurationStatus.issues.join(" ")} Restart the app after updating `web/.env`.
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
