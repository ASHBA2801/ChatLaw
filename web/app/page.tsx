import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-[var(--background)]">
      <header className="border-b border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link href="/" className="flex items-center gap-2 text-sm font-bold tracking-tight">
            <span className="flex h-7 w-7 items-center justify-center bg-[var(--signal)] text-[10px] text-white">CL</span>
            ChatLaw
          </Link>
          <nav className="flex flex-wrap items-center gap-1 text-xs font-bold uppercase tracking-wide">
            {[
              ["/chat", "Chat"],
              ["/documents", "Documents"],
              ["/cases", "Cases"],
              ["/research", "Research"],
              ["/signin", "Sign in"],
            ].map(([href, label]) => (
              <Link
                key={href}
                href={href}
                className="border border-transparent px-2.5 py-2 text-[var(--ink-muted)] hover:border-[var(--line)] hover:text-[var(--foreground)]"
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-0 border-x border-[var(--line)] lg:grid-cols-[1.05fr_0.95fr]">
        <div className="border-b border-[var(--line)] bg-[var(--surface)] p-6 sm:p-10 lg:border-b-0 lg:border-r">
          <div className="module-tab inline-block">Indian law · 22+ languages</div>
          <h1 className="mt-4 max-w-xl text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
            ChatLaw
            <span className="mt-2 block text-[var(--signal)]">Your legal assistant.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-7 text-[var(--ink-muted)] sm:text-base">
            Describe your situation in English or an Indian language. ChatLaw asks focused follow-ups, then explains the
            law in plain language with sources you can check.
          </p>
          <div className="mt-8 flex flex-wrap gap-2">
            <Link
              href="/chat"
              className="inline-flex min-h-11 items-center bg-[var(--signal)] px-5 text-sm font-bold uppercase tracking-wide text-white"
            >
              Start with Chat
            </Link>
            <Link
              href="/research"
              className="inline-flex min-h-11 items-center border border-[var(--line)] bg-white px-5 text-sm font-bold uppercase tracking-wide text-[var(--foreground)]"
            >
              Search sources
            </Link>
            <Link
              href="/documents"
              className="inline-flex min-h-11 items-center border border-[var(--line)] bg-white px-5 text-sm font-bold uppercase tracking-wide text-[var(--foreground)]"
            >
              Draft a document
            </Link>
          </div>
          <p className="mt-4 text-[11px] text-[var(--ink-muted)]">
            Informational assistance only — not a substitute for a lawyer or court.
          </p>
        </div>

        <div className="grid grid-rows-[auto_1fr_auto] bg-[var(--background)]">
          <div className="module-tab">Structured answer · demo</div>
          <div className="border-b border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5">
            <p className="text-xs font-bold text-[var(--ink-muted)]">You</p>
            <p className="mt-1 border border-[var(--line)] bg-[var(--module-fill)] px-3 py-2 text-sm">
              My landlord is refusing to return my deposit.
            </p>
            <p className="mt-4 text-xs font-bold text-[var(--ink-muted)]">ChatLaw</p>
            <p className="mt-1 text-sm leading-6">
              Which state are you in, and has the tenancy ended? After that I can point to the sections that usually
              govern deposit return.
            </p>
            <div className="mt-4 border border-[var(--line)]">
              <div className="module-tab">Citations</div>
              <ul className="divide-y divide-[var(--line)] text-xs">
                <li className="flex items-center justify-between gap-2 px-3 py-2">
                  <span>Transfer of Property Act · related tenancy terms</span>
                  <span className="bg-[var(--signal-soft)] px-1.5 py-0.5 font-bold text-[var(--signal)]">Act</span>
                </li>
                <li className="flex items-center justify-between gap-2 px-3 py-2">
                  <span>State rent / tenancy rules (after location)</span>
                  <span className="bg-[var(--module-fill)] px-1.5 py-0.5 font-bold text-[var(--ink-muted)]">Next</span>
                </li>
              </ul>
            </div>
          </div>
          <div className="grid grid-cols-4 divide-x divide-[var(--line)] border-t border-[var(--line)] bg-[var(--surface)] text-center text-[10px] font-bold uppercase tracking-wide">
            <span className="px-1 py-3 text-[var(--signal)]">Chat</span>
            <span className="px-1 py-3 text-[var(--ink-muted)]">Documents</span>
            <span className="px-1 py-3 text-[var(--ink-muted)]">Cases</span>
            <span className="px-1 py-3 text-[var(--ink-muted)]">Research</span>
          </div>
        </div>
      </section>
    </main>
  );
}
