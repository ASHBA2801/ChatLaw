import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col bg-[var(--background)]">
      <header className="shrink-0 border-b border-[var(--line)] bg-[var(--surface)]">
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
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

      <section className="grid min-h-0 flex-1 lg:grid-cols-2">
        <div className="flex flex-col justify-center border-b border-[var(--line)] bg-[var(--surface)] p-6 sm:p-10 lg:border-b-0 lg:border-r lg:p-12 xl:p-16">
          <h1 className="text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl xl:text-7xl">
            ChatLaw
            <span className="mt-2 block text-[var(--signal)]">Your legal assistant.</span>
          </h1>
          <p className="mt-5 max-w-prose text-sm leading-7 text-[var(--ink-muted)] sm:text-base lg:text-lg">
            Understand Indian law in 22+ languages. Describe your situation in English or an Indian language. ChatLaw asks
            focused follow-ups, then explains the law in plain language with sources you can check.
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
          <p className="mt-4 max-w-prose text-[11px] text-[var(--ink-muted)]">
            Informational assistance only — not a substitute for a lawyer or court.
          </p>
        </div>

        <div className="flex min-h-[min(420px,50vh)] flex-col lg:min-h-0">
          <div className="module-tab shrink-0">Structured answer · demo</div>
          <div className="flex flex-1 flex-col border-b border-[var(--line)] bg-[var(--surface)] p-4 sm:p-6 lg:p-8">
            <p className="text-xs font-bold text-[var(--ink-muted)]">You</p>
            <p className="mt-1 border border-[var(--line)] bg-[var(--module-fill)] px-3 py-2 text-sm sm:text-base">
              My landlord is refusing to return my deposit.
            </p>
            <p className="mt-4 text-xs font-bold text-[var(--ink-muted)]">ChatLaw</p>
            <p className="mt-1 max-w-prose text-sm leading-6 sm:text-base">
              Which state are you in, and has the tenancy ended? After that I can point to the sections that usually
              govern deposit return.
            </p>
            <div className="mt-4 flex-1 border border-[var(--line)]">
              <div className="module-tab">Citations</div>
              <ul className="divide-y divide-[var(--line)] text-xs sm:text-sm">
                <li className="flex items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3">
                  <span>Transfer of Property Act · related tenancy terms</span>
                  <span className="shrink-0 bg-[var(--signal-soft)] px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--signal)] sm:text-xs">
                    Act
                  </span>
                </li>
                <li className="flex items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3">
                  <span>State rent / tenancy rules (after location)</span>
                  <span className="shrink-0 bg-[var(--module-fill)] px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--ink-muted)] sm:text-xs">
                    Next
                  </span>
                </li>
              </ul>
            </div>
          </div>
          <div className="grid shrink-0 grid-cols-4 divide-x divide-[var(--line)] border-t border-[var(--line)] bg-[var(--surface)] text-center text-[10px] font-bold uppercase tracking-wide sm:text-xs">
            <span className="px-1 py-3 text-[var(--signal)] sm:py-4">Chat</span>
            <span className="px-1 py-3 text-[var(--ink-muted)] sm:py-4">Documents</span>
            <span className="px-1 py-3 text-[var(--ink-muted)] sm:py-4">Cases</span>
            <span className="px-1 py-3 text-[var(--ink-muted)] sm:py-4">Research</span>
          </div>
        </div>
      </section>
    </main>
  );
}
