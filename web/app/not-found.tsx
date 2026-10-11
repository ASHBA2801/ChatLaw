import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center px-4 py-16 sm:px-6">
      <p className="text-sm font-semibold text-[var(--accent)]">404</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">
        That link may be outdated or mistyped. Try one of the main workspaces instead.
      </p>
      <div className="mt-6 flex flex-wrap gap-2">
        <Link href="/chat" className="btn-primary">
          Open Chat
        </Link>
        <Link href="/research" className="btn-secondary">
          Research
        </Link>
        <Link href="/cases" className="btn-secondary">
          My cases
        </Link>
      </div>
    </main>
  );
}
