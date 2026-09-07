import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-lg flex-col justify-center px-4 py-16 sm:px-6">
      <div className="border border-[var(--line)] bg-[var(--surface)]">
        <div className="module-tab">ChatLaw</div>
        <div className="p-5">
          <h1 className="text-2xl font-bold tracking-tight">Page not found</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
            That link may be outdated or mistyped. Try one of the main workspaces below.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <Link
              href="/chat"
              className="inline-flex min-h-11 items-center bg-[var(--signal)] px-4 text-xs font-bold uppercase tracking-wide text-white"
            >
              Open Chat
            </Link>
            <Link
              href="/research"
              className="inline-flex min-h-11 items-center border border-[var(--line)] bg-white px-4 text-xs font-bold uppercase tracking-wide text-[var(--foreground)]"
            >
              Research
            </Link>
            <Link
              href="/cases"
              className="inline-flex min-h-11 items-center border border-[var(--line)] bg-white px-4 text-xs font-bold uppercase tracking-wide text-[var(--foreground)]"
            >
              My cases
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
